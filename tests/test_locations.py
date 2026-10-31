"""Tests for location retrieval, XML/HTML parsing, and Tamil text preservation."""

from pathlib import Path
import pytest
from app.portal.locations import parse_select_options
from app.services.location_service import LocationService

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_parse_zones_preserves_tamil_and_filters_placeholders():
    html = (FIXTURES_DIR / "ec_page.html").read_text(encoding="utf-8")
    zones = parse_select_options(html, select_id_or_name="cmb_Zone")

    assert len(zones) == 3
    # Check that -1 was filtered out
    assert not any(z.id == "-1" for z in zones)
    assert not any("தெரிவு" in z.name for z in zones)

    # Check that Tamil text is preserved intact
    zone_dict = {z.id: z.name for z in zones}
    assert "2" in zone_dict
    assert zone_dict["2"] == "கோயம்புத்தூர்"
    assert "1" in zone_dict
    assert zone_dict["1"] == "சென்னை"
    assert "4" in zone_dict
    assert zone_dict["4"] == "மதுரை"


def test_parse_districts_xml():
    xml = (FIXTURES_DIR / "districts.xml").read_text(encoding="utf-8")
    districts = parse_select_options(xml, select_id_or_name="cmb_District")

    assert len(districts) == 2
    d_dict = {d.id: d.name for d in districts}
    assert d_dict["50006"] == "கோயம்புத்தூர் தெற்கு"
    assert d_dict["20006"] == "கோயம்புத்தூர் வடக்கு"


def test_parse_sros_xml():
    xml = (FIXTURES_DIR / "sros.xml").read_text(encoding="utf-8")
    sros = parse_select_options(xml, select_id_or_name="cmb_SroName")

    assert len(sros) == 3
    sro_dict = {s.id: s.name for s in sros}
    assert sro_dict["20120:1"] == "மதுக்கரை"
    assert sro_dict["20117:1"] == "சிங்காநல்லூர்"


def test_parse_villages_xml():
    xml = (FIXTURES_DIR / "villages.xml").read_text(encoding="utf-8")
    villages = parse_select_options(xml, select_id_or_name="cmb_Village")

    assert len(villages) == 3
    v_dict = {v.id: v.name for v in villages}
    assert v_dict["2739"] == "மதுக்கரை"
    assert v_dict["2740"] == "எட்டிமடை"


def test_parse_select_options_english():
    sample_html = """
    <select id="cmb_Zone">
        <option value="-1">--Select--</option>
        <option value="1">Chennai</option>
        <option value="2">Coimbatore</option>
        <option value="3">Madurai</option>
    </select>
    """
    zones = parse_select_options(sample_html, select_id_or_name="cmb_Zone")
    assert len(zones) == 3
    assert not any(z.id == "-1" for z in zones)
    assert not any("Select" in z.name for z in zones)
    zone_dict = {z.id: z.name for z in zones}
    assert zone_dict["1"] == "Chennai"
    assert zone_dict["2"] == "Coimbatore"
    assert zone_dict["3"] == "Madurai"


def test_parse_select_options_multilingual_translation():
    sample_html = """
    <select id="cmb_Zone">
        <option value="-1">--Select--</option>
        <option value="1">சென்னை</option>
        <option value="2">கோயம்புத்தூர்</option>
        <option value="4">மதுரை</option>
    </select>
    """
    # In English mode, Tamil zone names must translate to English
    zones_en = parse_select_options(sample_html, select_id_or_name="cmb_Zone", lang="en")
    dict_en = {z.id: z.name for z in zones_en}
    assert dict_en["1"] == "Chennai"
    assert dict_en["2"] == "Coimbatore"
    assert dict_en["4"] == "Madurai"

    # In Tamil mode, Tamil zone names must remain native Tamil
    zones_ta = parse_select_options(sample_html, select_id_or_name="cmb_Zone", lang="ta")
    dict_ta = {z.id: z.name for z in zones_ta}
    assert dict_ta["1"] == "சென்னை"
    assert dict_ta["2"] == "கோயம்புத்தூர்"
    assert dict_ta["4"] == "மதுரை"


@pytest.mark.asyncio
async def test_location_service_cache_isolation_by_language():
    from unittest.mock import AsyncMock, patch
    from app.schemas.locations import LocationItem

    service = LocationService(cache_ttl_seconds=3600)

    # Mock _ensure_client
    mock_client = AsyncMock()

    with patch.object(service, "_ensure_client", new_callable=AsyncMock) as mock_ensure:
        mock_ensure.return_value = (mock_client, "fake-csrf")

        # Mock fetch_districts to return different names depending on lang
        async def mock_fetch_dist(client, zone_id, csrf_token, lang="en"):
            if lang == "en":
                return [LocationItem(id="50006", name="Coimbatore South")]
            return [LocationItem(id="50006", name="கோயம்புத்தூர் தெற்கு")]

        with patch("app.services.location_service.fetch_districts", side_effect=mock_fetch_dist):
            res_en = await service.get_districts(zone_id="2", lang="en")
            assert res_en.data[0].name == "Coimbatore South"

            res_ta = await service.get_districts(zone_id="2", lang="ta")
            assert res_ta.data[0].name == "கோயம்புத்தூர் தெற்கு"

            # Both should be cached separately
            assert "2:en" in service._districts_cache
            assert "2:ta" in service._districts_cache
            assert service._districts_cache["2:en"][1][0].name == "Coimbatore South"
            assert service._districts_cache["2:ta"][1][0].name == "கோயம்புத்தூர் தெற்கு"


