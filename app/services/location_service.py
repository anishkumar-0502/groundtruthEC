"""Location service for dynamic retrieval and in-memory caching with multilingual support."""

import asyncio
from datetime import datetime, timedelta, timezone
import logging
from typing import Dict, List, Optional, Tuple

from app.errors import PortalError
from app.portal.client import PortalHttpClient
from app.portal.locations import (
    fetch_blocks,
    fetch_districts,
    fetch_initial_page_and_zones,
    fetch_sros,
    fetch_towns,
    fetch_villages,
    fetch_wards,
)
from app.schemas.locations import LocationItem, LocationListResponse

logger = logging.getLogger("ground_truth.location_service")


class LocationService:
    """Provides cached and dynamic location lookups against TNREGINET in English (default) or Tamil."""

    def __init__(self, cache_ttl_seconds: int = 3600):
        self.cache_ttl = timedelta(seconds=cache_ttl_seconds)
        self._lock = asyncio.Lock()
        self._clients: Dict[str, PortalHttpClient] = {}
        self._csrf_tokens: Dict[str, str] = {}
        self._auth_tokens: Dict[str, str] = {}
        self._session_created_at: Dict[str, datetime] = {}

        # In-memory location caches keyed by: key:lang -> (timestamp, data)
        self._zones_cache: Dict[str, Tuple[datetime, List[LocationItem]]] = {}
        self._districts_cache: Dict[str, Tuple[datetime, List[LocationItem]]] = {}
        self._sros_cache: Dict[str, Tuple[datetime, List[LocationItem]]] = {}
        self._villages_cache: Dict[str, Tuple[datetime, List[LocationItem]]] = {}
        self._towns_cache: Dict[str, Tuple[datetime, List[LocationItem]]] = {}
        self._wards_cache: Dict[str, Tuple[datetime, List[LocationItem]]] = {}
        self._blocks_cache: Dict[str, Tuple[datetime, List[LocationItem]]] = {}

    async def _ensure_client(self, lang: str = "en") -> Tuple[PortalHttpClient, str]:
        """Ensure an active portal client with fresh CSRF token for the specified language."""
        now = datetime.now(timezone.utc)
        lang_client = self._clients.get(lang)
        created_at = self._session_created_at.get(lang)

        if not lang_client or not created_at or (now - created_at) > timedelta(minutes=15):
            if lang_client:
                await lang_client.close()
            new_client = PortalHttpClient()
            try:
                csrf, auth, zones = await fetch_initial_page_and_zones(new_client, lang=lang)
                self._clients[lang] = new_client
                self._csrf_tokens[lang] = csrf
                self._auth_tokens[lang] = auth
                self._session_created_at[lang] = now
                if zones:
                    self._zones_cache[lang] = (now, zones)
            except Exception as exc:
                logger.error(f"Failed to initialize location client session for lang={lang}: {exc}")
                raise PortalError(f"Could not connect to portal to initialize location metadata: {exc}") from exc

        return self._clients[lang], self._csrf_tokens.get(lang, "")

    async def get_zones(self, lang: str = "en") -> LocationListResponse:
        """Retrieve all zones (cached if fresh), default English."""
        async with self._lock:
            now = datetime.now(timezone.utc)
            if lang in self._zones_cache:
                cached_time, data = self._zones_cache[lang]
                if (now - cached_time) < self.cache_ttl:
                    return LocationListResponse(status="success", data=data)

            client, _ = await self._ensure_client(lang=lang)
            if lang in self._zones_cache:
                return LocationListResponse(status="success", data=self._zones_cache[lang][1])

            _, _, zones = await fetch_initial_page_and_zones(client, lang=lang)
            self._zones_cache[lang] = (now, zones)
            return LocationListResponse(status="success", data=zones)

    async def get_districts(self, zone_id: str, lang: str = "en") -> LocationListResponse:
        """Retrieve districts for a zone in specified language."""
        key = f"{zone_id}:{lang}"
        async with self._lock:
            now = datetime.now(timezone.utc)
            if key in self._districts_cache:
                cached_time, data = self._districts_cache[key]
                if (now - cached_time) < self.cache_ttl:
                    return LocationListResponse(status="success", data=data)

            client, csrf = await self._ensure_client(lang=lang)
            districts = await fetch_districts(client, zone_id=zone_id, csrf_token=csrf, lang=lang)
            self._districts_cache[key] = (now, districts)
            return LocationListResponse(status="success", data=districts)

    async def get_sros(self, district_id: str, lang: str = "en") -> LocationListResponse:
        """Retrieve SROs for a district in specified language."""
        key = f"{district_id}:{lang}"
        async with self._lock:
            now = datetime.now(timezone.utc)
            if key in self._sros_cache:
                cached_time, data = self._sros_cache[key]
                if (now - cached_time) < self.cache_ttl:
                    return LocationListResponse(status="success", data=data)

            client, csrf = await self._ensure_client(lang=lang)
            sros = await fetch_sros(client, district_id=district_id, csrf_token=csrf, lang=lang)
            self._sros_cache[key] = (now, sros)
            return LocationListResponse(status="success", data=sros)

    async def get_villages(self, sro_id: str, lang: str = "en") -> LocationListResponse:
        """Retrieve villages for an SRO in specified language."""
        key = f"{sro_id}:{lang}"
        async with self._lock:
            now = datetime.now(timezone.utc)
            if key in self._villages_cache:
                cached_time, data = self._villages_cache[key]
                if (now - cached_time) < self.cache_ttl:
                    return LocationListResponse(status="success", data=data)

            client, csrf = await self._ensure_client(lang=lang)
            villages = await fetch_villages(client, sro_id=sro_id, csrf_token=csrf, lang=lang)
            self._villages_cache[key] = (now, villages)
            return LocationListResponse(status="success", data=villages)

    async def get_towns(self, village_id: str, lang: str = "en") -> LocationListResponse:
        """Retrieve towns mapped to a village in specified language."""
        key = f"{village_id}:{lang}"
        async with self._lock:
            now = datetime.now(timezone.utc)
            if key in self._towns_cache:
                cached_time, data = self._towns_cache[key]
                if (now - cached_time) < self.cache_ttl:
                    return LocationListResponse(status="success", data=data)

            client, csrf = await self._ensure_client(lang=lang)
            towns = await fetch_towns(client, village_id=village_id, csrf_token=csrf, lang=lang)
            self._towns_cache[key] = (now, towns)
            return LocationListResponse(status="success", data=towns)

    async def get_wards(self, village_id: str, town_code: str, lang: str = "en") -> LocationListResponse:
        """Retrieve wards for a town in specified language."""
        key = f"{village_id}:{town_code}:{lang}"
        async with self._lock:
            now = datetime.now(timezone.utc)
            if key in self._wards_cache:
                cached_time, data = self._wards_cache[key]
                if (now - cached_time) < self.cache_ttl:
                    return LocationListResponse(status="success", data=data)

            client, csrf = await self._ensure_client(lang=lang)
            wards = await fetch_wards(client, village_id=village_id, town_code=town_code, csrf_token=csrf, lang=lang)
            self._wards_cache[key] = (now, wards)
            return LocationListResponse(status="success", data=wards)

    async def get_blocks(self, village_id: str, town_code: str, ward_code: str, lang: str = "en") -> LocationListResponse:
        """Retrieve blocks for a ward in specified language."""
        key = f"{village_id}:{town_code}:{ward_code}:{lang}"
        async with self._lock:
            now = datetime.now(timezone.utc)
            if key in self._blocks_cache:
                cached_time, data = self._blocks_cache[key]
                if (now - cached_time) < self.cache_ttl:
                    return LocationListResponse(status="success", data=data)

            client, csrf = await self._ensure_client(lang=lang)
            blocks = await fetch_blocks(
                client,
                village_id=village_id,
                town_code=town_code,
                ward_code=ward_code,
                csrf_token=csrf,
                lang=lang,
            )
            self._blocks_cache[key] = (now, blocks)
            return LocationListResponse(status="success", data=blocks)

    async def close(self) -> None:
        """Shutdown all active language clients."""
        for client in self._clients.values():
            try:
                await client.close()
            except Exception:
                pass
        self._clients.clear()


location_service = LocationService()
