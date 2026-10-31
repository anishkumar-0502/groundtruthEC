"""HTML parser for TNREGINET EC search results and status classification."""

from decimal import Decimal, InvalidOperation
import logging
import re
from typing import Any, Dict, List, Optional, Tuple
from bs4 import BeautifulSoup

from app.schemas.ec import ECRecord, ECStatus

logger = logging.getLogger("ground_truth.parser")

# Exact observed phrases from TNREGINET portal
NO_RECORDS_PHRASES = [
    "தேடுதல் காலத்தில் எந்த ஆவணங்களும் பதிவு செய்யப்படவில்லை",
    "எந்த ஆவணங்களும் பதிவு செய்யப்படவில்லை",
    "no documents registered during the search period",
    "no documents registered",
    "no document registered",
    "no records found",
    "no record found",
    "records not found",
]

WRONG_CAPTCHA_PHRASES = [
    "சரியான காப்புக் குறியீட்டினை உள்ளிடவும்",
    "தயவுசெய்து சரியான காப்புக் குறியீட்டினை உள்ளிடவும்",
    "தவறான காப்புக் குறியீடு",
    "please enter valid captcha",
    "enter valid captcha",
    "valid captcha",
    "invalid captcha",
    "incorrect captcha",
]

SESSION_EXPIRED_PHRASES = [
    "உங்கள் அமர்வு காலாவதியாகி விட்டது",
    "session expired",
    "session has expired",
    "your session has expired",
]

TOO_MANY_RECORDS_PHRASES = [
    "அதிகப்படியான பதிவுருக்கள்",
    "too many records",
    "exceeds maximum limit",
    "வரையறைக்கு மேற்பட்ட ஆவணங்கள்",
]


def clean_text(text: Optional[str]) -> str:
    """Clean whitespace while strictly preserving Tamil and English script."""
    if not text:
        return ""
    return " ".join(text.split())


def parse_currency(amount_str: Optional[str]) -> Optional[Decimal]:
    """Parse monetary text (e.g., '1,50,000.00' or '₹ 50000') into an exact Decimal."""
    if not amount_str:
        return None
    cleaned = re.sub(r"[^\d.]", "", amount_str.strip())
    if not cleaned or cleaned == ".":
        return None
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        logger.warning(f"Failed to parse currency Decimal from '{amount_str}'")
        return None


def parse_year(year_str: Optional[str]) -> Optional[int]:
    """Extract 4-digit year from string."""
    if not year_str:
        return None
    m = re.search(r"\b(19\d\d|20\d\d)\b", year_str)
    if m:
        try:
            return int(m.group(1))
        except ValueError:
            pass
    return None


class ECResultParser:
    """Parses TNREGINET EC result pages into structured models."""

    @staticmethod
    def classify_response(html: str) -> Tuple[ECStatus, Optional[str]]:
        """Classify the HTML response into a recognized status outcome."""
        if not html or not html.strip():
            return ECStatus.PORTAL_ERROR, "Received empty response from portal"

        soup = BeautifulSoup(html, "html.parser")
        title_text = soup.title.get_text(strip=True).lower() if soup.title else ""

        # Extract visible text without <script> and <style>
        clean_soup = BeautifulSoup(html, "html.parser")
        for tag in clean_soup(["script", "style"]):
            tag.decompose()
        page_text = clean_soup.get_text(" ", strip=True).lower()
        raw_lower = html.lower()

        # 1. Check Session Expired
        if any(phrase in page_text for phrase in SESSION_EXPIRED_PHRASES):
            return ECStatus.SESSION_EXPIRED, "Portal session has expired. Please initialize a new session."
        if "session expired" in title_text or "session expire" in title_text:
            return ECStatus.SESSION_EXPIRED, "Portal session has expired. Please initialize a new session."
        if "sessionexpire.jsp" in raw_lower and len(html.strip()) < 500:
            return ECStatus.SESSION_EXPIRED, "Portal session has expired. Please initialize a new session."

        # 2. Check Generic Portal Error
        if (
            "sorry! an error has occurred" in page_text
            or "unable to process your request due to some error" in page_text
            or (title_text == "error page" and "காலாவதியாகி" not in page_text and "session" not in page_text)
        ):
            return ECStatus.PORTAL_ERROR, "Portal encountered an internal error. Please retry after some time."

        # 3. Check Wrong Captcha
        if any(phrase in page_text for phrase in WRONG_CAPTCHA_PHRASES):
            return ECStatus.WRONG_CAPTCHA, "Invalid CAPTCHA code entered. Please try again with the new image."
        for phrase in WRONG_CAPTCHA_PHRASES:
            if (
                f"smoke.alert('{phrase}" in raw_lower
                or f'smoke.alert("{phrase}' in raw_lower
                or f"#{phrase}#" in raw_lower
            ):
                return ECStatus.WRONG_CAPTCHA, "Invalid CAPTCHA code entered. Please try again with the new image."

        # 4. Check Too Many Records
        if any(phrase in page_text for phrase in TOO_MANY_RECORDS_PHRASES):
            return ECStatus.TOO_MANY_RECORDS, "Query returned too many records. Please narrow date or survey range."

        # 5. Check Found Records
        # Look for result tables or entries in property details container (ignoring survey input table)
        prop_div = soup.find(id=re.compile(r"divPropertyList|propertyDetailSection", re.IGNORECASE))
        container = prop_div or soup
        for tbl in container.find_all("table"):
            if tbl.get("id") == "multiAddSurvey" or "multiAddSurvey" in tbl.get("class", []):
                continue
            rows = tbl.find_all("tr")
            if len(rows) > 1:
                return ECStatus.FOUND, None

        # 6. Check No Records
        div_nothing = soup.find(id=re.compile(r"divNothingFound|noRecordsDiv", re.IGNORECASE))
        if div_nothing:
            div_text = div_nothing.get_text(strip=True).lower()
            if any(p in div_text for p in NO_RECORDS_PHRASES) or "no documents" in div_text:
                return ECStatus.NO_RECORDS, "No transactions registered during the selected period"

        count_input = soup.find("input", attrs={"name": "countNoRecords"})
        if count_input and count_input.get("value") == "0":
            return ECStatus.NO_RECORDS, "No transactions registered during the selected period"

        for phrase in NO_RECORDS_PHRASES:
            if phrase in page_text:
                return ECStatus.NO_RECORDS, "No transactions registered during the selected period"

        # 7. Check Personal Details / Email Mode (When query requires applicant details for email delivery)
        if (
            "personal details" in page_text
            or "saveviewecpersonaldetails" in raw_lower
            or soup.find("input", attrs={"name": "email_citizen"})
        ):
            return (
                ECStatus.TOO_MANY_RECORDS,
                "This EC is too large for direct download — applicant details are needed before it can be emailed. Narrow the date range and try again.",
            )

        # 8. Fallback: Search form re-rendered without results or explicit error
        if soup.find("form", id="EncumbranceCertificateForm"):
            return ECStatus.PORTAL_ERROR, "Search form returned without results or error indicator"

        return ECStatus.PORTAL_ERROR, "Unrecognized portal response format"

    @classmethod
    def parse_records(cls, html: str) -> List[ECRecord]:
        """Parse structured EC records from search results HTML."""
        soup = BeautifulSoup(html, "html.parser")
        records: List[ECRecord] = []

        # Find property details container or tables
        container = soup.find(id=re.compile(r"divPropertyList|propertyDetailSection", re.IGNORECASE)) or soup
        tables = container.find_all("table")

        for table in tables:
            # Skip survey entry input table (multiAddSurvey)
            if table.get("id") == "multiAddSurvey":
                continue

            rows = table.find_all("tr")
            if len(rows) < 2:
                continue

            header_cells = [clean_text(th.get_text()) for th in rows[0].find_all(["th", "td"])]

            # Map column indices if standard headers are present
            col_map = cls._map_columns(header_cells)

            for row in rows[1:]:
                cells = row.find_all(["td", "th"])
                if not cells or len(cells) < 2:
                    continue

                cell_texts = [clean_text(td.get_text()) for td in cells]

                # Check if this row is a data row
                record = cls._extract_record_from_row(cell_texts, col_map)
                if record:
                    records.append(record)

        return records

    @staticmethod
    def _map_columns(headers: List[str]) -> Dict[str, int]:
        """Map logical field names to column indices based on English and Tamil headers."""
        mapping: Dict[str, int] = {}
        for idx, h in enumerate(headers):
            h_lower = h.lower().strip()
            if any(k in h_lower for k in ["nature", "type", "description", "ஆவண வகை", "ஆவணத்தின் தன்மை", "வகை"]):
                mapping["doc_type"] = idx
            elif any(k in h_lower for k in ["doc no", "doc. no", "document no", "document number", "doc_no", "ஆவண எண்", "ஆவண_எண்", "ஆவணஎண்", "document"]):
                mapping["doc_no"] = idx
            elif any(k in h_lower for k in ["reg date", "reg. date", "registration date", "date of reg", "date of registration", "பதிவு நாள்", "பதிவு தேதி", "பதிவுநாள்"]):
                mapping["reg_date"] = idx
            elif any(k in h_lower for k in ["executant", "எழுதி கொடுத்தவர்", "எழுதிக்கொடுத்தவர்", "எழுதி_கொடுத்தவர்"]):
                mapping["executants"] = idx
            elif any(k in h_lower for k in ["claimant", "எழுதி வாங்கியவர்", "எழுதிவாங்கியவர்", "எழுதி_வாங்கியவர்"]):
                mapping["claimants"] = idx
            elif any(k in h_lower for k in ["market", "guideline", "சந்தை", "market value"]):
                mapping["market_value"] = idx
            elif any(k in h_lower for k in ["consideration", "கைமாற்று", "மதிப்பு", "amount"]):
                mapping["consideration"] = idx
            elif any(k in h_lower for k in ["survey", "புல எண்", "புலஎண்", "சர்வே", "sub division", "subdivision", "உட்பிரிவு"]):
                mapping["survey_numbers"] = idx
        return mapping

    @classmethod
    def _extract_record_from_row(cls, cells: List[str], col_map: Dict[str, int]) -> Optional[ECRecord]:
        """Extract an ECRecord from row cell texts using column mapping or positional fallback."""
        if not cells:
            return None

        # Positional extraction or mapped extraction
        doc_no = cells[col_map["doc_no"]] if "doc_no" in col_map and col_map["doc_no"] < len(cells) else cells[0]
        if not doc_no or doc_no.lower() in ["sl no", "வ.எண்", "#", "s.no"]:
            return None

        # Registration date
        reg_date = (
            cells[col_map["reg_date"]] if "reg_date" in col_map and col_map["reg_date"] < len(cells) else None
        )
        # Fallback date search across cells
        if not reg_date:
            for cell in cells:
                if re.search(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{4}\b", cell):
                    reg_date = cell
                    break

        # Document year
        doc_year = parse_year(doc_no) or parse_year(reg_date)

        # Document type
        doc_type = (
            cells[col_map["doc_type"]] if "doc_type" in col_map and col_map["doc_type"] < len(cells) else None
        )

        # Executants
        executants: List[str] = []
        if "executants" in col_map and col_map["executants"] < len(cells):
            raw = cells[col_map["executants"]]
            executants = [p.strip() for p in re.split(r"[,;\n]+", raw) if p.strip()]

        # Claimants
        claimants: List[str] = []
        if "claimants" in col_map and col_map["claimants"] < len(cells):
            raw = cells[col_map["claimants"]]
            claimants = [p.strip() for p in re.split(r"[,;\n]+", raw) if p.strip()]

        # Consideration value
        consideration_val = None
        if "consideration" in col_map and col_map["consideration"] < len(cells):
            consideration_val = parse_currency(cells[col_map["consideration"]])

        # Market value
        market_val = None
        if "market_value" in col_map and col_map["market_value"] < len(cells):
            market_val = parse_currency(cells[col_map["market_value"]])

        # Survey numbers
        survey_numbers: List[str] = []
        if "survey_numbers" in col_map and col_map["survey_numbers"] < len(cells):
            raw_surv = cells[col_map["survey_numbers"]]
            # Split only on commas, semicolons, and newlines — preserve slashes for subdivisions (e.g. 999/1, 999/1A)
            tokens = [re.sub(r"\s*/\s*", "/", s.strip()) for s in re.split(r"[,;\n]+", raw_surv) if s.strip()]
            cleaned_survs = []
            i = 0
            while i < len(tokens):
                tok = tokens[i]
                if "/" in tok or "-" in tok:
                    cleaned_survs.append(tok)
                    i += 1
                elif tok.isdigit() and i + 1 < len(tokens) and "/" not in tokens[i + 1]:
                    # Handle alternating survey, subdivision tokens (e.g. "999, 1" -> "999/1")
                    cleaned_survs.append(f"{tok}/{tokens[i + 1]}")
                    i += 2
                else:
                    cleaned_survs.append(tok)
                    i += 1
            survey_numbers = cleaned_survs

        return ECRecord(
            document_number=doc_no,
            document_year=doc_year,
            registration_date=reg_date,
            document_type=doc_type,
            executants=executants,
            claimants=claimants,
            consideration_value=consideration_val,
            market_value=market_val,
            survey_numbers=survey_numbers,
        )

    @staticmethod
    def extract_pdf_params(html: str) -> Optional[Dict[str, str]]:
        """Extract hidden parameter fields needed for previewECWisePdf."""
        soup = BeautifulSoup(html, "html.parser")
        app_trans_id = soup.find("input", attrs={"name": re.compile(r"^appTransId$", re.I)}) or soup.find("input", id=re.compile(r"^appTransId$", re.I))
        doc_create_app_id = soup.find("input", attrs={"name": re.compile(r"^docCreateAppId$", re.I)}) or soup.find("input", id=re.compile(r"^docCreateAppId$", re.I))
        template_ids = soup.find("input", attrs={"name": re.compile(r"^templateIds$", re.I)}) or soup.find("input", id=re.compile(r"^templateIds$", re.I))
        json_string = soup.find("input", attrs={"name": re.compile(r"^jsonString$", re.I)}) or soup.find("input", id=re.compile(r"^jsonString$", re.I))
        start_date = soup.find("input", attrs={"name": re.compile(r"^txt_PeriodStartDt$", re.I)}) or soup.find("input", id=re.compile(r"^txt_PeriodStartDt$", re.I))
        end_date = soup.find("input", attrs={"name": re.compile(r"^txt_PeriodEndDt$", re.I)}) or soup.find("input", id=re.compile(r"^txt_PeriodEndDt$", re.I))

        if not app_trans_id or app_trans_id.get("value") in ["0", "", None]:
            return None

        return {
            "appTransId": app_trans_id.get("value", "0"),
            "docCreateAppId": doc_create_app_id.get("value", "8400001") if doc_create_app_id else "8400001",
            "tmpltMstID": "8400003",
            "previewFlagFrmCnfg": "true",
            "templateIds": template_ids.get("value", "") if template_ids else "",
            "tableString": "8400001~A4~NA~1~1~2.5~2.5~29.7~21.0~LandScape~cm~null~2.5",
            "txt_PeriodStartDt": start_date.get("value", "") if start_date else "",
            "txt_PeriodEndDt": end_date.get("value", "") if end_date else "",
            "jsonString": json_string.get("value", "") if json_string else "",
        }
