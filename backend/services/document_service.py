"""
Document Service
================
Backend service that uses the Google Docs API to append new entries
to an internal knowledge repository Google Doc.

Design contract:
  - NEVER overwrites existing content. Strictly additive.
  - Each entry is timestamped and separated from previous entries.
  - If GOOGLE_DOC_ID is not configured, falls back to local JSON file.
"""

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from core.config import settings

logger = logging.getLogger(__name__)

# Google Docs scopes
DOCS_SCOPES = [
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive.file",
]

_BACKEND_ROOT = Path(__file__).resolve().parent.parent
_TOKEN_PATH = _BACKEND_ROOT / "credentials" / "docs_token.json"
_SECRET_PATH = (
    Path(os.environ.get("GOOGLE_CLIENT_SECRET_PATH", ""))
    if os.environ.get("GOOGLE_CLIENT_SECRET_PATH")
    else _BACKEND_ROOT.parent / "client_secret_10616404203-bt3063lelbakaub5jlcrpbnaebuocuhv.apps.googleusercontent.com.json"
)

# Local fallback file
_LOCAL_REPO_PATH = _BACKEND_ROOT / "data" / "knowledge_repository.json"
_SEPARATOR = "─" * 60


def _get_docs_credentials() -> Optional[Credentials]:
    """Load or refresh Google Docs OAuth credentials."""
    # Try shared token path first (MCP server may have already authenticated)
    mcp_token = _BACKEND_ROOT.parent / "mcp_server" / "credentials" / "token.json"

    for token_path in [_TOKEN_PATH, mcp_token]:
        if token_path.exists():
            try:
                creds = Credentials.from_authorized_user_file(str(token_path), DOCS_SCOPES)
                if creds and creds.valid:
                    return creds
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                    _TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
                    with open(_TOKEN_PATH, "w") as f:
                        f.write(creds.to_json())
                    logger.info("Docs credentials refreshed")
                    return creds
            except Exception as e:
                logger.warning(f"Could not load Docs token from {token_path}: {e}")

    return None


class DocumentService:
    """
    Service for appending structured entries to an internal Google Doc
    (or local JSON file as fallback).
    """

    def __init__(self, document_id: Optional[str] = None):
        self.document_id = document_id or settings.google_doc_id or os.environ.get("GOOGLE_DOC_ID")
        self._creds = _get_docs_credentials()
        self._docs_service = None

        if self._creds and self.document_id:
            try:
                self._docs_service = build("docs", "v1", credentials=self._creds)
                logger.info(f"DocumentService: ready with Google Doc {self.document_id}")
            except Exception as e:
                logger.error(f"DocumentService init failed: {e}")

    @property
    def is_google_doc_available(self) -> bool:
        return self._docs_service is not None and bool(self.document_id)

    def _get_doc_end_index(self) -> int:
        """Return the last character index in the document body."""
        doc = self._docs_service.documents().get(documentId=self.document_id).execute()
        content = doc.get("body", {}).get("content", [])
        if not content:
            return 1
        return max(1, content[-1].get("endIndex", 1) - 1)

    def _append_to_google_doc(self, text: str) -> dict:
        """Append raw text to the Google Doc via batchUpdate."""
        try:
            end_index = self._get_doc_end_index()
            requests = [
                {
                    "insertText": {
                        "location": {"index": end_index},
                        "text": text,
                    }
                }
            ]
            self._docs_service.documents().batchUpdate(
                documentId=self.document_id,
                body={"requests": requests},
            ).execute()
            doc_url = f"https://docs.google.com/document/d/{self.document_id}/edit"
            return {
                "status": "success",
                "backend": "google_docs",
                "document_id": self.document_id,
                "document_url": doc_url,
                "chars_appended": len(text),
                "message": "Entry appended to Google Doc successfully.",
            }
        except HttpError as e:
            logger.error(f"Google Docs append failed: {e}")
            raise RuntimeError(f"Google Docs API error: {e.reason}") from e

    def _append_to_local_file(self, entry: dict) -> dict:
        """Fallback: append entry to local JSON file."""
        _LOCAL_REPO_PATH.parent.mkdir(parents=True, exist_ok=True)

        # Load existing data
        existing: list[dict] = []
        if _LOCAL_REPO_PATH.exists():
            try:
                with open(_LOCAL_REPO_PATH, "r") as f:
                    existing = json.load(f)
                    if not isinstance(existing, list):
                        existing = [existing]
            except (json.JSONDecodeError, Exception) as e:
                logger.warning(f"Could not parse existing repo file: {e}")
                existing = []

        existing.append(entry)

        with open(_LOCAL_REPO_PATH, "w") as f:
            json.dump(existing, f, indent=2, ensure_ascii=False)

        return {
            "status": "success",
            "backend": "local_json",
            "file_path": str(_LOCAL_REPO_PATH),
            "total_entries": len(existing),
            "message": f"Entry appended to local file: {_LOCAL_REPO_PATH}",
        }

    def append_entry(self, entry: dict) -> dict:
        """
        Append a structured entry to the internal knowledge repository.

        Tries Google Doc first, falls back to local JSON file.
        Never overwrites previous entries.

        Args:
            entry: Dict containing the structured data to append.

        Returns:
            Dict with status, backend, and confirmation details.
        """
        timestamp = datetime.now(timezone.utc).isoformat()

        if self.is_google_doc_available:
            try:
                # Format entry as readable text for Google Doc
                text = self._format_entry_as_text(entry)
                result = self._append_to_google_doc(text)
                result["timestamp"] = timestamp
                return result
            except Exception as e:
                logger.error(f"Google Doc append failed, falling back to local: {e}")

        # Fallback to local file
        result = self._append_to_local_file(entry)
        result["timestamp"] = timestamp
        return result

    @staticmethod
    def _format_entry_as_text(entry: dict) -> str:
        """Format a structured entry as human-readable text for Google Doc."""
        lines = [
            f"\n{_SEPARATOR}\n",
            f"Date: {entry.get('date', 'N/A')}\n",
        ]

        if "top_themes" in entry:
            lines.append(f"\nTop Themes:\n")
            for t in entry.get("top_themes", []):
                lines.append(f"  • {t}\n")
        if "weekly_pulse" in entry:
            lines.append(f"\nWeekly Pulse:\n{entry['weekly_pulse']}\n")
        if "identified_fee_issue" in entry:
            lines.append(f"\nIdentified Fee Issue: {entry.get('identified_fee_issue', 'N/A')}\n")
        if "explanation_bullets" in entry:
            lines.append(f"\nExplanation Bullets:\n")
            for b in entry.get("explanation_bullets", []):
                lines.append(f"  • {b}\n")
        if "source_links" in entry:
            lines.append(f"\nSource Links:\n")
            for url in entry.get("source_links", []):
                lines.append(f"  - {url}\n")

        return "".join(lines)


# Module-level singleton
_document_service: Optional["DocumentService"] = None


def get_document_service() -> DocumentService:
    """Return the shared DocumentService instance (lazy init)."""
    global _document_service
    if _document_service is None:
        _document_service = DocumentService()
    return _document_service
