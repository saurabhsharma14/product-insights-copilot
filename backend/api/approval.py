"""
Approval API
============
Endpoints:
  GET  /api/approval/{batch_id}/preview  — Full approval preview (document + email draft)
  POST /api/approval/{batch_id}/approve  — Execute approval → both MCP write actions
  POST /api/approval/{batch_id}/reject   — Reject outputs (blocks write actions)
  GET  /api/approval/{batch_id}/status   — Return per-action MCPActionResult

Approval flow:
  1. Human reviews preview
  2. Human clicks "Approve" → POST /approve
  3. approval_gate.approve(batch_id) is called
  4. approval_gate.guard(batch_id) is verified before every write
  5. Document append → Gmail draft creation
  6. Results returned with per-action status
"""

import json
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.database import get_db
from models.approval import ApprovalStatus, MCPActionResult
from services.approval_gate import approval_gate
from services.gmail_service import get_gmail_service
from services.document_service import get_document_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/approval", tags=["approval"])


# ---------------------------------------------------------------------------
# Request/Response models
# ---------------------------------------------------------------------------

class ApproveRequest(BaseModel):
    recipient_email: str = ""          # Optional: override default recipient
    google_doc_id: str = ""            # Optional: override default Google Doc ID


class ApprovalPreviewResponse(BaseModel):
    batch_id: str
    approval_status: str
    review_count: int
    review_period: str
    top_themes: list[str]
    fee_issue: Optional[str]
    document_entry_preview: dict
    email_subject: str
    email_body: str
    gmail_authenticated: bool
    google_doc_configured: bool


class ApprovalResult(BaseModel):
    batch_id: str
    approval_status: str
    approved_at: Optional[str]
    document_action: Optional[MCPActionResult]
    gmail_action: Optional[MCPActionResult]


# ---------------------------------------------------------------------------
# Helper: build email content from analysis results
# ---------------------------------------------------------------------------

def _build_email_content(batch_data: dict) -> tuple[str, str]:
    """Build email subject and body from persisted analysis data."""
    fee_issue = batch_data.get("fee_issue_data")
    pulse_data = batch_data.get("pulse_data")
    explainer_data = batch_data.get("explainer_data")

    # Subject
    fee_name = fee_issue.get("fee_name", "Fee Issue") if fee_issue else "Product Feedback"
    subject = f"Weekly Product Pulse + Customer Clarification — {fee_name}"

    # Body sections
    lines = []

    if pulse_data and pulse_data.get("content"):
        lines.append(pulse_data["content"])
    else:
        lines.append("[Product Pulse not generated]")

    if explainer_data:
        lines.append("")
        lines.append(explainer_data.get("customer_confusion_summary", ""))
        for bullet in explainer_data.get("bullets", []):
            lines.append(f"• {bullet}")

        sources = explainer_data.get("sources", [])
        if sources:
            lines.append("")
            lines.append("Official Sources:")
            for s in sources:
                url = s.get("url", "") if isinstance(s, dict) else str(s)
                title = s.get("title", url) if isinstance(s, dict) else url
                lines.append(f"  - {title}: {url}")

    lines.append("")
    lines.append("(No auto-send)")

    return subject, "\n".join(lines)


# ---------------------------------------------------------------------------
# Helper: build document entry
# ---------------------------------------------------------------------------

def _build_document_entry(batch_id: str, batch_data: dict) -> dict:
    """Build the structured entry to append to the internal document."""
    themes = batch_data.get("themes_data", [])
    top_theme_names = [
        t.get("theme_name", "Unknown") for t in themes[:3]
    ] if themes else []

    fee_issue = batch_data.get("fee_issue_data")
    pulse_data = batch_data.get("pulse_data")
    explainer_data = batch_data.get("explainer_data")

    # Extract source links
    sources = []
    if explainer_data and "sources" in explainer_data:
        for s in explainer_data["sources"]:
            url = s.get("url", "") if isinstance(s, dict) else str(s)
            if url:
                sources.append(url)

    return {
        "date": datetime.now(timezone.utc).isoformat(),
        "top_themes": top_theme_names,
        "weekly_pulse": pulse_data.get("content", "") if pulse_data else "",
        "identified_fee_issue": fee_issue.get("fee_name") if fee_issue else None,
        "explanation_bullets": explainer_data.get("bullets", []) if explainer_data else [],
        "source_links": sources
    }


# ---------------------------------------------------------------------------
# Helper: load full batch data from DB
# ---------------------------------------------------------------------------

async def _load_batch_data(batch_id: str) -> dict:
    """Load all analysis data for a batch from SQLite."""
    async with get_db() as db:
        row = await db.fetchrow(
            """
            SELECT review_count, review_period_start, review_period_end,
                   avg_rating, themes, fee_issues, product_pulse, fee_explainer,
                   approval_status, approved_at
            FROM analysis_runs
            WHERE batch_id = $1
            """,
            batch_id,
        )

    if not row:
        raise HTTPException(status_code=404, detail=f"Batch '{batch_id}' not found")

    return {
        "review_count": row["review_count"] or 0,
        "review_period_start": row["review_period_start"] or "",
        "review_period_end": row["review_period_end"] or "",
        "avg_rating": row["avg_rating"] or 0,
        "themes_data": json.loads(row["themes"]) if row["themes"] else [],
        "fee_issue_data": json.loads(row["fee_issues"]) if row["fee_issues"] else None,
        "pulse_data": json.loads(row["product_pulse"]) if row["product_pulse"] else None,
        "explainer_data": json.loads(row["fee_explainer"]) if row["fee_explainer"] else None,
        "approval_status": row["approval_status"] or "pending",
        "approved_at": row["approved_at"],
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/{batch_id}/preview", response_model=ApprovalPreviewResponse)
async def get_approval_preview(batch_id: str):
    """
    Return a full preview of what will be written if approved:
    - Structured document entry (for Google Doc / local JSON)
    - Email subject + body (for Gmail draft)
    - Auth status (is Gmail connected? is Google Doc configured?)
    """
    batch_data = await _load_batch_data(batch_id)

    # Initialize gate if needed
    current_status = approval_gate.get_status(batch_id)
    if current_status == ApprovalStatus.PENDING and batch_data["approval_status"] == "approved":
        approval_gate.approve(batch_id)

    # Build previews
    document_entry = _build_document_entry(batch_id, batch_data)
    subject, body = _build_email_content(batch_data)

    # Auth checks
    gmail_svc = get_gmail_service()
    doc_svc = get_document_service()

    themes = batch_data.get("themes_data", [])
    top_themes = [t.get("theme_name", "") for t in themes[:3]] if themes else []
    fee_issue = batch_data.get("fee_issue_data")

    return ApprovalPreviewResponse(
        batch_id=batch_id,
        approval_status=approval_gate.get_status(batch_id).value,
        review_count=batch_data["review_count"],
        review_period=f"{batch_data['review_period_start']} to {batch_data['review_period_end']}",
        top_themes=top_themes,
        fee_issue=fee_issue.get("fee_name") if fee_issue else None,
        document_entry_preview=document_entry,
        email_subject=subject,
        email_body=body,
        gmail_authenticated=gmail_svc.is_authenticated,
        google_doc_configured=doc_svc.is_google_doc_available,
    )


@router.post("/{batch_id}/approve", response_model=ApprovalResult)
async def execute_approval(batch_id: str, req: ApproveRequest = ApproveRequest()):
    """
    Execute approval and trigger both MCP write actions:
      1. Append structured entry to internal document (Google Doc or local JSON)
      2. Create Gmail draft (never sends)

    The approval gate is checked immediately before each write action.
    Any failure in the gate raises HTTP 403.
    """
    batch_data = await _load_batch_data(batch_id)

    # --- Step 1: Grant approval ---
    approval_gate.approve(batch_id)
    approved_at = approval_gate.get_approved_at(batch_id)

    now = datetime.now(timezone.utc).isoformat()
    document_result: Optional[MCPActionResult] = None
    gmail_result: Optional[MCPActionResult] = None

    # --- Step 2: Document append ---
    try:
        approval_gate.guard(batch_id)  # Double-check gate before write
        doc_entry = _build_document_entry(batch_id, batch_data)
        doc_svc = get_document_service()

        # Override doc ID if provided
        if req.google_doc_id:
            doc_svc.document_id = req.google_doc_id

        append_result = doc_svc.append_entry(doc_entry)
        document_result = MCPActionResult(
            action_name="append_to_internal_document",
            status=append_result.get("status", "failed"),
            message=append_result.get("message", "Unknown result"),
            timestamp=append_result.get("timestamp", now),
        )
        logger.info(f"[{batch_id}] Document append: {document_result.status}")
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"[{batch_id}] Document append failed: {e}")
        document_result = MCPActionResult(
            action_name="append_to_internal_document",
            status="failed",
            message=str(e),
            timestamp=now,
        )

    # --- Step 3: Gmail draft ---
    try:
        approval_gate.guard(batch_id)  # Double-check gate before write
        subject, body = _build_email_content(batch_data)
        gmail_svc = get_gmail_service()

        to_email = req.recipient_email or "product-team@groww.in"
        draft_result = gmail_svc.create_draft(
            subject=subject,
            body=body,
            to=to_email,
        )
        gmail_result = MCPActionResult(
            action_name="create_gmail_draft",
            status=draft_result.get("status", "failed"),
            message=draft_result.get("message", "Unknown result"),
            timestamp=draft_result.get("timestamp", now),
        )
        logger.info(f"[{batch_id}] Gmail draft: {gmail_result.status}")
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"[{batch_id}] Gmail draft failed: {e}")
        gmail_result = MCPActionResult(
            action_name="create_gmail_draft",
            status="failed",
            message=str(e),
            timestamp=now,
        )

    # --- Step 4: Persist results to DB ---
    async with get_db() as db:
        await db.execute(
            """
            UPDATE analysis_runs
            SET approval_status = 'approved',
                approved_at = $1,
                mcp_document_status = $2,
                mcp_gmail_status = $3
            WHERE batch_id = $4
            """,
            approved_at,
            document_result.status if document_result else None,
            gmail_result.status if gmail_result else None,
            batch_id,
        )

    return ApprovalResult(
        batch_id=batch_id,
        approval_status=ApprovalStatus.APPROVED.value,
        approved_at=approved_at,
        document_action=document_result,
        gmail_action=gmail_result,
    )


@router.post("/{batch_id}/reject")
async def reject_approval(batch_id: str):
    """Reject the outputs — blocks all write actions for this batch."""
    # Verify batch exists
    await _load_batch_data(batch_id)
    approval_gate.reject(batch_id)

    async with get_db() as db:
        await db.execute(
            "UPDATE analysis_runs SET approval_status = 'rejected' WHERE batch_id = $1",
            batch_id,
        )

    return {
        "batch_id": batch_id,
        "approval_status": "rejected",
        "message": "Outputs rejected. No write actions will be executed.",
    }


@router.get("/{batch_id}/status", response_model=ApprovalResult)
async def get_approval_status(batch_id: str):
    """Return the current approval status and MCP action results for a batch."""
    async with get_db() as db:
        row = await db.fetchrow(
            """
            SELECT approval_status, approved_at,
                   mcp_document_status, mcp_gmail_status
            FROM analysis_runs
            WHERE batch_id = $1
            """,
            batch_id,
        )

    if not row:
        raise HTTPException(status_code=404, detail=f"Batch '{batch_id}' not found")

    now = datetime.now(timezone.utc).isoformat()

    doc_status = row["mcp_document_status"]
    gmail_status = row["mcp_gmail_status"]

    return ApprovalResult(
        batch_id=batch_id,
        approval_status=row["approval_status"] or "pending",
        approved_at=row["approved_at"],
        document_action=MCPActionResult(
            action_name="append_to_internal_document",
            status=doc_status or "not_executed",
            message="Document action not yet executed" if not doc_status else f"Status: {doc_status}",
            timestamp=row["approved_at"] or now,
        ) if doc_status else None,
        gmail_action=MCPActionResult(
            action_name="create_gmail_draft",
            status=gmail_status or "not_executed",
            message="Gmail action not yet executed" if not gmail_status else f"Status: {gmail_status}",
            timestamp=row["approved_at"] or now,
        ) if gmail_status else None,
    )
