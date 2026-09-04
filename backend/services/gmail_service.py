"""
Gmail Service
=============
Backend service that uses the Gmail API to create draft emails.
Used by the approval API after human approval is granted.

This service is separate from the MCP server's gmail_tools — it runs
inside the FastAPI backend using the same OAuth flow.
"""

import base64
import json
import logging
import os
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

# OAuth scopes required for Gmail
GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.readonly",
]

# Token/secret paths
_BACKEND_ROOT = Path(__file__).resolve().parent.parent
_TOKEN_PATH = _BACKEND_ROOT / "credentials" / "gmail_token.json"
_SECRET_PATH = (
    Path(os.environ.get("GOOGLE_CLIENT_SECRET_PATH", ""))
    if os.environ.get("GOOGLE_CLIENT_SECRET_PATH")
    else _BACKEND_ROOT.parent / "client_secret_10616404203-bt3063lelbakaub5jlcrpbnaebuocuhv.apps.googleusercontent.com.json"
)


def _get_gmail_credentials() -> Optional[Credentials]:
    """Load or refresh Gmail OAuth credentials. Returns None if not configured."""
    creds: Optional[Credentials] = None

    if _TOKEN_PATH.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(_TOKEN_PATH), GMAIL_SCOPES)
        except Exception as e:
            logger.warning(f"Could not load Gmail token: {e}")

    if creds and creds.valid:
        return creds

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            _TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(_TOKEN_PATH, "w") as f:
                f.write(creds.to_json())
            logger.info("Gmail credentials refreshed")
            return creds
        except Exception as e:
            logger.error(f"Gmail token refresh failed: {e}")

    return None  # Not authenticated — OAuth flow required


class GmailService:
    """
    Service for creating Gmail drafts and sending emails via the Gmail API.

    Design contract:
      - `create_draft()` NEVER sends the email. It only creates a draft.
      - `send_email()` sends immediately — call only with explicit intent.
    """

    def __init__(self):
        self._creds = _get_gmail_credentials()
        self._service = None
        if self._creds:
            try:
                self._service = build("gmail", "v1", credentials=self._creds)
                logger.info("GmailService: authenticated and ready")
            except Exception as e:
                logger.error(f"GmailService init failed: {e}")
                self._service = None

    @property
    def is_authenticated(self) -> bool:
        return self._service is not None

    def _build_message(
        self,
        to: str,
        subject: str,
        body: str,
        body_html: Optional[str] = None,
        cc: Optional[str] = None,
    ) -> dict:
        if body_html:
            msg = MIMEMultipart("alternative")
            msg.attach(MIMEText(body, "plain", "utf-8"))
            msg.attach(MIMEText(body_html, "html", "utf-8"))
        else:
            msg = MIMEText(body, "plain", "utf-8")

        msg["To"] = to
        msg["Subject"] = subject
        if cc:
            msg["Cc"] = cc

        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
        return {"raw": raw}

    def create_draft(
        self,
        subject: str,
        body: str,
        to: str,
        body_html: Optional[str] = None,
        cc: Optional[str] = None,
    ) -> dict:
        """
        Create a Gmail draft. Does NOT send the email.

        Returns a dict with:
          - status: "success" | "failed" | "no_auth"
          - draft_id: Gmail draft ID (on success)
          - message: Human-readable status message
          - timestamp: ISO UTC timestamp
        """
        timestamp = datetime.now(timezone.utc).isoformat()

        if not self.is_authenticated:
            return {
                "status": "no_auth",
                "draft_id": None,
                "message": (
                    "Gmail not authenticated. Please complete OAuth flow via "
                    "GET /api/auth/google/login to enable Gmail draft creation."
                ),
                "timestamp": timestamp,
            }

        try:
            message = self._build_message(to, subject, body, body_html, cc)
            draft_body = {"message": message}
            result = (
                self._service.users()
                .drafts()
                .create(userId="me", body=draft_body)
                .execute()
            )
            draft_id = result["id"]
            logger.info(f"Gmail draft created | id={draft_id} to={to}")
            return {
                "status": "success",
                "draft_id": draft_id,
                "message_id": result.get("message", {}).get("id"),
                "message": f"Gmail draft created successfully (id={draft_id}). No email sent.",
                "timestamp": timestamp,
                "to": to,
                "subject": subject,
            }
        except HttpError as e:
            logger.error(f"Gmail create_draft error: {e}")
            return {
                "status": "failed",
                "draft_id": None,
                "message": f"Gmail API error: {e.reason}",
                "timestamp": timestamp,
            }
        except Exception as e:
            logger.error(f"Gmail create_draft unexpected error: {e}")
            return {
                "status": "failed",
                "draft_id": None,
                "message": str(e),
                "timestamp": timestamp,
            }

    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        body_html: Optional[str] = None,
        cc: Optional[str] = None,
    ) -> dict:
        """
        Send an email via Gmail. Only call when explicitly intending to send.

        Returns a dict with status, message_id, and timestamp.
        """
        timestamp = datetime.now(timezone.utc).isoformat()

        if not self.is_authenticated:
            return {
                "status": "no_auth",
                "message_id": None,
                "message": "Gmail not authenticated.",
                "timestamp": timestamp,
            }

        try:
            message = self._build_message(to, subject, body, body_html, cc)
            result = (
                self._service.users()
                .messages()
                .send(userId="me", body=message)
                .execute()
            )
            logger.info(f"Email sent | id={result['id']} to={to}")
            return {
                "status": "success",
                "message_id": result["id"],
                "thread_id": result.get("threadId"),
                "message": f"Email sent to {to}",
                "timestamp": timestamp,
            }
        except HttpError as e:
            logger.error(f"Gmail send_email error: {e}")
            return {
                "status": "failed",
                "message_id": None,
                "message": f"Gmail API error: {e.reason}",
                "timestamp": timestamp,
            }


# Module-level singleton
_gmail_service: Optional["GmailService"] = None


def get_gmail_service() -> GmailService:
    """Return the shared GmailService instance (lazy init)."""
    global _gmail_service
    if _gmail_service is None:
        _gmail_service = GmailService()
    return _gmail_service
