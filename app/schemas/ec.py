"""Pydantic schemas for EC search, sessions, records, and responses."""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
import re
from typing import Any, List, Literal, Optional
from pydantic import BaseModel, Field, model_validator


class SearchMode(str, Enum):
    SURVEY_NUMBER = "survey_number"
    WARD_BLOCK = "ward_block"


class ECStatus(str, Enum):
    FOUND = "found"
    NO_RECORDS = "no_records"
    WRONG_CAPTCHA = "wrong_captcha"
    SESSION_EXPIRED = "session_expired"
    TOO_MANY_RECORDS = "too_many_records"
    PORTAL_ERROR = "portal_error"


def parse_and_validate_date(date_str: str) -> str:
    """Validate date and normalize to portal's required DD/MM/YYYY format."""
    date_str = date_str.strip()

    # Try DD/MM/YYYY
    m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})$", date_str)
    if m:
        day, month, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
        try:
            d = date(year, month, day)
            return f"{d.day:02d}/{d.month:02d}/{d.year:04d}"
        except ValueError as exc:
            raise ValueError(f"'{date_str}' is not a valid calendar date: {exc}")

    # Try YYYY-MM-DD
    m_iso = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})$", date_str)
    if m_iso:
        year, month, day = int(m_iso.group(1)), int(m_iso.group(2)), int(m_iso.group(3))
        try:
            d = date(year, month, day)
            return f"{d.day:02d}/{d.month:02d}/{d.year:04d}"
        except ValueError as exc:
            raise ValueError(f"'{date_str}' is not a valid calendar date: {exc}")

    # Try DD-MMM-YYYY (e.g. 01-Jan-2010)
    for fmt in ("%d-%b-%Y", "%d-%B-%Y", "%d-%m-%Y"):
        try:
            dt = datetime.strptime(date_str, fmt).date()
            return f"{dt.day:02d}/{dt.month:02d}/{dt.year:04d}"
        except ValueError:
            pass

    raise ValueError(f"Invalid date format '{date_str}'. Expected DD/MM/YYYY or YYYY-MM-DD.")


class CreateSessionRequest(BaseModel):
    """Payload to start a search session on TNREGINET."""

    search_mode: SearchMode = Field(..., description="Search mode: 'survey_number' or 'ward_block'")

    # Common location fields
    lang: str = Field(default="en", description="Portal language: 'en' for English (default), 'ta' for Tamil")
    zone_id: Optional[str] = Field(None, description="Zone identifier (e.g., '2' for Coimbatore)")
    district_id: str = Field(..., description="District identifier (e.g., '50006' for Coimbatore South)")
    sro_id: str = Field(..., description="SRO identifier (e.g., '20120:1' for Madukkarai)")
    sro_name: Optional[str] = Field(None, description="Human-readable SRO text name (e.g. 'Madukkarai')")
    village_id: str = Field(..., description="Village identifier (e.g., '2739' for Madukkarai)")

    # Date range fields
    start_date: str = Field(..., description="Start date in DD/MM/YYYY or YYYY-MM-DD format")
    end_date: str = Field(..., description="End date in DD/MM/YYYY or YYYY-MM-DD format")

    # Mode A: Survey Number fields
    survey_number: Optional[str] = Field(None, description="Mandatory for survey_number mode (e.g. '999')")
    subdivision_number: Optional[str] = Field(None, description="Optional subdivision number")

    # Mode B: Town Ward/Block fields
    town_code: Optional[str] = Field(None, description="Mandatory for ward_block mode")
    ward_code: Optional[str] = Field(None, description="Mandatory for ward_block mode")
    block_code: Optional[str] = Field(None, description="Mandatory for ward_block mode")

    @model_validator(mode="after")
    def validate_search_inputs(self) -> "CreateSessionRequest":
        # Validate dates
        norm_start = parse_and_validate_date(self.start_date)
        norm_end = parse_and_validate_date(self.end_date)

        d_start = datetime.strptime(norm_start, "%d/%m/%Y").date()
        d_end = datetime.strptime(norm_end, "%d/%m/%Y").date()

        if d_start > d_end:
            raise ValueError(f"Start date ({norm_start}) cannot be later than end date ({norm_end})")

        if d_start.year < 1900 or d_end.year < 1900:
            raise ValueError("Registration department search years must be 1900 or later")

        from datetime import date
        today = date.today()
        if d_end > today:
            raise ValueError(f"End date ({norm_end}) cannot be in the future. Today is {today.strftime('%d/%m/%Y')}.")

        if self.sro_id and self.sro_id.endswith(":0"):
            raise ValueError("The selected Sub-Registrar Office is marked as Closed by TNREGINET. Please select an active office.")

        self.start_date = norm_start
        self.end_date = norm_end

        # Mode specific validations
        if self.search_mode == SearchMode.SURVEY_NUMBER:
            if not self.survey_number or not self.survey_number.strip():
                raise ValueError("survey_number is required for 'survey_number' search mode")
        elif self.search_mode == SearchMode.WARD_BLOCK:
            if not self.ward_code or not self.ward_code.strip():
                raise ValueError("ward_code is required for 'ward_block' search mode")
            if not self.block_code or not self.block_code.strip():
                raise ValueError("block_code is required for 'ward_block' search mode")

        return self


class SessionCreatedResponse(BaseModel):
    """Response returned when an EC search session is initialized."""

    status: Literal["captcha_required"] = "captcha_required"
    session_id: str = Field(..., description="Cryptographically random application session ID")
    captcha_image_url: str = Field(..., description="URL to retrieve real CAPTCHA image")
    captcha_data_url: Optional[str] = Field(None, description="Base64 Data URI of the CAPTCHA image for instant rendering")
    expires_at: str = Field(..., description="Session expiration ISO-8601 timestamp")


class SubmitSearchRequest(BaseModel):
    """Request payload containing human-solved CAPTCHA text."""

    captcha_text: str = Field(..., min_length=1, max_length=20, description="CAPTCHA string entered by a human")


class ECRecord(BaseModel):
    """Single Encumbrance Certificate document entry parsed from portal results."""

    document_number: str = Field(..., description="Document registration number")
    document_year: Optional[int] = Field(None, description="Document registration year")
    registration_date: Optional[str] = Field(None, description="Date of document registration")
    document_type: Optional[str] = Field(None, description="Nature / type of transaction (e.g. Sale Deed, Mortgage)")
    executants: List[str] = Field(default_factory=list, description="List of parties who executed the document")
    claimants: List[str] = Field(default_factory=list, description="List of claimants / beneficiaries")
    consideration_value: Optional[Decimal] = Field(None, description="Consideration amount in INR")
    market_value: Optional[Decimal] = Field(None, description="Guideline / market value in INR")
    survey_numbers: List[str] = Field(default_factory=list, description="Survey / subdivision numbers involved")


class VerifySubdivisionRequest(BaseModel):
    """Payload to verify CAPTCHA for a specific subdivision download."""

    subdivision: str = Field(..., description="Subdivision identifier (e.g. '999/1')")
    captcha_text: str = Field(..., description="Human-entered CAPTCHA characters")


class VerifySubdivisionResponse(BaseModel):
    """Result of subdivision CAPTCHA verification and record matching."""

    valid: bool = Field(..., description="Whether the CAPTCHA was verified")
    subdivision: str = Field(..., description="Subdivision identifier")
    total_records: int = Field(..., description="Count of transaction records found for this subdivision")
    records: List[ECRecord] = Field(default_factory=list, description="Matching transaction records")
    pdf_url: str = Field(..., description="Download URL for Ground Truth Intelligence Report")
    original_pdf_url: str = Field(..., description="Download URL for Official Government EC")


class ECSearchResponse(BaseModel):
    """Stable JSON schema returned for all EC search outcomes."""

    status: ECStatus = Field(..., description="Outcome status of the search operation")
    records: List[ECRecord] = Field(default_factory=list, description="List of parsed EC records if status is 'found'")
    total_records: int = Field(default=0, description="Count of parsed records")
    message: Optional[str] = Field(None, description="Human-readable explanation of status or error")
    error_code: Optional[str] = Field(None, description="Stable machine-readable error code")
    correlation_id: Optional[str] = Field(None, description="Unique correlation / request ID for traceability")
    pdf_available: bool = Field(default=False, description="Whether an original EC PDF is available for download")
    pdf_url: Optional[str] = Field(None, description="Endpoint to download original binary EC PDF if available")
    original_pdf_url: Optional[str] = Field(None, description="Endpoint to download Official Government EC PDF")
    discovered_subdivisions: List[str] = Field(
        default_factory=list,
        description="List of distinct subdivision numbers discovered across the search records",
    )

