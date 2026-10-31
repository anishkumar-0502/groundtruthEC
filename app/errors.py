"""Domain exceptions and API error representations."""

from typing import Any, Dict, Optional
from fastapi import Request, status
from fastapi.responses import JSONResponse


class GroundTruthError(Exception):
    """Base exception for Ground Truth service."""

    def __init__(self, message: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}


class PortalError(GroundTruthError):
    """Raised when portal responds unexpectedly, errors out, or is unreachable."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, status_code=status.HTTP_502_BAD_GATEWAY, details=details)


class SessionExpiredError(GroundTruthError):
    """Raised when application session or portal session is expired."""

    def __init__(self, message: str = "Session has expired or is invalid"):
        super().__init__(message=message, status_code=status.HTTP_404_NOT_FOUND)


class WrongCaptchaError(GroundTruthError):
    """Raised when submitted CAPTCHA fails portal verification."""

    def __init__(self, message: str = "Invalid CAPTCHA entered. Please try again."):
        super().__init__(message=message, status_code=status.HTTP_400_BAD_REQUEST)


class TooManyRecordsError(GroundTruthError):
    """Raised when query exceeds supported result limit."""

    def __init__(self, message: str = "Query returned too many records. Please narrow date or survey range."):
        super().__init__(message=message, status_code=status.HTTP_400_BAD_REQUEST)


class PdfUnavailableError(GroundTruthError):
    """Raised when an EC PDF cannot be retrieved or was not generated."""

    def __init__(self, message: str = "Original EC PDF is unavailable for this search"):
        super().__init__(message=message, status_code=status.HTTP_404_NOT_FOUND)


async def ground_truth_error_handler(request: Request, exc: GroundTruthError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "error_type": exc.__class__.__name__,
            "message": exc.message,
            "details": exc.details,
        },
    )

