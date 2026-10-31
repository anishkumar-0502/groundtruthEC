"""Tests for application session management and lifecycle."""

from datetime import datetime, timedelta, timezone
import pytest
from app.errors import SessionExpiredError
from app.portal.client import PortalHttpClient
from app.portal.sessions import SessionManager


@pytest.mark.asyncio
async def test_session_lifecycle():
    manager = SessionManager()
    client = PortalHttpClient()

    session = await manager.create_session(
        client=client,
        search_params={"district_id": "50006", "survey_number": "999"},
        csrf_token="csrf-123",
        auth_token="auth-456",
    )

    assert session.session_id is not None
    assert len(session.session_id) >= 32
    assert session.csrf_token == "csrf-123"
    assert session.auth_token == "auth-456"

    # Lookup active session
    retrieved = await manager.get_session(session.session_id)
    assert retrieved.session_id == session.session_id
    assert not retrieved.is_expired

    # Invalidate session
    await manager.invalidate_session(session.session_id)
    with pytest.raises(SessionExpiredError):
        await manager.get_session(session.session_id)


@pytest.mark.asyncio
async def test_session_expiration():
    manager = SessionManager()
    client = PortalHttpClient()

    session = await manager.create_session(
        client=client,
        search_params={"survey_number": "123"},
    )

    # Force expiration
    session.expires_at = datetime.now(timezone.utc) - timedelta(seconds=10)
    assert session.is_expired

    # Getting expired session should raise and invalidate
    with pytest.raises(SessionExpiredError):
        await manager.get_session(session.session_id)

    # Cleanup expired
    cleaned = await manager.cleanup_expired()
    assert cleaned == 0  # Already cleaned during get


@pytest.mark.asyncio
async def test_cleanup_expired_multiple():
    manager = SessionManager()

    # Create 3 sessions, 2 expired
    s1 = await manager.create_session(client=PortalHttpClient(), search_params={})
    s2 = await manager.create_session(client=PortalHttpClient(), search_params={})
    s3 = await manager.create_session(client=PortalHttpClient(), search_params={})

    s1.expires_at = datetime.now(timezone.utc) - timedelta(seconds=20)
    s2.expires_at = datetime.now(timezone.utc) - timedelta(seconds=10)

    cleaned = await manager.cleanup_expired()
    assert cleaned == 2

    # s3 still valid
    assert (await manager.get_session(s3.session_id)).session_id == s3.session_id
    await manager.close_all()

