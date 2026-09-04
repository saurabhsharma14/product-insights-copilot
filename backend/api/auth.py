"""
Google OAuth API
================
Endpoints:
  GET /api/auth/google/login    — Initiate OAuth flow (redirects to Google)
  GET /api/auth/google/callback — Handle OAuth callback, store credentials
  GET /api/auth/google/status   — Check authentication status
  POST /api/auth/google/revoke  — Revoke stored credentials

Uses the installed-app / desktop OAuth flow with a localhost redirect.
Stores tokens at backend/credentials/gmail_token.json
"""

import json
import logging
import os
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])

# Token / secret paths
_BACKEND_ROOT = Path(__file__).resolve().parent.parent
_CREDENTIALS_DIR = _BACKEND_ROOT / "credentials"
_TOKEN_PATH = _CREDENTIALS_DIR / "gmail_token.json"
_DOCS_TOKEN_PATH = _CREDENTIALS_DIR / "docs_token.json"

# Find client secret
_SECRET_PATH = (
    Path(os.environ.get("GOOGLE_CLIENT_SECRET_PATH", ""))
    if os.environ.get("GOOGLE_CLIENT_SECRET_PATH")
    else _BACKEND_ROOT.parent / "client_secret_10616404203-bt3063lelbakaub5jlcrpbnaebuocuhv.apps.googleusercontent.com.json"
)

_REDIRECT_URI = os.environ.get("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/auth/google/callback")

# Combined scopes for Gmail + Docs
ALL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive.file",
]

# In-memory state storage (in production, use a signed cookie or Redis)
_oauth_state: dict[str, dict] = {}


@router.get("/google/status")
async def google_auth_status():
    """Return the current OAuth authentication status."""
    is_gmail_authed = False
    is_docs_authed = False

    for token_path, label in [(_TOKEN_PATH, "gmail"), (_DOCS_TOKEN_PATH, "docs")]:
        if token_path.exists():
            try:
                creds = Credentials.from_authorized_user_file(str(token_path), ALL_SCOPES)
                if creds and creds.valid:
                    if label == "gmail":
                        is_gmail_authed = True
                    else:
                        is_docs_authed = True
                elif creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                    with open(token_path, "w") as f:
                        f.write(creds.to_json())
                    if label == "gmail":
                        is_gmail_authed = True
                    else:
                        is_docs_authed = True
            except Exception as e:
                logger.warning(f"Auth status check failed for {label}: {e}")

    # Check MCP server token (shared)
    mcp_token = _BACKEND_ROOT.parent / "mcp_server" / "credentials" / "token.json"
    if mcp_token.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(mcp_token), ALL_SCOPES)
            if creds and (creds.valid or (creds.expired and creds.refresh_token)):
                is_gmail_authed = True
                is_docs_authed = True
        except Exception:
            pass

    return {
        "gmail_authenticated": is_gmail_authed,
        "docs_authenticated": is_docs_authed,
        "fully_authenticated": is_gmail_authed and is_docs_authed,
        "login_url": "/api/auth/google/login",
        "secret_path_found": _SECRET_PATH.exists() or "GOOGLE_CLIENT_SECRET_JSON" in os.environ,
    }


@router.get("/google/login")
async def google_login():
    """
    Initiate the Google OAuth consent flow.
    Redirects the user to Google's authorization page.
    """
    secret_json = os.environ.get("GOOGLE_CLIENT_SECRET_JSON")
    if not _SECRET_PATH.exists() and not secret_json:
        raise HTTPException(
            status_code=503,
            detail=(
                f"OAuth client secret not found at: {_SECRET_PATH}. "
                "Please set GOOGLE_CLIENT_SECRET_JSON or GOOGLE_CLIENT_SECRET_PATH environment variable."
            ),
        )

    try:
        if secret_json:
            flow = Flow.from_client_config(
                json.loads(secret_json),
                scopes=ALL_SCOPES,
                redirect_uri=_REDIRECT_URI,
            )
        else:
            flow = Flow.from_client_secrets_file(
                str(_SECRET_PATH),
                scopes=ALL_SCOPES,
                redirect_uri=_REDIRECT_URI,
            )
        auth_url, state = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",
        )
        # Store flow state for callback verification
        _oauth_state[state] = {
            "flow_state": state,
            "code_verifier": getattr(flow, "code_verifier", None)
        }
        logger.info(f"Redirecting to Google OAuth: {auth_url[:80]}…")
        return RedirectResponse(url=auth_url)
    except Exception as e:
        logger.error(f"OAuth login initiation failed: {e}")
        raise HTTPException(status_code=500, detail=f"OAuth setup failed: {e}")


@router.get("/google/callback")
async def google_callback(code: str = "", state: str = "", error: str = ""):
    """
    Handle the OAuth callback from Google.
    Exchanges authorization code for tokens and stores them.
    """
    if error:
        logger.warning(f"OAuth error from Google: {error}")
        return JSONResponse(
            status_code=400,
            content={"error": f"OAuth error: {error}", "message": "Authentication was denied or failed."},
        )

    if not code:
        raise HTTPException(status_code=400, detail="No authorization code received")

    try:
        secret_json = os.environ.get("GOOGLE_CLIENT_SECRET_JSON")
        if secret_json:
            flow = Flow.from_client_config(
                json.loads(secret_json),
                scopes=ALL_SCOPES,
                redirect_uri=_REDIRECT_URI,
                state=state,
            )
        else:
            flow = Flow.from_client_secrets_file(
                str(_SECRET_PATH),
                scopes=ALL_SCOPES,
                redirect_uri=_REDIRECT_URI,
                state=state,
            )

        # Restore code_verifier if it exists in state
        if state in _oauth_state and _oauth_state[state].get("code_verifier"):
            flow.code_verifier = _oauth_state[state]["code_verifier"]

        flow.fetch_token(code=code)
        creds = flow.credentials

        # Save tokens
        _CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)
        token_data = creds.to_json()

        # Save to both token paths (Gmail + Docs use same token)
        for token_path in [_TOKEN_PATH, _DOCS_TOKEN_PATH]:
            with open(token_path, "w") as f:
                f.write(token_data)

        # Also save to MCP server credentials for shared use
        mcp_creds_dir = _BACKEND_ROOT.parent / "mcp_server" / "credentials"
        mcp_creds_dir.mkdir(parents=True, exist_ok=True)
        with open(mcp_creds_dir / "token.json", "w") as f:
            f.write(token_data)

        logger.info("Google OAuth tokens saved successfully (Gmail + Docs + MCP server)")

        # Reinitialize services with new credentials
        from services.gmail_service import get_gmail_service
        from services.document_service import get_document_service
        import services.gmail_service as gmail_mod
        import services.document_service as doc_mod
        gmail_mod._gmail_service = None  # Force re-init
        doc_mod._document_service = None  # Force re-init

        return JSONResponse(content={
            "status": "authenticated",
            "message": "Google OAuth authentication successful! Gmail and Docs are now connected.",
            "gmail_ready": True,
            "docs_ready": True,
            "note": "You can now use the approval flow to create Gmail drafts and append to Google Docs.",
        })

    except Exception as e:
        logger.error(f"OAuth callback failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"OAuth callback failed: {e}")


@router.post("/google/revoke")
async def google_revoke():
    """Revoke stored Google OAuth tokens (force re-authentication)."""
    revoked = []
    for token_path in [_TOKEN_PATH, _DOCS_TOKEN_PATH]:
        if token_path.exists():
            token_path.unlink()
            revoked.append(str(token_path))

    mcp_token = _BACKEND_ROOT.parent / "mcp_server" / "credentials" / "token.json"
    if mcp_token.exists():
        mcp_token.unlink()
        revoked.append(str(mcp_token))

    # Reset service instances
    import services.gmail_service as gmail_mod
    import services.document_service as doc_mod
    gmail_mod._gmail_service = None
    doc_mod._document_service = None

    logger.info(f"Revoked tokens: {revoked}")
    return {
        "status": "revoked",
        "revoked_files": revoked,
        "message": "Google credentials revoked. Re-authenticate via GET /api/auth/google/login.",
    }
