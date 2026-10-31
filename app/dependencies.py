"""FastAPI dependencies and service singletons."""

from app.services.ec_service import ec_service
from app.services.location_service import location_service


def get_location_service():
    """Dependency provider for LocationService."""
    return location_service


def get_ec_service():
    """Dependency provider for ECService."""
    return ec_service

