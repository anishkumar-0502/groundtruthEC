"""Tests for PDF signature validation, retrieval, and error handling."""

import pytest
from app.errors import PdfUnavailableError
from app.portal.client import PortalHttpClient
from app.portal.pdf import is_valid_pdf_content, retrieve_ec_pdf


def test_is_valid_pdf_content():
    # Valid PDF magic headers
    assert is_valid_pdf_content(b"%PDF-1.4\n1 0 obj\n<<>>\nendobj")
    assert is_valid_pdf_content(b"%PDF-1.7 standard header")
    assert is_valid_pdf_content(b"\r\n%PDF-1.3 with preceding whitespace")

    # Invalid contents
    assert not is_valid_pdf_content(b"<html><head><title>Error</title></head></html>")
    assert not is_valid_pdf_content(b"")
    assert not is_valid_pdf_content(b"%PD")
    assert not is_valid_pdf_content(b"RANDOM_NON_PDF_BYTES")


@pytest.mark.asyncio
async def test_retrieve_ec_pdf_rejects_html_error(monkeypatch):
    client = PortalHttpClient()

    class MockResponse:
        status_code = 200
        headers = {"content-type": "text/html"}
        content = b"<!DOCTYPE html><html><body>Error occurred generating PDF</body></html>"

    async def mock_get(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr(client, "get", mock_get)

    with pytest.raises(PdfUnavailableError) as exc_info:
        await retrieve_ec_pdf(client, {"appTransId": "123"})

    assert "HTML error page" in str(exc_info.value)
    await client.close()


@pytest.mark.asyncio
async def test_retrieve_ec_pdf_success(monkeypatch):
    client = PortalHttpClient()

    valid_pdf_bytes = b"%PDF-1.5\n%Mock PDF binary content for testing\n%%EOF"

    class MockResponse:
        status_code = 200
        headers = {"content-type": "application/pdf"}
        content = valid_pdf_bytes

    async def mock_get(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr(client, "get", mock_get)

    result = await retrieve_ec_pdf(client, {"appTransId": "123"})
    assert result.startswith(b"%PDF-")
    await client.close()


@pytest.mark.asyncio
async def test_retrieve_or_generate_ec_pdf_fallback():
    from app.portal.pdf import retrieve_or_generate_ec_pdf

    client = PortalHttpClient()
    search_params = {
        "sro_name": "Madukkarai",
        "village_name": "Madukkarai",
        "survey_number": "999",
        "subdivision_number": "1",
        "start_date": "01-Jan-2010",
        "end_date": "30-Oct-2026",
    }
    records = [
        {
            "document_number": "3366/2010",
            "document_year": 2010,
            "registration_date": "21-Jul-2010",
            "document_type": "Receipt",
            "executants": ["R. Govindaraj"],
            "claimants": ["Kannathal"],
            "consideration_value": 100000,
        }
    ]

    pdf_bytes = await retrieve_or_generate_ec_pdf(
        client=client,
        search_params=search_params,
        records=records,
        pdf_params=None,  # Triggers Ground Truth branded generator
    )

    assert pdf_bytes.startswith(b"%PDF-")
    assert is_valid_pdf_content(pdf_bytes)
    assert len(pdf_bytes) > 1000
    await client.close()


def test_prepend_cover_page_with_sample_pdf():
    import os
    from app.portal.pdf_generator import SAMPLE_PDF_PATH, pdf_generator

    assert os.path.exists(SAMPLE_PDF_PATH)
    with open(SAMPLE_PDF_PATH, "rb") as f:
        sample_bytes = f.read()

    search_params = {
        "sro_name": "Madukkarai",
        "village_name": "Madukkarai",
        "survey_number": "999",
        "subdivision_number": "1",
        "start_date": "01-Jan-2010",
        "end_date": "30-Oct-2026",
    }

    merged_pdf = pdf_generator.prepend_cover_page(sample_bytes, search_params)

    assert is_valid_pdf_content(merged_pdf)
    assert len(merged_pdf) > len(sample_bytes)

    # Verify that the cover stream within the incremental update contains the expected Ground Truth text
    import re
    import zlib
    inc_part = merged_pdf[len(sample_bytes):]
    streams = re.findall(rb"stream\r?\n(.*?)\r?\nendstream", inc_part, re.DOTALL)
    decompressed_texts = []
    for s in streams:
        try:
            decompressed_texts.append(zlib.decompress(s))
        except Exception:
            pass
    full_decomp = b"\n".join(decompressed_texts)
    assert b"GROUND TRUTH" in full_decomp
    assert b"Madukkarai" in full_decomp
    assert b"999/1" in full_decomp
    assert b"thegroundtruth.site" in full_decomp


def test_generate_original_government_pdf():
    import re
    import zlib
    from app.portal.pdf_generator import pdf_generator

    search_params = {
        "sro_name": "Madukkarai",
        "village_name": "Madukkarai",
        "survey_number": "999",
        "subdivision_number": "1",
    }
    gov_pdf = pdf_generator.generate_original_government_pdf(search_params, [])
    assert is_valid_pdf_content(gov_pdf)
    assert len(gov_pdf) > 100000

    # Verify that the government PDF also includes the Ground Truth cover page as Page 1
    streams = re.findall(rb"stream\r?\n(.*?)\r?\nendstream", gov_pdf, re.DOTALL)
    decompressed_texts = []
    for s in streams:
        try:
            decompressed_texts.append(zlib.decompress(s))
        except Exception:
            pass
    full_decomp = b"\n".join(decompressed_texts)
    assert b"GROUND TRUTH" in full_decomp


def test_no_duplicate_cover_page_in_government_pdf():
    """Verify that prepending the corporate cover page replaces any legacy white cover page (object 322)."""
    import os
    import re
    from app.portal.pdf_generator import SAMPLE_PDF_PATH, pdf_generator

    assert os.path.exists(SAMPLE_PDF_PATH)
    with open(SAMPLE_PDF_PATH, "rb") as f:
        sample_bytes = f.read()

    search_params = {
        "sro_name": "Madukkarai",
        "village_name": "Madukkarai",
        "survey_number": "999",
        "subdivision_number": "",
    }
    gov_pdf = pdf_generator.prepend_cover_page(sample_bytes, search_params)
    assert is_valid_pdf_content(gov_pdf)

    # Find the latest /Kids array in the document
    kids_matches = re.findall(rb"/Kids\s*\[(.*?)\]", gov_pdf)
    assert len(kids_matches) > 0
    latest_kids = kids_matches[-1].decode()

    # 322 0 R was the legacy white cover page; it MUST NOT be in the latest Kids array!
    assert "322 0 R" not in latest_kids
    # The first child in Kids must be our new cover page object, followed by 4 0 R (Government EC page 1)
    kids_tokens = latest_kids.strip().split()
    first_page_ref = f"{kids_tokens[0]} {kids_tokens[1]} {kids_tokens[2]}"
    second_page_ref = f"{kids_tokens[3]} {kids_tokens[4]} {kids_tokens[5]}"
    assert second_page_ref == "4 0 R"
    assert first_page_ref != "322 0 R"


@pytest.mark.asyncio
async def test_get_record_pdf_single_transaction():
    from app.services.ec_service import ec_service
    # Generate tailored PDF for record 3366/2010
    pdf_bytes = await ec_service.get_record_pdf("non-existent-session", "3366/2010")
    assert pdf_bytes.startswith(b"%PDF-")
    assert is_valid_pdf_content(pdf_bytes)
    assert len(pdf_bytes) > 1000



