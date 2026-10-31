"""Pydantic schemas for location endpoints."""

from typing import List
from pydantic import BaseModel, Field


class LocationItem(BaseModel):
    """Represents a single location option with portal identifier and name."""

    id: str = Field(..., description="Actual portal identifier for this location level")
    name: str = Field(..., description="Display name of the location preserving Tamil and English script")


class LocationListResponse(BaseModel):
    """Standardized response format for location lookups."""

    status: str = Field(default="success", description="Response status (e.g., success)")
    data: List[LocationItem] = Field(default_factory=list, description="List of available location items")

