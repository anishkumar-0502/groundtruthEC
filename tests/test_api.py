"""End-to-end API router offline tests with mocked portal responses."""

from pathlib import Path
from unittest.mock import AsyncMock, patch
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.portal.client import PortalHttpClient
from app.portal.sessions import session_manager
from app.schemas.locations import LocationItem

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def mock_ec_html():
    return (FIXTURES_DIR / "ec_page.html").read_text(encoding="utf-8")


@pytest.fixture
def mock_districts_xml():
    return (FIXTURES_DIR / "districts.xml").read_text(encoding="utf-8")


@pytest.fixture
def mock_sros_xml():
    return (FIXTURES_DIR / "sros.xml").read_text(encoding="utf-8")


@pytest.fixture
def mock_villages_xml():
    return (FIXTURES_DIR / "villages.xml").read_text(encoding="utf-8")


@pytest.fixture
def mock_found_html():
    return (FIXTURES_DIR / "search_found_single.html").read_text(encoding="utf-8")


@pytest.fixture
def mock_no_records_html():
    return (FIXTURES_DIR / "search_no_records.html").read_text(encoding="utf-8")


@pytest.mark.asyncio
async def test_ec_session_invalid_calendar_date():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(
            "/ec/sessions",
            json={
                "search_mode": "survey_number",
                "district_id": "50006",
                "sro_id": "20120:1",
                "village_id": "2739",
                "survey_number": "999",
                "start_date": "01/01/2010",
                "end_date": "30/02/2020",  # February 30th does not exist
            },
        )
        assert resp.status_code == 422
        data = resp.json()
        assert data["status"] == "validation_error"
        assert "not a valid calendar date" in data["message"] or "range" in data["message"]


@pytest.mark.asyncio
async def test_locations_api_workflow(
    mock_ec_html, mock_districts_xml, mock_sros_xml, mock_villages_xml
):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        with patch.object(
            PortalHttpClient, "get", new_callable=AsyncMock
        ) as mock_get, patch.object(
            PortalHttpClient, "post", new_callable=AsyncMock
        ) as mock_post:

            # Mock initial page for zones
            class MockResponse:
                def __init__(self, text, status_code=200):
                    self.text = text
                    self.status_code = status_code
                    self.headers = {}

            mock_get.return_value = MockResponse(mock_ec_html)

            # 1. Test zones endpoint (default English)
            res_zones = await client.get("/locations/zones")
            assert res_zones.status_code == 200
            zones_data = res_zones.json()["data"]
            assert len(zones_data) >= 1
            assert any(z["name"] in ["Coimbatore", "கோயம்புத்தூர்"] for z in zones_data)

            # 2. Test districts endpoint (default English)
            mock_post.return_value = MockResponse(mock_districts_xml)
            res_dist = await client.get("/locations/districts?zone_id=2")
            assert res_dist.status_code == 200
            dist_data = res_dist.json()["data"]
            assert any(d["name"] in ["Coimbatore South", "கோயம்புத்தூர் தெற்கு"] for d in dist_data)

            # 3. Test SROs endpoint (default English)
            mock_post.return_value = MockResponse(mock_sros_xml)
            res_sros = await client.get("/locations/sros?district_id=50006")
            assert res_sros.status_code == 200
            sros_data = res_sros.json()["data"]
            assert any(s["name"] in ["Madukkarai", "மதுக்கரை"] for s in sros_data)

            # 4. Test Villages endpoint
            mock_post.return_value = MockResponse(mock_villages_xml)
            res_vil = await client.get("/locations/villages?sro_id=20120:1")
            assert res_vil.status_code == 200
            vil_data = res_vil.json()["data"]
            assert any(v["name"] in ["Madukkarai", "மதுக்கரை", "எட்டிமடை"] for v in vil_data)


@pytest.mark.asyncio
async def test_ec_session_and_search_found_workflow(mock_ec_html, mock_found_html):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:

        class MockResponse:
            def __init__(self, text="", content=b"", status_code=200, headers=None):
                self.text = text
                self.content = content
                self.status_code = status_code
                self.headers = headers or {"content-type": "image/png"}

        fake_captcha_png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 200

        with patch.object(
            PortalHttpClient, "get", new_callable=AsyncMock
        ) as mock_get, patch.object(
            PortalHttpClient, "post", new_callable=AsyncMock
        ) as mock_post:

            # Configure mock_get for initial page and captcha
            def side_effect_get(url, *args, **kwargs):
                if "SimpleCaptcha" in url:
                    return MockResponse(content=fake_captcha_png, headers={"content-type": "image/png"})
                return MockResponse(text=mock_ec_html)

            mock_get.side_effect = side_effect_get
            mock_post.return_value = MockResponse(text="<?xml ...?><select></select>")

            # 1. Create Session
            payload = {
                "search_mode": "survey_number",
                "zone_id": "2",
                "district_id": "50006",
                "sro_id": "20120:1",
                "village_id": "2739",
                "survey_number": "999",
                "subdivision_number": "1A",
                "start_date": "01/01/2010",
                "end_date": "31/12/2010",
            }
            res_create = await client.post("/ec/sessions", json=payload)
            assert res_create.status_code == 200
            create_data = res_create.json()
            assert create_data["status"] == "captcha_required"
            session_id = create_data["session_id"]
            assert create_data["captcha_image_url"] == f"/ec/sessions/{session_id}/captcha"

            # 2. Retrieve CAPTCHA image
            res_cap = await client.get(f"/ec/sessions/{session_id}/captcha")
            assert res_cap.status_code == 200
            assert res_cap.headers["content-type"].startswith("image/png")
            assert res_cap.content == fake_captcha_png

            # 3. Submit Search (Mock captcha check OK and search returns records)
            def side_effect_post(url, *args, **kwargs):
                if "checkCaptcha" in url:
                    return MockResponse(text="<?xml ...?>#OK#true")
                return MockResponse(text=mock_found_html)

            mock_post.side_effect = side_effect_post

            res_search = await client.post(
                f"/ec/sessions/{session_id}/search",
                json={"captcha_text": "ABCD"},
            )
            assert res_search.status_code == 200
            search_data = res_search.json()
            assert search_data["status"] == "found"
            assert search_data["total_records"] == 1
            assert search_data["records"][0]["document_number"] == "1234/2010"
            assert search_data["pdf_available"] is True
            assert search_data["pdf_url"] == f"/ec/sessions/{session_id}/pdf"

            # 4. Download PDF
            mock_pdf_bytes = b"%PDF-1.4\nMock PDF binary content\n%%EOF"
            mock_get.side_effect = lambda *args, **kwargs: MockResponse(
                content=mock_pdf_bytes,
                headers={"content-type": "application/pdf"},
            )

            res_pdf = await client.get(f"/ec/sessions/{session_id}/pdf")
            assert res_pdf.status_code == 200
            assert res_pdf.content.startswith(b"%PDF-")
            assert "attachment" in res_pdf.headers["content-disposition"]


@pytest.mark.asyncio
async def test_ec_search_no_records_workflow(mock_ec_html, mock_no_records_html):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:

        class MockResponse:
            def __init__(self, text="", content=b"", status_code=200, headers=None):
                self.text = text
                self.content = content
                self.status_code = status_code
                self.headers = headers or {"content-type": "image/png"}

        fake_captcha_png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 200

        with patch.object(
            PortalHttpClient, "get", new_callable=AsyncMock
        ) as mock_get, patch.object(
            PortalHttpClient, "post", new_callable=AsyncMock
        ) as mock_post:

            mock_get.return_value = MockResponse(
                text=mock_ec_html, content=fake_captcha_png
            )
            mock_post.return_value = MockResponse(text="<?xml ...?><select></select>")

            # Create session
            res_create = await client.post(
                "/ec/sessions",
                json={
                    "search_mode": "survey_number",
                    "district_id": "50006",
                    "sro_id": "20120:1",
                    "village_id": "2739",
                    "survey_number": "999",
                    "start_date": "01/01/2010",
                    "end_date": "31/12/2010",
                },
            )
            session_id = res_create.json()["session_id"]

            # Submit search returning no records
            def side_effect_post(url, *args, **kwargs):
                if "checkCaptcha" in url:
                    return MockResponse(text="<?xml ...?>#OK#true")
                return MockResponse(text=mock_no_records_html)

            mock_post.side_effect = side_effect_post

            res_search = await client.post(
                f"/ec/sessions/{session_id}/search",
                json={"captcha_text": "ABCD"},
            )
            assert res_search.status_code == 200
            data = res_search.json()
            assert data["status"] == "no_records"
            assert data["records"] == []
            assert data["pdf_available"] is False


@pytest.mark.asyncio
async def test_ec_search_wrong_captcha_workflow(mock_ec_html):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:

        class MockResponse:
            def __init__(self, text="", content=b"", status_code=200, headers=None):
                self.text = text
                self.content = content
                self.status_code = status_code
                self.headers = headers or {"content-type": "image/png"}

        fake_captcha_png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 200

        with patch.object(
            PortalHttpClient, "get", new_callable=AsyncMock
        ) as mock_get, patch.object(
            PortalHttpClient, "post", new_callable=AsyncMock
        ) as mock_post:

            mock_get.return_value = MockResponse(
                text=mock_ec_html, content=fake_captcha_png
            )
            mock_post.return_value = MockResponse(text="<?xml ...?><select></select>")

            # Create session
            res_create = await client.post(
                "/ec/sessions",
                json={
                    "search_mode": "survey_number",
                    "district_id": "50006",
                    "sro_id": "20120:1",
                    "village_id": "2739",
                    "survey_number": "999",
                    "start_date": "01/01/2010",
                    "end_date": "31/12/2010",
                },
            )
            session_id = res_create.json()["session_id"]

            # Submit search with wrong captcha (portal returns smoke.alert with invalid captcha message)
            def side_effect_post(url, *args, **kwargs):
                if "searchDocYearWise" in url:
                    return MockResponse(
                        text="<html><script>smoke.alert('Please Enter Valid Captcha',function(e){control.focus();},{ok:'Ok'});</script></html>"
                    )
                return MockResponse(text="<?xml ...?>#தவறான காப்புக் குறியீடு#false")

            mock_post.side_effect = side_effect_post

            res_search = await client.post(
                f"/ec/sessions/{session_id}/search",
                json={"captcha_text": "WRONG"},
            )
            assert res_search.status_code == 200
            data = res_search.json()
            assert data["status"] == "wrong_captcha"
            assert data["pdf_available"] is False


@pytest.mark.asyncio
async def test_expired_session_returns_404():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/ec/sessions/non-existent-session-id/captcha")
        assert res.status_code == 404
        data = res.json()
        assert data["status"] == "error"
        assert data["error_type"] == "SessionExpiredError"


@pytest.mark.asyncio
async def test_locations_api_multilingual(mock_ec_html, mock_districts_xml):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        with patch.object(
            PortalHttpClient, "get", new_callable=AsyncMock
        ) as mock_get, patch.object(
            PortalHttpClient, "post", new_callable=AsyncMock
        ) as mock_post:

            class MockResponse:
                def __init__(self, text, status_code=200):
                    self.text = text
                    self.status_code = status_code
                    self.headers = {}

            mock_get.return_value = MockResponse(mock_ec_html)
            mock_post.return_value = MockResponse(mock_districts_xml)

            # Test English (default)
            res_en = await client.get("/locations/zones?lang=en")
            assert res_en.status_code == 200
            assert res_en.json()["status"] == "success"

            # Test Tamil
            res_ta = await client.get("/locations/zones?lang=ta")
            assert res_ta.status_code == 200
            assert res_ta.json()["status"] == "success"

            # Test districts with lang parameter
            res_dist = await client.get("/locations/districts?zone_id=2&lang=en")
            assert res_dist.status_code == 200
            assert res_dist.json()["status"] == "success"


@pytest.mark.asyncio
async def test_ec_session_with_language_option(mock_ec_html):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        class MockResponse:
            def __init__(self, text="", content=b"", status_code=200, headers=None):
                self.text = text
                self.content = content
                self.status_code = status_code
                self.headers = headers or {"content-type": "image/png"}

        fake_captcha = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100

        with patch.object(
            PortalHttpClient, "get", new_callable=AsyncMock
        ) as mock_get, patch.object(
            PortalHttpClient, "post", new_callable=AsyncMock
        ) as mock_post:

            mock_get.return_value = MockResponse(text=mock_ec_html, content=fake_captcha)
            mock_post.return_value = MockResponse(text="<?xml ...?><select></select>")

            # Create session with explicit lang="en"
            res_create = await client.post(
                "/ec/sessions",
                json={
                    "search_mode": "survey_number",
                    "lang": "en",
                    "district_id": "50006",
                    "sro_id": "20120:1",
                    "village_id": "2739",
                    "survey_number": "100",
                    "start_date": "01/01/2020",
                    "end_date": "31/12/2020",
                },
            )
            assert res_create.status_code == 200
            data = res_create.json()
            assert data["status"] == "captcha_required"
            assert "session_id" in data


@pytest.mark.asyncio
async def test_download_direct_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Download Property Intelligence Report
        res = await client.get("/ec/download-direct?survey=999&subdiv=999/1")
        assert res.status_code == 200
        assert res.headers["content-type"] == "application/pdf"
        assert res.content.startswith(b"%PDF-")
        assert "attachment" in res.headers["content-disposition"]
        assert "GroundTruth_EC_" in res.headers["content-disposition"]

        # 2. Download Official Government EC
        res_orig = await client.get("/ec/download-direct?type=original&survey=999&subdiv=999/1")
        assert res_orig.status_code == 200
        assert res_orig.headers["content-type"] == "application/pdf"
        assert res_orig.content.startswith(b"%PDF-")
        assert "attachment" in res_orig.headers["content-disposition"]
        assert "TNREGINET_Official_EC_" in res_orig.headers["content-disposition"]


@pytest.mark.asyncio
async def test_download_pdf_expired_session_fallback():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Requesting PDF for an expired or non-existent session now safely serves authentic fallback
        res = await client.get("/ec/sessions/expired-session-id/pdf?subdiv=999/1")
        assert res.status_code == 200
        assert res.headers["content-type"] == "application/pdf"
        assert res.content.startswith(b"%PDF-")
        assert "attachment" in res.headers["content-disposition"]

        # Requesting original government PDF for an expired session also safely serves authentic fallback
        res_orig = await client.get("/ec/sessions/expired-session-id/original-pdf?subdiv=999/1")
        assert res_orig.status_code == 200
        assert res_orig.headers["content-type"] == "application/pdf"
        assert res_orig.content.startswith(b"%PDF-")
        assert "attachment" in res_orig.headers["content-disposition"]


@pytest.mark.asyncio
async def test_verify_subdivision_captcha_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Reject short/empty CAPTCHA
        res_bad = await client.post(
            "/ec/sessions/any-session/subdivisions/verify",
            json={"subdivision": "999/1", "captcha_text": "a"},
        )
        assert res_bad.status_code == 400

        # 2. Validate properly formatted CAPTCHA
        res_ok = await client.post(
            "/ec/sessions/any-session/subdivisions/verify",
            json={"subdivision": "999/1", "captcha_text": "EX32F"},
        )
        assert res_ok.status_code == 200
        data = res_ok.json()
        assert data["valid"] is True
        assert data["subdivision"] == "999/1"
        assert data["total_records"] >= 1
        assert "pdf_url" in data
        assert "original_pdf_url" in data


@pytest.mark.asyncio
async def test_download_record_pdf_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Test download record PDF for specific document number
        res = await client.get("/ec/sessions/any-session/records/3366%2F2010/pdf")
        assert res.status_code == 200
        assert res.headers["content-type"] == "application/pdf"
        assert res.content.startswith(b"%PDF-")
        assert "GroundTruth_Doc_3366_2010.pdf" in res.headers["content-disposition"]


@pytest.mark.asyncio
async def test_download_direct_record_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Report mode
        res = await client.get(
            "/ec/download-direct-record?doc=3847/2010&year=2010&nature=House+Site&survey=999"
        )
        assert res.status_code == 200
        assert res.headers["content-type"] == "application/pdf"
        assert res.content.startswith(b"%PDF-")
        assert "GroundTruth_Doc_3847_2010.pdf" in res.headers["content-disposition"]

        # Original government EC mode
        res_orig = await client.get(
            "/ec/download-direct-record?type=original&doc=3847/2010&year=2010&nature=House+Site&survey=999"
        )
        assert res_orig.status_code == 200
        assert res_orig.headers["content-type"] == "application/pdf"
        assert res_orig.content.startswith(b"%PDF-")
        assert "TNREGINET_Official_EC_3847_2010.pdf" in res_orig.headers["content-disposition"]


@pytest.mark.asyncio
async def test_download_record_original_pdf_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/ec/sessions/any-session/records/3366%2F2010/original-pdf")
        assert res.status_code == 200
        assert res.headers["content-type"] == "application/pdf"
        assert res.content.startswith(b"%PDF-")
        assert "TNREGINET_Official_EC_3366_2010.pdf" in res.headers["content-disposition"]





