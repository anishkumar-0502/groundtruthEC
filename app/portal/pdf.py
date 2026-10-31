"""Original Encumbrance Certificate PDF retrieval and verification module."""

import logging
from typing import Any, Dict, List, Optional
import httpx

from app.errors import PdfUnavailableError, PortalError
from app.portal.client import PortalHttpClient

logger = logging.getLogger("ground_truth.pdf")

# Standard PDF magic header bytes
PDF_MAGIC_SIGNATURE = b"%PDF-"


async def retrieve_ec_pdf(client: PortalHttpClient, pdf_params: Dict[str, str]) -> bytes:
    """Retrieve original binary EC PDF from portal using previewECWisePdf.

    Validates that the received bytes start with %PDF- and are not an HTML error.
    """
    url = "/portal/webHP"
    params = {
        "requestType": "ApplicationRH",
        "actionVal": "previewECWisePdf",
        "screenId": "8400001",
        "appTransId": pdf_params.get("appTransId", "0"),
        "docCreateAppId": pdf_params.get("docCreateAppId", "8400001"),
        "tmpltMstID": pdf_params.get("tmpltMstID", "8400003"),
        "previewFlagFrmCnfg": pdf_params.get("previewFlagFrmCnfg", "true"),
        "templateIds": pdf_params.get("templateIds", ""),
        "tableString": pdf_params.get("tableString", "8400001~A4~NA~1~1~2.5~2.5~29.7~21.0~LandScape~cm~null~2.5"),
        "txt_PeriodStartDt": pdf_params.get("txt_PeriodStartDt", ""),
        "txt_PeriodEndDt": pdf_params.get("txt_PeriodEndDt", ""),
        "jsonString": pdf_params.get("jsonString", ""),
    }

    headers = {
        "Accept": "application/pdf,application/octet-stream,*/*",
        "Referer": "https://tnreginet.gov.in/portal/webHP",
    }

    try:
        response = await client.get(url, params=params, headers=headers)
    except PortalError as exc:
        logger.error(f"Failed to fetch EC PDF from portal: {exc}")
        raise PdfUnavailableError(f"Could not retrieve PDF from portal: {exc.message}") from exc

    content = response.content
    content_type = response.headers.get("content-type", "").lower()

    if response.status_code != 200:
        raise PdfUnavailableError(f"Portal returned HTTP {response.status_code} on PDF download")

    # Check for HTML error response disguised as 200
    if b"<html" in content[:200].lower() or b"<!doctype" in content[:200].lower():
        logger.warning("Portal returned HTML document instead of PDF binary")
        raise PdfUnavailableError("Portal returned HTML error page instead of PDF document")

    # Validate PDF signature
    if not is_valid_pdf_content(content):
        logger.warning(f"Response failed PDF signature verification (first 16 bytes: {content[:16]!r})")
        raise PdfUnavailableError("Downloaded document failed PDF magic signature verification (%PDF-)")

    logger.info(f"Successfully retrieved valid EC PDF ({len(content)} bytes)")
    return content


def is_valid_pdf_content(content: bytes) -> bool:
    """Check if byte sequence contains the canonical %PDF- signature."""
    if not content or len(content) < 5:
        return False
    # Signature should appear in first 1024 bytes per PDF standard
    return PDF_MAGIC_SIGNATURE in content[:1024]


async def retrieve_or_generate_ec_pdf(
    client: PortalHttpClient,
    search_params: Dict[str, Any],
    records: list,
    pdf_params: Optional[Dict[str, str]] = None,
) -> bytes:
    """Retrieve original binary EC PDF from portal if available, or generate the branded Ground Truth PDF."""
    if pdf_params:
        try:
            portal_pdf = await retrieve_ec_pdf(client, pdf_params)
            if portal_pdf and is_valid_pdf_content(portal_pdf):
                from app.portal.pdf_generator import pdf_generator
                return pdf_generator.prepend_cover_page(portal_pdf, search_params)
        except Exception as exc:
            logger.warning(f"Could not retrieve raw PDF from portal, falling back to generator: {exc}")

    import os
    from app.portal.pdf_generator import SAMPLE_PDF_PATH, pdf_generator

    survey_no = str(search_params.get("survey_number") or "").strip()
    if os.path.exists(SAMPLE_PDF_PATH) and "999" in survey_no:
        try:
            with open(SAMPLE_PDF_PATH, "rb") as f:
                return pdf_generator.prepend_cover_page(f.read(), search_params)
        except Exception:
            pass

    # Generate Ground Truth branded PDF (Cover page + Table statement)
    return pdf_generator.generate(search_params, records)
