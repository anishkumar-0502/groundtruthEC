"""In-memory application and portal session manager."""

import asyncio
from datetime import datetime, timedelta, timezone
import logging
import secrets
from typing import Any, Dict, Optional
from dataclasses import dataclass, field

from app.config import settings
from app.errors import SessionExpiredError
from app.portal.client import PortalHttpClient

logger = logging.getLogger("ground_truth.sessions")


@dataclass
class SearchSession:
    """Represents an active EC search session tied to an isolated portal HTTP client."""

    session_id: str
    client: PortalHttpClient
    search_params: Dict[str, Any]
    csrf_token: str = ""
    auth_token: str = ""
    captcha_bytes: Optional[bytes] = None
    captcha_content_type: str = "image/png"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc) + timedelta(seconds=settings.session_ttl_seconds)
    )
    status: str = "captcha_required"
    results: Optional[Dict[str, Any]] = None
    pdf_params: Optional[Dict[str, Any]] = None
    records: list = field(default_factory=list)

    @property
    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) >= self.expires_at


class SessionManager:
    """Manages ephemeral in-memory search sessions.

    Note: In-memory storage is suitable for single-process local development.
    Sessions will disappear on process restart and do not persist across multiple
    production workers. A multi-worker production setup would require centralized
    session storage (e.g. Redis) or sticky routing.
    """

    def __init__(self):
        self._sessions: Dict[str, SearchSession] = {}
        self._lock = asyncio.Lock()

    async def create_session(
        self,
        client: PortalHttpClient,
        search_params: Dict[str, Any],
        csrf_token: str = "",
        auth_token: str = "",
        captcha_bytes: Optional[bytes] = None,
        captcha_content_type: str = "image/png",
    ) -> SearchSession:
        """Create and register a new cryptographically secure session."""
        session_id = secrets.token_urlsafe(32)
        session = SearchSession(
            session_id=session_id,
            client=client,
            search_params=search_params,
            csrf_token=csrf_token,
            auth_token=auth_token,
            captcha_bytes=captcha_bytes,
            captcha_content_type=captcha_content_type,
        )
        async with self._lock:
            self._sessions[session_id] = session
        logger.info(f"Created session {session_id[:8]}... (expires at {session.expires_at.isoformat()})")
        return session

    async def get_session(self, session_id: str) -> SearchSession:
        """Retrieve a session by ID, validating its expiration status."""
        async with self._lock:
            session = self._sessions.get(session_id)

        if not session:
            logger.warning(f"Session {session_id[:8]}... not found")
            raise SessionExpiredError("Session not found")

        if session.is_expired:
            logger.warning(f"Session {session_id[:8]}... has expired")
            await self.invalidate_session(session_id)
            raise SessionExpiredError("Session has expired. Please initiate a new search.")

        return session

    async def invalidate_session(self, session_id: str) -> None:
        """Remove a session and cleanly close its associated HTTP client."""
        async with self._lock:
            session = self._sessions.pop(session_id, None)

        if session:
            try:
                await session.client.close()
            except Exception as exc:
                logger.error(f"Error closing client for session {session_id[:8]}...: {exc}")
            logger.info(f"Invalidated session {session_id[:8]}...")

    async def cleanup_expired(self) -> int:
        """Remove all expired sessions and close their clients."""
        expired_ids = []
        now = datetime.now(timezone.utc)
        async with self._lock:
            for sid, sess in list(self._sessions.items()):
                if now >= sess.expires_at:
                    expired_ids.append(sid)

        for sid in expired_ids:
            await self.invalidate_session(sid)

        if expired_ids:
            logger.info(f"Cleaned up {len(expired_ids)} expired session(s)")
        return len(expired_ids)

    async def close_all(self) -> None:
        """Close all active sessions on shutdown."""
        async with self._lock:
            sessions = list(self._sessions.values())
            self._sessions.clear()

        for session in sessions:
            try:
                await session.client.close()
            except Exception as exc:
                logger.debug(f"Error during shutdown client cleanup: {exc}")


# Global process session manager singleton
session_manager = SessionManager()

