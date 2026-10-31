"""Portal CAPTCHA retrieval and validation operations."""

import logging
import time
import urllib.parse
from typing import Tuple

from app.errors import PortalError
from app.portal.client import PortalHttpClient

logger = logging.getLogger("ground_truth.captcha")


async def fetch_captcha_image(client: PortalHttpClient) -> Tuple[bytes, str]:
    """Retrieve the real CAPTCHA image from TNREGINET for the active session.

    Never generates fake CAPTCHAs or calls automated solvers.
    """
    ts = int(time.time() * 1000)
    url = f"/portal/SimpleCaptcha?{ts}"
    resp = await client.get(url)

    if resp.status_code != 200:
        raise PortalError(f"Failed to fetch CAPTCHA image: HTTP {resp.status_code}")

    content_type = resp.headers.get("content-type", "image/png").split(";")[0].strip()
    if not resp.content or len(resp.content) < 100:
        raise PortalError("Portal returned empty or truncated CAPTCHA image")

    logger.info(f"Retrieved real CAPTCHA image ({len(resp.content)} bytes, {content_type})")
    return resp.content, content_type


async def verify_captcha_text(client: PortalHttpClient, captcha_text: str, csrf_token: str) -> Tuple[bool, str]:
    """Verify submitted CAPTCHA string via the portal's checkCaptcha endpoint.

    Returns (is_valid, message).
    """
    encoded_val = urllib.parse.quote(captcha_text.strip())
    url = f"/portal/webHP?requestType=ApplicationRH&actionVal=checkCaptcha&queryType=Select&screenId=114&captcha_val={encoded_val}"
    headers = {
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    }
    data = {"_csrf": csrf_token}

    resp = await client.post(url, data=data, headers=headers)
    if resp.status_code != 200:
        logger.warning(f"checkCaptcha returned HTTP {resp.status_code}")
        raise PortalError(f"Failed to verify CAPTCHA with portal: HTTP {resp.status_code}")

    raw_text = resp.text.strip()
    # Response structure: <?xml ...?>#Message#true/false
    parts = raw_text.split("#")
    if len(parts) >= 3:
        msg = parts[1].strip()
        flag = parts[2].strip().lower()
        is_valid = flag == "true"
        return is_valid, msg

    # Fallback check
    if "false" in raw_text.lower():
        return False, "Incorrect CAPTCHA code"
    if "true" in raw_text.lower():
        return True, "CAPTCHA verified"

    raise PortalError(f"Unrecognized checkCaptcha response from portal: {raw_text[:120]}")

