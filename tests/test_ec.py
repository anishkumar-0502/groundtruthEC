"""Tests for EC search input validation, rate limiting, and workflow orchestration."""

import asyncio
import time
import pytest
from pydantic import ValidationError

from app.portal.client import PortalRateLimiter
from app.schemas.ec import CreateSessionRequest, SearchMode, parse_and_validate_date
from app.services.ec_service import normalize_portal_date


def test_normalize_portal_date():
    assert normalize_portal_date("01/01/2010") == "01-Jan-2010"
    assert normalize_portal_date("31/12/2010") == "31-Dec-2010"
    assert normalize_portal_date("2010-01-01") == "01-Jan-2010"
    assert normalize_portal_date("2010-12-31") == "31-Dec-2010"
    assert normalize_portal_date("01-Jan-2010") == "01-Jan-2010"
    assert normalize_portal_date("31-Dec-2010") == "31-Dec-2010"


def test_closed_sro_rejected():
    with pytest.raises(ValidationError) as exc:
        CreateSessionRequest(
            search_mode=SearchMode.SURVEY_NUMBER,
            district_id="50006",
            sro_id="20121:0",  # Closed office ending in :0
            village_id="2739",
            survey_number="999",
            start_date="01/01/2010",
            end_date="31/12/2010",
        )
    assert "Closed" in str(exc.value)


def test_date_validation_formats():
    # Valid DD/MM/YYYY
    assert parse_and_validate_date("01/01/2010") == "01/01/2010"
    assert parse_and_validate_date("31/12/2020") == "31/12/2020"

    # Valid ISO YYYY-MM-DD normalized to DD/MM/YYYY
    assert parse_and_validate_date("2010-01-01") == "01/01/2010"
    assert parse_and_validate_date("2020-12-31") == "31/12/2020"

    # Invalid formats
    with pytest.raises(ValueError):
        parse_and_validate_date("invalid-date")
    with pytest.raises(ValueError):
        parse_and_validate_date("32/01/2010")
    with pytest.raises(ValueError):
        parse_and_validate_date("01/13/2010")


def test_request_validation_dates_order():
    with pytest.raises(ValidationError) as exc:
        CreateSessionRequest(
            search_mode=SearchMode.SURVEY_NUMBER,
            district_id="50006",
            sro_id="20120:1",
            village_id="2739",
            survey_number="999",
            start_date="31/12/2010",
            end_date="01/01/2010",  # start > end
        )
    assert "cannot be later than end date" in str(exc.value)


def test_request_validation_year_limit():
    with pytest.raises(ValidationError) as exc:
        CreateSessionRequest(
            search_mode=SearchMode.SURVEY_NUMBER,
            district_id="50006",
            sro_id="20120:1",
            village_id="2739",
            survey_number="999",
            start_date="01/01/1850",
            end_date="31/12/1850",
        )
    assert "must be 1900 or later" in str(exc.value)


def test_request_validation_modes():
    # Survey number mode requires survey_number
    with pytest.raises(ValidationError):
        CreateSessionRequest(
            search_mode=SearchMode.SURVEY_NUMBER,
            district_id="50006",
            sro_id="20120:1",
            village_id="2739",
            start_date="01/01/2010",
            end_date="31/12/2010",
            survey_number="",  # missing
        )

    # Ward block mode requires ward_code and block_code
    with pytest.raises(ValidationError):
        CreateSessionRequest(
            search_mode=SearchMode.WARD_BLOCK,
            district_id="50006",
            sro_id="20120:1",
            village_id="2739",
            start_date="01/01/2010",
            end_date="31/12/2010",
            ward_code="",
            block_code="",
        )


@pytest.mark.asyncio
async def test_rate_limiter_timing():
    # Use a small test interval (0.2s)
    limiter = PortalRateLimiter(min_interval_seconds=0.2)

    t0 = time.monotonic()
    await limiter.acquire()
    t1 = time.monotonic()
    await limiter.acquire()
    t2 = time.monotonic()

    # Second acquire should have waited ~0.2s from t0
    elapsed = t2 - t0
    assert elapsed >= 0.18, f"Expected elapsed >= 0.18s, got {elapsed:.3f}s"

