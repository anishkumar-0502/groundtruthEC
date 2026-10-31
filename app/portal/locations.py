"""Portal location extraction and lookup module with multilingual support."""

import logging
import re
from typing import List, Tuple
import warnings
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

from app.errors import PortalError
from app.portal.client import PortalHttpClient
from app.schemas.locations import LocationItem

logger = logging.getLogger("ground_truth.portal_locations")

# Default placeholders to filter out of selectable location items
EXCLUDED_VALUES = {"-1", "", "null", "undefined"}
EXCLUDED_NAMES = {
    "தெரிவு செய்க",
    "select",
    "--select--",
    "choose",
    "- select -",
    "-select-",
    "-- select --",
}

# Comprehensive bilingual translation map for TNREGINET Zones and Districts
TAMIL_TO_ENGLISH_LOCATIONS = {
    "அரியலூர்": "Ariyalur",
    "இராணிப்பேட்டை": "Ranipet",
    "இராமநாதபுரம்": "Ramanathapuram",
    "ராமநாதபுரம்": "Ramanathapuram",
    "ஈரோடு": "Erode",
    "கடலூர்": "Cuddalore",
    "கரூர்": "Karur",
    "கள்ளக்குறிச்சி": "Kallakurichi",
    "கன்னியாகுமரி": "Kanyakumari",
    "காஞ்சிபுரம்": "Kanchipuram",
    "கிருஷ்ணகிரி": "Krishnagiri",
    "கோயம்புத்தூர்": "Coimbatore",
    "கோயமுத்தூர்": "Coimbatore",
    "கோயம்புத்தூர் தெற்கு": "Coimbatore South",
    "கோயம்புத்தூர் வடக்கு": "Coimbatore North",
    "சிவகங்கை": "Sivagangai",
    "செங்கல்பட்டு": "Chengalpattu",
    "சென்னை": "Chennai",
    "சென்னை தெற்கு": "Chennai South",
    "சென்னை மத்திய": "Chennai Central",
    "சென்னை வடக்கு": "Chennai North",
    "சேலம்": "Salem",
    "சேலம் மேற்கு": "Salem West",
    "சேலம் கிழக்கு": "Salem East",
    "தஞ்சாவூர்": "Thanjavur",
    "தர்மபுரி": "Dharmapuri",
    "திருவாரூர்": "Tiruvarur",
    "திண்டுக்கல்": "Dindigul",
    "திருச்சிராப்பள்ளி": "Tiruchirappalli",
    "திருச்சி": "Tiruchirappalli",
    "திருநெல்வேலி": "Tirunelveli",
    "திருப்பத்தூர்": "Tirupathur",
    "திருப்பூர்": "Tiruppur",
    "திருவண்ணாமலை": "Tiruvannamalai",
    "திருவள்ளூர்": "Tiruvallur",
    "தூத்துக்குடி": "Thoothukudi",
    "தென்காசி": "Tenkasi",
    "தேனி": "Theni",
    "நாகப்பட்டினம்": "Nagapattinam",
    "நாமக்கல்": "Namakkal",
    "நீலகிரி": "Nilgiris",
    "புதுக்கோட்டை": "Pudukkottai",
    "பெரம்பலூர்": "Perambalur",
    "மதுரை": "Madurai",
    "மதுரை தெற்கு": "Madurai South",
    "மதுரை வடக்கு": "Madurai North",
    "மயிலாடுதுறை": "Mayiladuthurai",
    "விருதுநகர்": "Virudhunagar",
    "விழுப்புரம்": "Villupuram",
    "வேலூர்": "Vellore",
    "கோபிசெட்டிபாளையம்": "Gobichettipalayam",
    "ஊட்டி": "Ooty",
    "உதகமண்டலம்": "Ooty",
    "மதுக்கரை": "Madukkarai",
    "சிங்காநல்லூர்": "Singanallur",
    "பீளமேடு": "Peelamedu",
    "சூலூர்": "Sulur",
    "பொள்ளாச்சி": "Pollachi",
    "ஆனைமலை": "Anaimalai",
    "கிணத்துக்கடவு": "Kinathukkadavu",
    "நெகமம்": "Negamam",
    "குமாரபாளையம்": "Kumarapalayam",
    "பவானி": "Bhavani",
    "அம்மாபேட்டை": "Ammapettai",
    "தெற்கு": "South",
    "வடக்கு": "North",
    "கிழக்கு": "East",
    "மேற்கு": "West",
    "மத்திய": "Central",
    "இணை": "Joint",
}

ENGLISH_TO_TAMIL_LOCATIONS = {v: k for k, v in TAMIL_TO_ENGLISH_LOCATIONS.items()}


def parse_select_options(
    html_or_xml: str, select_id_or_name: str = "", lang: str = None
) -> List[LocationItem]:
    """Parse `<option>` tags from an HTML or XML `<select>` element.

    Preserves Tamil text or English names and excludes default prompt entries.
    If lang is 'en' or 'ta', maps location names to the requested language.
    """
    soup = BeautifulSoup(html_or_xml, "html.parser")

    options = []
    if select_id_or_name:
        select_tag = soup.find("select", id=select_id_or_name) or soup.find("select", attrs={"name": select_id_or_name})
        if select_tag:
            options = select_tag.find_all("option")
    else:
        options = soup.find_all("option")

    items: List[LocationItem] = []
    for opt in options:
        val = opt.get("value", "").strip()
        name = opt.get_text(strip=True)
        if not val or val in EXCLUDED_VALUES:
            continue
        if name.lower() in EXCLUDED_NAMES or any(prompt in name.lower() for prompt in ["தெரிவு செய்க", "select", "choose", "தேர்ந்தெடு"]):
            continue
        # Filter out decommissioned/closed SRO offices (marked with :0 or closed)
        if (select_id_or_name == "cmb_SroName" or "sro" in select_id_or_name.lower()) and (
            val.endswith(":0") or "closed" in name.lower() or "மூடப்பட்டது" in name
        ):
            continue

        # Language translation mapping if requested
        if lang == "en":
            clean_n = name.strip()
            if clean_n in TAMIL_TO_ENGLISH_LOCATIONS:
                name = TAMIL_TO_ENGLISH_LOCATIONS[clean_n]
            else:
                for ta_k, en_v in TAMIL_TO_ENGLISH_LOCATIONS.items():
                    if ta_k in clean_n:
                        name = clean_n.replace(ta_k, en_v)
                        break
        elif lang == "ta":
            clean_n = name.strip()
            if clean_n in ENGLISH_TO_TAMIL_LOCATIONS:
                name = ENGLISH_TO_TAMIL_LOCATIONS[clean_n]
            else:
                for en_k, ta_v in ENGLISH_TO_TAMIL_LOCATIONS.items():
                    if en_k.lower() in clean_n.lower():
                        name = re.sub(re.escape(en_k), ta_v, clean_n, flags=re.IGNORECASE)
                        break

        items.append(LocationItem(id=val, name=name))

    return items


async def fetch_initial_page_and_zones(client: PortalHttpClient, lang: str = "en") -> Tuple[str, str, List[LocationItem]]:
    """Fetch initial EC page with specified language, returning (csrf_token, auth_token, zones_list)."""
    # 1. Fetch portal home for initial cookies
    r0 = await client.get("/portal/")

    # Explicitly set the session locale on TNREGINET
    m_home_csrf = re.search(r"var csrfVal=\s*['\"]([^'\"]+)['\"]", r0.text)
    csrf_val = m_home_csrf.group(1) if m_home_csrf else ""
    if csrf_val:
        try:
            await client.post(
                f"/portal/webHP?requestType=ApplicationRH&actionVal=homePage&screenId=114&UserLocaleID={lang}&_csrf={csrf_val}",
                data={"UserLocaleID": lang, "_csrf": csrf_val},
            )
        except Exception as e:
            logger.debug(f"Non-critical error setting session locale: {e}")

    # 2. Open EC search page with UserLocaleID parameter
    ec_url = f"/portal/webHP?requestType=ApplicationRH&actionVal=openEncumbranceCertSearch&screenId=8400001&scenarioId=2&menuCode=8400010&auditUSFlag=true&UserLocaleID={lang}"
    response = await client.get(ec_url)

    if response.status_code != 200:
        raise PortalError(f"Failed to open EC search page: HTTP {response.status_code}")

    html = response.text
    if "Error Page" in html and ("மன்னிக்கவும்" in html or "sorry" in html.lower()):
        raise PortalError("Portal returned error page on opening EC search module")

    # Extract dynamic CSRF token
    m_csrf = re.search(r"var csrf\s*=\s*['\"]([^'\"]+)['\"]", html)
    csrf_token = m_csrf.group(1) if m_csrf else ""

    # Extract form authToken
    soup = BeautifulSoup(html, "html.parser")
    auth_input = soup.find("input", attrs={"name": "authToken"})
    auth_token = auth_input.get("value", "") if auth_input else ""

    # Parse zones
    zones = parse_select_options(html, select_id_or_name="cmb_Zone", lang=lang)
    if not zones:
        logger.warning(f"No zones parsed from EC search page (lang={lang})")

    return csrf_token, auth_token, zones


async def fetch_districts(client: PortalHttpClient, zone_id: str, csrf_token: str, lang: str = "en") -> List[LocationItem]:
    """Retrieve districts under a given zone via loadDistrictCombo."""
    url = f"/portal/webHP?requestType=ApplicationRH&actionVal=loadDistrictCombo&queryType=Select&screenId=8400001&comboValue={zone_id}&_csrf={csrf_token}&UserLocaleID={lang}"
    headers = {"X-Requested-With": "XMLHttpRequest"}
    resp = await client.post(url, headers=headers)

    if resp.status_code != 200:
        raise PortalError(f"Portal district request failed with HTTP {resp.status_code}")

    return parse_select_options(resp.text, select_id_or_name="cmb_District", lang=lang)


async def fetch_sros(client: PortalHttpClient, district_id: str, csrf_token: str, lang: str = "en") -> List[LocationItem]:
    """Retrieve SROs under a given district via loadSroCombo."""
    url = f"/portal/webHP?requestType=ApplicationRH&actionVal=loadSroCombo&queryType=Select&screenId=8400001&comboValue={district_id}&_csrf={csrf_token}&UserLocaleID={lang}"
    headers = {"X-Requested-With": "XMLHttpRequest"}
    resp = await client.post(url, headers=headers)

    if resp.status_code != 200:
        raise PortalError(f"Portal SRO request failed with HTTP {resp.status_code}")

    return parse_select_options(resp.text, select_id_or_name="cmb_SroName", lang=lang)


async def fetch_villages(client: PortalHttpClient, sro_id: str, csrf_token: str, lang: str = "en") -> List[LocationItem]:
    """Retrieve villages under a given SRO via loadVillageCombo."""
    url = f"/portal/webHP?requestType=ApplicationRH&actionVal=loadVillageCombo&queryType=Select&screenId=8400001&comboValue={sro_id}&_csrf={csrf_token}&UserLocaleID={lang}"
    headers = {"X-Requested-With": "XMLHttpRequest"}
    resp = await client.post(url, headers=headers)

    if resp.status_code != 200:
        raise PortalError(f"Portal village request failed with HTTP {resp.status_code}")

    return parse_select_options(resp.text, select_id_or_name="cmb_Village", lang=lang)


async def fetch_towns(client: PortalHttpClient, village_id: str, csrf_token: str, lang: str = "en") -> List[LocationItem]:
    """Retrieve towns mapped to a village via getTownDetails."""
    url = f"/portal/webHP?requestType=ApplicationRH&actionVal=getTownDetails&screenId=8400001&regVillage={village_id}&townCode=-1&townName=-1&selectedTownId=-1&isRevVilMappedToRegVillage=&_csrf={csrf_token}&UserLocaleID={lang}"
    headers = {"X-Requested-With": "XMLHttpRequest"}
    resp = await client.post(url, headers=headers)

    if resp.status_code != 200:
        raise PortalError(f"Portal town request failed with HTTP {resp.status_code}")

    return parse_select_options(resp.text, select_id_or_name="cmb_reg_town_revenue", lang=lang)


async def fetch_wards(
    client: PortalHttpClient,
    village_id: str,
    town_code: str,
    csrf_token: str,
    rev_dist: str = "-1",
    taluk: str = "-1",
    town_id: str = "-1",
    lang: str = "en",
) -> List[LocationItem]:
    """Retrieve wards under a town via getRevWardDetails."""
    url = (
        f"/portal/webHP?requestType=ApplicationRH&actionVal=getRevWardDetails&screenId=8400001"
        f"&revDist={rev_dist}&taluk={taluk}&townCode={town_code}&talukMappingLoadedCase=3"
        f"&regVillageId={village_id}&townId={town_id}&_csrf={csrf_token}&UserLocaleID={lang}"
    )
    headers = {"X-Requested-With": "XMLHttpRequest"}
    resp = await client.post(url, headers=headers)

    if resp.status_code != 200:
        raise PortalError(f"Portal ward request failed with HTTP {resp.status_code}")

    return parse_select_options(resp.text, select_id_or_name="cmb_ward_no_revenue", lang=lang)


async def fetch_blocks(
    client: PortalHttpClient,
    village_id: str,
    town_code: str,
    ward_code: str,
    csrf_token: str,
    rev_dist: str = "-1",
    taluk: str = "-1",
    town_id: str = "-1",
    lang: str = "en",
) -> List[LocationItem]:
    """Retrieve blocks under a ward via getRevBlockDetails."""
    url = (
        f"/portal/webHP?requestType=ApplicationRH&actionVal=getRevBlockDetails&screenId=8400001"
        f"&revDist={rev_dist}&taluk={taluk}&townCode={town_code}&wardCode={ward_code}"
        f"&talukMappingLoadedCase=3&regVillageId={village_id}&townId={town_id}&_csrf={csrf_token}&UserLocaleID={lang}"
    )
    headers = {"X-Requested-With": "XMLHttpRequest"}
    resp = await client.post(url, headers=headers)

    if resp.status_code != 200:
        raise PortalError(f"Portal block request failed with HTTP {resp.status_code}")

    return parse_select_options(resp.text, select_id_or_name="cmb_block_revenue", lang=lang)
