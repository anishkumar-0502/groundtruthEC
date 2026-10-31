# TNREGINET Portal Findings & Reverse-Engineering Technical Report

## 1. Overview & Verification Status

This document records the empirical findings from direct inspection and interaction with the official Tamil Nadu Registration Department portal:
- **Base URL:** `https://tnreginet.gov.in/portal/`
- **Application Engine:** Java Servlet / JSP 2.3 with Spring Security and jQuery front-end (not ASP.NET).
- **Session Cookie:** `PORTALJSESSIONID` (e.g. `PORTALJSESSIONID=wiwKbt_Sd8Ijn7KhGoHMDXIBbOIQCUI9EYXAn3nz.portal6; Path=/portal; HttpOnly`).
- **CSRF Protection:** Double CSRF mechanism:
  1. Meta CSRF token: `<meta name="_csrf" content="<uuid>"/>` and header `X-CSRF-TOKEN`.
  2. JavaScript dynamically embedded CSRF token: `function getAjaxSecurityToken() { var csrf = '<uuid>'; return csrf; }`.
  3. Per-form anti-tampering token: `<input type="hidden" name="authToken" id="authToken" value="<token>"/>` generated inside `EncumbranceCertificateForm`.

---

## 2. Navigation Sequence to EC Search

1. **Portal Entry:**
   - `GET https://tnreginet.gov.in/portal/`
   - Yields initial `PORTALJSESSIONID` and homepage CSRF tokens.

2. **Open Encumbrance Certificate Search Module:**
   - URL: `GET https://tnreginet.gov.in/portal/webHP?requestType=ApplicationRH&actionVal=openEncumbranceCertSearch&screenId=8400001&scenarioId=2&menuCode=8400010&auditUSFlag=true`
   - Triggered on portal via JavaScript function `menuAct(...)`.
   - Returns the full EC Search Page containing:
     - Embedded CSRF token (`var csrf = '...'`)
     - Form `EncumbranceCertificateForm`
     - Pre-populated Zones dropdown (`cmb_Zone`) with 12 Tamil Nadu registration zones.
     - Search type radio buttons:
       - `DOC_SEARCH=1`: Survey Number / Year wise (`YEAR_WISE`)
       - `DOC_SEARCH=2`: Document wise (`DOC_WISE`)
       - `DOC_SEARCH=3`: Plot / Flat wise (`PLOT_FLAT_WISE`)
       - `DOC_SEARCH=4`: Ward / Block wise (`WADR_BLOCK_WISE`)
     - Village selection radio buttons:
       - `VILLAGE_SELECTION=false`: Registration Village (`REGISTRATION_VILLAGE` - default)
       - `VILLAGE_SELECTION=true`: Revenue Village (`REVENUE_VILLAGE`)
     - Dynamic CAPTCHA image element (`<img src="SimpleCaptcha?<timestamp>" id="captcha"/>`).

---

## 3. Dynamic Location Hierarchy & Endpoints

All dynamic location combo requests use `POST` to `webHP` with query parameters and `_csrf` security token. Responses are returned as XML/HTML `<select>` fragments.

### Level 1: Zones (`cmb_Zone`)
- Embedded directly in the initial search page HTML inside `<select name="cmb_Zone" id="cmb_Zone">`.
- Examples verified on live portal:
  - `ID: 2` - கோயம்புத்தூர் (Coimbatore)
  - `ID: 1` - சென்னை (Chennai)
  - `ID: 4` - மதுரை (Madurai)
  - `ID: 5` - சேலம் (Salem)
  - `ID: 6` - திருச்சி (Trichy)
  - `ID: 9` - வேலூர் (Vellore)
  - `ID: 15` - செங்கல்பட்டு (Chengalpattu)
  - `ID: 8` - திருநெல்வேலி (Tirunelveli)
  - `ID: 7` - தஞ்சாவூர் (Thanjavur)
  - `ID: 3` - கடலூர் (Cuddalore)
  - `ID: 13` - இராமநாதபுரம் (Ramanathapuram)

### Level 2: Districts (`cmb_District`)
- **Trigger:** JavaScript `makeDistrictRequest()` on `cmb_Zone` change.
- **Request:**
  - `POST https://tnreginet.gov.in/portal/webHP?requestType=ApplicationRH&actionVal=loadDistrictCombo&queryType=Select&screenId=8400001&comboValue={zone_id}&_csrf={csrf_token}`
- **Verified Response for Zone 2 (Coimbatore):**
  - `20006`: கோயம்புத்தூர் வடக்கு (Coimbatore North)
  - `50006`: கோயம்புத்தூர் தெற்கு (Coimbatore South)
  - `20007`: திருப்பூர் (Tiruppur)
  - `20008`: ஊட்டி (Ooty)
  - `20009`: ஈரோடு (Erode)
  - `20010`: கோபிச்செட்டிப்பாளையம் (Gobichettipalayam)

### Level 3: Sub-Registrar Offices / SROs (`cmb_SroName`)
- **Trigger:** JavaScript `makeSroRequest()` on `cmb_District` change.
- **Request:**
  - `POST https://tnreginet.gov.in/portal/webHP?requestType=ApplicationRH&actionVal=loadSroCombo&queryType=Select&screenId=8400001&comboValue={district_id}&_csrf={csrf_token}`
- **Verified SRO Identifiers:**
  - SRO values have the format `{sro_number}:{status_flag}`, e.g.:
    - `20120:1`: மதுக்கரை (Madukkarai) - Active (`:1`)
    - `20117:1`: சிங்காநல்லூர் (Singanallur)
    - `20123:1`: பீளமேடு (Peelamedu)
    - `20130:1`: சூலூர் (Sulur)
    - `20116:0`: 2 எண் இணை சார்பதிவாளர் கோயம்புத்தூர்_மூடப்பட்டது - Closed (`:0`)

### Level 4: Villages (`cmb_Village`)
- **Trigger:** JavaScript `makeVillageRequest()` on `cmb_SroName` change.
- **Request:**
  - `POST https://tnreginet.gov.in/portal/webHP?requestType=ApplicationRH&actionVal=loadVillageCombo&queryType=Select&screenId=8400001&comboValue={sro_id}&_csrf={csrf_token}`
  - Example: `comboValue=20120:1`
- **Verified Villages for Madukkarai SRO (`20120:1`):**
  - `2739`: மதுக்கரை (Madukkarai)
  - `2740`: எட்டிமடை (Ettimadai)
  - `2741`: பிச்சனூர் (Pichanur)
  - `2743`: சுண்டக்காமுத்தூர் (Sundakkamuthur)
  - `2745`: மலுமிச்சம்பட்டி (Malumichampatti)
  - `2746`: நாச்சி பாளையம் (Nachipalayam)
  - `2747`: பாலத்துறை (Palathurai)
  - `2748`: கருஞ்சாமிக் கவுண்டன் பாளையம் (Karunjamigoundenpalayam)
  - `2749`: மாவுத்தம்பதி (Mavuthampathi)

### Level 5: Town Wards & Blocks (`DOC_SEARCH=4`)
When switching to Ward/Block mode via `openBlockWardWiseSearch`:
1. `POST webHP?requestType=ApplicationRH&actionVal=openBlockWardWiseSearch&screenId=8400001&divId=searchComponentSection&_csrf={csrf}&DOC_SEARCH=4&formId=EncumbranceCertificateForm`
2. **Towns (`cmb_reg_town_revenue`):**
   - Function: `LoadTownCombo()`
   - `POST webHP?requestType=ApplicationRH&actionVal=getTownDetails&screenId=8400001&regVillage={village_id}&townCode=-1&townName=-1&selectedTownId=-1&isRevVilMappedToRegVillage=&_csrf={csrf}`
3. **Wards (`cmb_ward_no_revenue`):**
   - Function: `LoadWardCombo()`
   - `POST webHP?requestType=ApplicationRH&actionVal=getRevWardDetails&screenId=8400001&revDist={revDist}&taluk={taluk}&townCode={townCode}&talukMappingLoadedCase={case}&regVillageId={regVillageId}&townId={townId}&_csrf={csrf}`
4. **Blocks (`cmb_block_revenue`):**
   - Function: `LoadBlockCombo()`
   - `POST webHP?requestType=ApplicationRH&actionVal=getRevBlockDetails&screenId=8400001&revDist={revDist}&taluk={taluk}&townCode={townCode}&wardCode={wardCode}&talukMappingLoadedCase={case}&regVillageId={regVillageId}&townId={townId}&_csrf={csrf}`

---

## 4. CAPTCHA Mechanism & Validation

1. **Image Retrieval:**
   - `GET https://tnreginet.gov.in/portal/SimpleCaptcha?{timestamp}`
   - Headers: Cookie session (`PORTALJSESSIONID`) is strictly required.
   - Response: `image/png` binary content (~5–7 KB).

2. **Server-Side Validation:**
   - `POST https://tnreginet.gov.in/portal/webHP?requestType=ApplicationRH&actionVal=checkCaptcha&queryType=Select&screenId=114&captcha_val={encoded_text}`
   - Body: `_csrf={csrf_token}`
   - Verified Response Format (delimiter: `#`):
     - **Incorrect CAPTCHA:**
       `<?xml version="1.0" encoding='UTF-8' standalone='yes'?>#தயவுசெய்து சரியான காப்புக் குறியீட்டினை உள்ளிடவும்#false`
       Where index 1 is Tamil message: *"Please enter the correct captcha code"* and index 2 is `"false"`.
     - **Correct CAPTCHA:**
       `<?xml version="1.0" encoding='UTF-8' standalone='yes'?>#...#true`

---

## 5. EC Search Submission & Session Continuity

1. **Preparation Sequence:**
   The portal's state machine tracks selections across the session:
   - Initial page load provides `authToken` and CSRF tokens.
   - SRO and Village combos must be traversed so server session records the context.
   - Survey numbers are added via hidden inputs:
     - `multi_SurveyNo={survey_no}`
     - `multi_SubDivisionNo={subdiv_no}`
     - `multi_cmb_Village={village_id}`
     - `hdnZone`, `hdnDistrict`, `hdnSroName` carry selected IDs.
   - Date range fields: `txt_PeriodStartDt` and `txt_PeriodEndDt` in `DD/MM/YYYY` format.

2. **Search Request Architecture (`updateContainer`):**
   - In TNREGINET's client script `content.min.js`, the search submission function `searchDocDtlsYearWise` calls:
     ```javascript
     var url = urlHome + "?requestType=ApplicationRH&actionVal=searchDocYearWise&screenId=8400001&divId=searchComponentSection&isPlotFlatWise=false&_csrf=" + getAjaxSecurityToken() + "&" + $.param($('#EncumbranceCertificateForm').serializeArray());
     updateContainer(url, "", 'searchComponentSection');
     ```
   - The servlet dispatches `actionVal=searchDocYearWise` strictly when the form parameters are passed in the **URL query string** with `portal=CAS&_csrf=...` in the POST body.
   - **Atomic CAPTCHA Validation:** `searchDocYearWise` validates the CAPTCHA atomically during search execution. Pre-flighting `checkCaptcha` before `searchDocYearWise` prematurely consumes the session CAPTCHA and causes subsequent search failures.
   - **Template Error Handlers vs Actual Session Expiration:** Every single JSP returned by TNREGINET includes a JavaScript callback handler:
     ```javascript
     if (xmlHttpRequest.status == 200) { ... }
     else { window.location = "sessionExpire.jsp"; }
     ```
     Substrings like `"sessionexpire.jsp"` in the raw HTML must therefore never be used alone to classify a page as session-expired. Instead, HTML parser must decompose `<script>` and `<style>` tags to evaluate genuine visible text indicators (`உங்கள் அமர்வு காலாவதியாகி விட்டது`, `Session Expired` in title or body, or tiny `< 500` byte direct redirect snippets).

3. **Response Classification:**
   - **`no_records`**: Response HTML contains `<div id="divNothingFound">தேடுதல் காலத்தில் எந்த ஆவணங்களும் பதிவு செய்யப்படவில்லை.</div>` (explicit message that no documents were registered in the period).
   - **`wrong_captcha`**: `checkCaptcha` returns `#false` or response alerts `சரியான காப்புக் குறியீட்டினை உள்ளிடவும்`.
   - **`session_expired`**: Response title `Error Page` or body containing `மன்னிக்கவும்! உங்கள் அமர்வு காலாவதியாகி விட்டது` / redirect to `sessionExpire.jsp`.
   - **`too_many_records`**: Portal returns maximum search limit alert or exceeds `multiVillageLimitEC`.
   - **`found`**: `#divPropertyList` contains table rows with document entries.

---

## 6. PDF Retrieval Mechanism

1. **JavaScript Function:** `previewPdfFun()`
2. **Endpoint:**
   - `GET https://tnreginet.gov.in/portal/webHP?requestType=ApplicationRH&actionVal=previewECWisePdf&screenId=8400001&appTransId={appTransId}&docCreateAppId={docCreateAppId}&tmpltMstID=8400003&previewFlagFrmCnfg=true&templateIds={templateIds}&tableString=8400001~A4~NA~1~1~2.5~2.5~29.7~21.0~LandScape~cm~null~2.5&txt_PeriodStartDt={start_date}&txt_PeriodEndDt={end_date}&jsonString={jsonString}`
3. **Session Dependency:**
   - Uses the same active session cookies.
   - Valid PDF response begins with standard binary signature `%PDF-1.`.
   - If not available or search had no records, portal does not generate a PDF; our service cleanly reports `pdf_unavailable`.

---

## 7. Multilingual Support & Portal Localization (English & Tamil)

1. **Locale Management on TNREGINET:**
   - The portal maintains a session-level locale (`UserLocaleID`).
   - By default or when explicitly passed `UserLocaleID=en`, the portal translates dropdown labels natively into English (e.g. `Coimbatore`, `Coimbatore South`, `Madukkarai`, `Ettimadai`).
   - When requested with `UserLocaleID=ta`, labels are returned in native Tamil script (`கோயம்புத்தூர்`, `கோயம்புத்தூர் தெற்கு`, `மதுக்கரை`, `எட்டிமடை`).

2. **Localization Endpoint Flow:**
   - Homepage locale priming:
     `POST /portal/webHP?requestType=ApplicationRH&actionVal=homePage&screenId=114&UserLocaleID=en&_csrf={csrf}`
   - Opening EC search module with language parameter:
     `GET /portal/webHP?...&UserLocaleID={lang}`
   - Dynamic location combo queries (`loadDistrictCombo`, `loadSroCombo`, `loadVillageCombo`, `getTownDetails`, etc.) accept `&UserLocaleID={lang}` to return `<option>` text in the requested language.

3. **JSP Zone Rendering Anomaly:**
   - While AJAX combo endpoints honor `UserLocaleID=en` dynamically, the initial JSP template for `openEncumbranceCertSearch` hardcodes all 38 revenue zone names in Tamil (`அரியலூர்`, `கோயம்புத்தூர்`, `சென்னை`...).
   - Solved by implementing an automated bidirectional lookup for all 38 Tamil Nadu zones and districts in `app/portal/locations.py` and `frontend/app.js`.

---

## 8. Tomcat Request Buffer Constraints on Search Submission

1. **Query String Length Rejection:**
   - TNREGINET runs Apache Tomcat with strict URL query string size thresholds.
   - When a POST request serializes all 25+ form fields into the URL query string (`len(url) > 1000`), Tomcat aborts processing and serves a generic Error Page: `<title>Error Page</title>` with text `"Sorry! An error has occurred"`.
   - By submitting the payload via `application/x-www-form-urlencoded` in the HTTP POST body while keeping only minimal routing params on the URL (`/portal/webHP?requestType=ApplicationRH&actionVal=searchDocYearWise&portal=CAS&_csrf={csrf}`), the request executes cleanly without triggering Tomcat errors.


