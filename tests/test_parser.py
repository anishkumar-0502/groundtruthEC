"""Tests for ECResultParser status classification, record parsing, and edge cases."""

from decimal import Decimal
from pathlib import Path
import pytest
from app.portal.parser import ECResultParser, parse_currency, parse_year
from app.schemas.ec import ECStatus

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_parse_currency():
    assert parse_currency("₹ 2,50,000.00") == Decimal("250000.00")
    assert parse_currency("12,50,000.50") == Decimal("1250000.50")
    assert parse_currency("0") == Decimal("0")
    assert parse_currency("") is None
    assert parse_currency(None) is None


def test_parse_year():
    assert parse_year("1234/2010") == 2010
    assert parse_year("15/06/2010") == 2010
    assert parse_year("Doc 1998") == 1998
    assert parse_year("No year here") is None


def test_classify_found_status():
    html = (FIXTURES_DIR / "search_found_single.html").read_text(encoding="utf-8")
    status, msg = ECResultParser.classify_response(html)
    assert status == ECStatus.FOUND


def test_classify_no_records_status():
    html = (FIXTURES_DIR / "search_no_records.html").read_text(encoding="utf-8")
    status, msg = ECResultParser.classify_response(html)
    assert status == ECStatus.NO_RECORDS
    assert "No transactions registered" in msg


def test_classify_session_expired():
    html = (FIXTURES_DIR / "session_expired.html").read_text(encoding="utf-8")
    status, msg = ECResultParser.classify_response(html)
    assert status == ECStatus.SESSION_EXPIRED


def test_classify_wrong_captcha():
    html = (FIXTURES_DIR / "search_wrong_captcha.html").read_text(encoding="utf-8")
    status, msg = ECResultParser.classify_response(html)
    assert status == ECStatus.WRONG_CAPTCHA


def test_classify_smoke_alert_wrong_captcha():
    html = "<html><head><title>Search EC</title></head><body><script>smoke.alert('Please Enter Valid Captcha',function(e){});</script></body></html>"
    status, msg = ECResultParser.classify_response(html)
    assert status == ECStatus.WRONG_CAPTCHA


def test_classify_portal_error_page():
    html = "<html><head><title>Error Page</title></head><body><p>Sorry! An error has occurred while processing your request.</p></body></html>"
    status, msg = ECResultParser.classify_response(html)
    assert status == ECStatus.PORTAL_ERROR
    assert "internal error" in msg.lower()


def test_classify_too_many_records():
    html = "<html><body><div id='alertMsg'>அதிகப்படியான பதிவுருக்கள் (Too many records)</div></body></html>"
    status, msg = ECResultParser.classify_response(html)
    assert status == ECStatus.TOO_MANY_RECORDS


def test_classify_malformed_html():
    html = (FIXTURES_DIR / "malformed_table.html").read_text(encoding="utf-8")
    status, msg = ECResultParser.classify_response(html)
    # Should not report no_records on unknown or malformed structure!
    assert status != ECStatus.NO_RECORDS
    assert status in [ECStatus.PORTAL_ERROR, ECStatus.FOUND]


def test_parse_single_record_details():
    html = (FIXTURES_DIR / "search_found_single.html").read_text(encoding="utf-8")
    records = ECResultParser.parse_records(html)

    assert len(records) == 1
    rec = records[0]
    assert rec.document_number == "1234/2010"
    assert rec.document_year == 2010
    assert rec.registration_date == "15/06/2010"
    assert "Sale Deed" in rec.document_type
    assert "கிரைய ஆவணம்" in rec.document_type
    assert rec.executants == ["முருகன் (Murugan)"]
    assert rec.claimants == ["கந்தன் (Kandhan)"]
    assert rec.consideration_value == Decimal("250000.00")
    assert rec.market_value == Decimal("300000.00")
    assert rec.survey_numbers == ["999", "1A"] or "999/1A" in rec.survey_numbers


def test_parse_multiple_records():
    html = (FIXTURES_DIR / "search_found_multiple.html").read_text(encoding="utf-8")
    records = ECResultParser.parse_records(html)

    assert len(records) == 3

    # First record: Mortgage
    assert records[0].document_number == "101/2010"
    assert records[0].consideration_value == Decimal("500000")
    assert "Arun" in records[0].executants[0]

    # Second record: Multiple executants and multiple survey numbers
    assert records[1].document_number == "202/2010"
    assert len(records[1].executants) >= 1
    assert records[1].consideration_value == Decimal("1250000.50")
    assert records[1].market_value == Decimal("1500000.00")

    # Third record: Zero consideration
    assert records[2].document_number == "303/2010"
    assert records[2].consideration_value == Decimal("0")


def test_extract_pdf_params():
    html = (FIXTURES_DIR / "search_found_single.html").read_text(encoding="utf-8")
    params = ECResultParser.extract_pdf_params(html)

    assert params is not None
    assert params["appTransId"] == "12345678"
    assert params["docCreateAppId"] == "8400001"
    assert params["templateIds"] == "TPL_001"
    assert "test_val" in params["jsonString"]

