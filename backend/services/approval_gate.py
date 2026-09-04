"""
Approval Gate
=============
Application-level write guard that prevents any MCP write actions
(Gmail draft creation, document append) until a human explicitly approves.

This is NOT an LLM guardrail — it is enforced at the application layer
and cannot be bypassed by model output.
"""

import logging
from datetime import datetime, timezone
from threading import Lock
from typing import Dict, Optional

from models.approval import ApprovalStatus

logger = logging.getLogger(__name__)


class ApprovalGate:
    """
    Singleton approval gate.

    Workflow:
      1. Gate starts in PENDING state for each batch.
      2. Human clicks "Approve" → `approve(batch_id)` is called.
      3. Every write action calls `guard(batch_id)` before executing.
      4. If status != APPROVED, guard raises PermissionError.
    """

    _instance: Optional["ApprovalGate"] = None
    _lock: Lock = Lock()

    def __new__(cls) -> "ApprovalGate":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._status: dict[str, ApprovalStatus] = {}
                cls._instance._approved_at: dict[str, str] = {}
                cls._instance._rejected_at: dict[str, str] = {}
                logger.info("ApprovalGate singleton initialized")
        return cls._instance

    # ------------------------------------------------------------------
    # State management
    # ------------------------------------------------------------------

    def initialize(self, batch_id: str) -> None:
        """Set a batch to PENDING state (called when analysis starts)."""
        self._status[batch_id] = ApprovalStatus.PENDING
        logger.info(f"[{batch_id}] Approval gate initialized → PENDING")

    def approve(self, batch_id: str) -> None:
        """Transition batch to APPROVED — enables write actions."""
        self._status[batch_id] = ApprovalStatus.APPROVED
        self._approved_at[batch_id] = datetime.now(timezone.utc).isoformat()
        logger.info(f"[{batch_id}] Approval gate → APPROVED at {self._approved_at[batch_id]}")

    def reject(self, batch_id: str) -> None:
        """Transition batch to REJECTED — blocks all write actions."""
        self._status[batch_id] = ApprovalStatus.REJECTED
        self._rejected_at[batch_id] = datetime.now(timezone.utc).isoformat()
        logger.info(f"[{batch_id}] Approval gate → REJECTED")

    def reset(self, batch_id: str) -> None:
        """Reset to PENDING (e.g., after edits that require re-approval)."""
        self._status[batch_id] = ApprovalStatus.PENDING
        self._approved_at.pop(batch_id, None)
        logger.info(f"[{batch_id}] Approval gate reset → PENDING")

    # ------------------------------------------------------------------
    # Inspection
    # ------------------------------------------------------------------

    def get_status(self, batch_id: str) -> ApprovalStatus:
        """Return the current approval status for a batch."""
        return self._status.get(batch_id, ApprovalStatus.PENDING)

    def is_write_allowed(self, batch_id: str) -> bool:
        """Return True only if the batch is in APPROVED state."""
        return self.get_status(batch_id) == ApprovalStatus.APPROVED

    def get_approved_at(self, batch_id: str) -> Optional[str]:
        """Return the ISO timestamp when approval was granted, or None."""
        return self._approved_at.get(batch_id)

    # ------------------------------------------------------------------
    # Guard (call before every write action)
    # ------------------------------------------------------------------

    def guard(self, batch_id: str) -> None:
        """
        Raise PermissionError if write is not yet approved.

        Call this immediately before executing any MCP write action.
        If it does not raise, the write is permitted.
        """
        status = self.get_status(batch_id)
        if status != ApprovalStatus.APPROVED:
            msg = (
                f"Write action blocked for batch '{batch_id}': "
                f"approval status is {status.value!r}. "
                "Human approval required before any write action."
            )
            logger.warning(msg)
            raise PermissionError(msg)
        logger.info(f"[{batch_id}] Guard passed — write action authorized")


# Module-level singleton instance
approval_gate = ApprovalGate()
