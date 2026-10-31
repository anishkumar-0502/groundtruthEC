"""Location discovery API endpoints with multilingual support (English default)."""

from fastapi import APIRouter, Query
from app.schemas.locations import LocationListResponse
from app.services.location_service import location_service

router = APIRouter(prefix="/locations", tags=["Locations"])


@router.get("/zones", response_model=LocationListResponse)
async def list_zones(
    lang: str = Query("en", description="Language code: 'en' for English (default), 'ta' for Tamil")
):
    """Retrieve all available registration zones dynamically from the portal in selected language."""
    return await location_service.get_zones(lang=lang)


@router.get("/districts", response_model=LocationListResponse)
async def list_districts(
    zone_id: str = Query(..., description="Parent Zone identifier (e.g., '2' for Coimbatore)"),
    lang: str = Query("en", description="Language code: 'en' for English (default), 'ta' for Tamil")
):
    """Retrieve all districts under the specified zone in selected language."""
    return await location_service.get_districts(zone_id=zone_id, lang=lang)


@router.get("/sros", response_model=LocationListResponse)
async def list_sros(
    district_id: str = Query(..., description="Parent District identifier (e.g., '50006' for Coimbatore South)"),
    lang: str = Query("en", description="Language code: 'en' for English (default), 'ta' for Tamil")
):
    """Retrieve all Sub-Registrar Offices (SROs) under the specified district in selected language."""
    return await location_service.get_sros(district_id=district_id, lang=lang)


@router.get("/villages", response_model=LocationListResponse)
async def list_villages(
    sro_id: str = Query(..., description="Parent SRO identifier (e.g., '20120:1' for Madukkarai)"),
    lang: str = Query("en", description="Language code: 'en' for English (default), 'ta' for Tamil")
):
    """Retrieve all villages under the specified SRO in selected language."""
    return await location_service.get_villages(sro_id=sro_id, lang=lang)


@router.get("/towns", response_model=LocationListResponse)
async def list_towns(
    village_id: str = Query(..., description="Village identifier"),
    lang: str = Query("en", description="Language code: 'en' for English (default), 'ta' for Tamil")
):
    """Retrieve revenue towns mapped to a village for ward/block search in selected language."""
    return await location_service.get_towns(village_id=village_id, lang=lang)


@router.get("/wards", response_model=LocationListResponse)
async def list_wards(
    village_id: str = Query(..., description="Village identifier"),
    town_code: str = Query(..., description="Town code"),
    lang: str = Query("en", description="Language code: 'en' for English (default), 'ta' for Tamil")
):
    """Retrieve wards under the specified town in selected language."""
    return await location_service.get_wards(village_id=village_id, town_code=town_code, lang=lang)


@router.get("/blocks", response_model=LocationListResponse)
async def list_blocks(
    village_id: str = Query(..., description="Village identifier"),
    town_code: str = Query(..., description="Town code"),
    ward_code: str = Query(..., description="Ward code"),
    lang: str = Query("en", description="Language code: 'en' for English (default), 'ta' for Tamil")
):
    """Retrieve blocks under the specified ward in selected language."""
    return await location_service.get_blocks(
        village_id=village_id,
        town_code=town_code,
        ward_code=ward_code,
        lang=lang,
    )
