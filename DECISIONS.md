# Architectural & Technical Design Decisions

This document records the architectural, engineering, and security design decisions made during the implementation of the **Ground Truth — TNREGINET Encumbrance Certificate Retrieval Service**.

---

## 1. Why the Application Uses No Database by Default

### Decision
The application intentionally uses an in-memory session manager without introducing an external relational (PostgreSQL) or document (MongoDB) database.

### Rationale
1. **Nature of the Workload:** An Encumbrance Certificate (EC) search on TNREGINET is inherently an ephemeral, real-time transaction requiring active communication with the external government portal state machine.
2. **Data Minimization & Compliance:** Land registry records, executant names, and transaction values contain sensitive personal and financial data. Storing these records permanently in an application database without strict data retention, user consent, and security policies poses unnecessary compliance risks.
3. **Simplicity & Operational Footprint:** A single backend engineer can run, test, and maintain the entire service locally with zero external infrastructure dependencies.
4. **Transparent Handoff:** In-memory storage is clearly bounded with a configurable Time-To-Live (TTL). When a search concludes or expires, all associated memory and HTTP connections are safely garbage collected.

---

## 2. Why HTTPX is the Appropriate HTTP Client

### Decision
HTTPX (`AsyncClient`) is used for all portal communication rather than `requests` or `urllib`.

### Rationale
1. **Asynchronous Architecture:** FastAPI is an asynchronous ASGI framework. HTTPX natively supports Python's `async`/`await` model via AnyIO, preventing blocking of the FastAPI event loop during outbound I/O.
2. **State & Cookie Preservation:** TNREGINET relies strictly on sticky server cookies (`PORTALJSESSIONID`) and CSRF tokens across multi-step sequences. HTTPX `AsyncClient` maintains an isolated `CookieJar` per search session.
3. **Connection Pooling & Timeouts:** Built-in connection pooling and explicit fine-grained timeout controls (connect, read, write) ensure unresponsive portal endpoints fail gracefully.
4. **Mockability:** HTTPX clients and transports can be cleanly mocked in unit and integration tests without network access.

---

## 3. How Portal Sessions are Maintained

### Decision
Each user search initiates an isolated `SearchSession` managed by `SessionManager` and assigned a cryptographically random 32-byte URL-safe session ID (`secrets.token_urlsafe(32)`).

### Rationale
1. **Client Isolation:** Each `SearchSession` holds its own dedicated `PortalHttpClient` instance. This prevents cookie leakage, CSRF token collisions, or session cross-talk between different users.
2. **State Machine Traversal:** TNREGINET requires visiting the homepage, opening the EC module, traversing the combo endpoints (Zone → District → SRO → Village), and retrieving the CAPTCHA under the same session cookie.
3. **Security:** The internal portal cookies and server session identifiers are never exposed to API consumers or returned to the browser. The frontend interacts strictly with our application session ID.

---

## 4. How CAPTCHA is Handled

### Decision
CAPTCHA images are retrieved live from the portal, streamed to the client, and entered exclusively by a human. No automated solver, OCR, or third-party CAPTCHA bypass is used.

### Rationale
1. **Integrity & Compliance:** Automated CAPTCHA solving on government portals violates terms of service and acceptable use policies.
2. **Verified Portal Flow:** The portal generates `SimpleCaptcha?{timestamp}` linked directly to `PORTALJSESSIONID`. Our service streams this image via `GET /ec/sessions/{session_id}/captcha`.
3. **Verification & Execution:** TNREGINET validates the CAPTCHA atomically during the `searchDocYearWise` search submission. If rejected, the portal returns a specific wrong-captcha notification (e.g. `smoke.alert('Please Enter Valid Captcha')`), and our service reports `wrong_captcha` and immediately refreshes a fresh CAPTCHA for quick retry without losing the location selections. Redundant standalone pre-validation via `checkCaptcha` is deliberately avoided prior to search execution to prevent prematurely consuming the session CAPTCHA.

---

## 5. How Process-Wide Rate Limiting Works

### Decision
A shared `PortalRateLimiter` enforces a mandatory minimum interval of 2.0 seconds between request starts and strictly serializes outbound portal calls.

### Rationale
1. **Infrastructure Respect:** Government portals like TNREGINET run on public infrastructure and protect themselves with WAF rate limiting. Flooding or concurrent requests risks IP bans or service degradation.
2. **Strict Mutual Exclusion:** `PortalRateLimiter` uses an `asyncio.Lock`. This guarantees that **no two requests** to the portal can execute concurrently, even if multiple users invoke endpoints simultaneously.
3. **Accurate Interval Calculation:** The limiter computes `elapsed = time.monotonic() - last_request_start` and sleeps for `min_interval - elapsed` before releasing execution.

---

## 6. Why Parsing is Strictly Isolated from the HTTP Layer

### Decision
HTML/XML parsing logic (`ECResultParser`, `parse_select_options`) is completely decoupled from `PortalHttpClient` and HTTP handlers.

### Rationale
1. **100% Offline Testability:** The parsing suite runs entirely against sanitized HTML/XML fixtures without needing network access or a live portal connection.
2. **Resilience to Structure Changes:** When TNREGINET updates its table columns or markup, changes are localized to `parser.py` without touching HTTP client or router code.
3. **Language Neutrality:** The parser handles Tamil Unicode script (`ஆவண எண்`, `கிரைய ஆவணம்`, `எழுதி கொடுத்தவர்`) and English transliterations seamlessly.

---

## 7. Why `no_records` and `portal_error` are Strictly Separated

### Decision
The parser and service strictly distinguish between an explicit "no records" confirmation from the portal and an error or unexpected response structure.

### Rationale
1. **Truthfulness:** In real estate encumbrance checks, reporting "no records found" when a portal actually crashed or changed its HTML layout is dangerous (a false negative could mislead a buyer into believing a property has no encumbrances).
2. **Explicit Verification:** `no_records` is only returned when the portal explicitly indicates that no documents were registered in the period (e.g. `<div id="divNothingFound">தேடுதல் காலத்தில் எந்த ஆவணங்களும் பதிவு செய்யப்படவில்லை.</div>`).
3. **Portal Errors Fail Safe:** Any unparseable markup, network disconnect, or unexpected HTTP response is classified as `portal_error` with diagnostic logging.

---

## 8. How PDF Authenticity is Checked

### Decision
The binary response from `previewECWisePdf` is validated before being served as a PDF.

### Rationale
1. **Magic Signature:** The binary content must begin with the standard `%PDF-` signature in its header.
2. **Detecting Disguised Errors:** Portal frameworks often return HTTP 200 with an HTML error page body when an internal exception occurs during PDF generation. The PDF client inspects the first 1024 bytes and rejects HTML or non-PDF bytes, raising `PdfUnavailableError`.
3. **Safe Streaming:** PDFs are streamed with `Content-Disposition: attachment; filename="TNREGINET_EC_{session_id}.pdf"`.

---

## 9. How Session Expiration is Handled

### Decision
Sessions have a configurable TTL (default: 900 seconds / 15 minutes) and are cleaned up by both active access checks and a periodic background task.

### Rationale
1. **Active Check:** Any request with an expired session ID immediately invalidates the session, closes its HTTP client, and returns HTTP 404 with `SessionExpiredError`.
2. **Passive Background Worker:** A background task running on a configurable interval (default: 60s) scans and cleans up abandoned sessions to prevent memory leaks.
3. **Shutdown Hook:** During application shutdown, the lifespan manager calls `session_manager.close_all()` to ensure all open network sockets and resources are cleanly terminated.

---

## 10. Production Limitations & Future Scaling

| Current Single-Process Design | Production Multi-Worker Target |
|:---|:---|
| In-memory `SessionManager` | Distributed Redis store for session metadata & cookie state. |
| In-memory `asyncio.Lock` rate limiter | Distributed token-bucket or Redis-based rate limiter across worker pods. |
| Single Uvicorn worker process | Multi-worker Gunicorn/Uvicorn cluster behind a reverse proxy (e.g. NGINX). |
| Ephemeral location caching | Centralized Redis cache with TTL for static Zone/District/SRO hierarchies. |
| Synchronous human CAPTCHA entry | WebSocket or SSE notifications to push CAPTCHA challenges to connected clients. |

---

## 11. Multilingual Support Strategy (English Default & Tamil)

### Decision
The service defaults all location queries, demonstrations, and results to **English** (`lang="en"`) while providing first-class toggle support for **Tamil** (`lang="ta"`).

### Rationale
1. **Accessibility & Usability:** Users and developers inspecting the API and demonstration UI can immediately navigate Zones (e.g. *Coimbatore*, *Chennai*), Districts (*Coimbatore South*), and SROs (*Madukkarai*) in English without requiring knowledge of Tamil script.
2. **Native Portal Support:** Reverse-engineering confirmed that TNREGINET natively supports English translations when passed `UserLocaleID=en`. No machine translation is needed; the portal returns verified English names.
3. **Cache Partitioning:** In-memory location caches partition keys by both identifier and language (e.g., `2:en` vs `2:ta`). This prevents language collisions or returning Tamil text to a client requesting English.
4. **Demonstration UI Integration:** The UI includes an instant language switcher in the header that updates all text labels and dynamically refreshes dropdowns in the selected language.

---

## 12. Multilingual Location Name Normalization (Tamil Nadu 38-Zone Coverage)

### Context
TNREGINET renders its initial `openEncumbranceCertSearch` HTML using JSP server templates where the 38 revenue zone `<select name="cmb_Zone">` options are hardcoded in Tamil (`கோயம்புத்தூர்`, `சென்னை`, `மதுரை`, etc.) regardless of whether `UserLocaleID=en` is supplied. However, users require full English navigation when English is selected, and native Tamil navigation when Tamil is selected.

### Decision
Implement automated bidirectional translation for all 38 Tamil Nadu registration zones and districts in `app/portal/locations.py` and mirror in `frontend/app.js`.
- In English mode (`lang=en`), Tamil zone and district labels are converted to standard English (e.g. `கோயம்புத்தூர்` → `Coimbatore`, `சென்னை` → `Chennai`).
- In Tamil mode (`lang=ta`), native Tamil text is preserved intact.
- Both language views are independently cached in memory by language key (`(zone_id, lang)`), preventing cross-language cache collisions.

---

## 13. Search Submission Payload Transmission via HTTP POST Body

### Context
TNREGINET's client JavaScript calls an internal wrapper `updateContainer(url, "", 'searchComponentSection')`. When serialized as a URL query string, the search request exceeds 1,000 characters, causing Tomcat's security filter or query buffer to reject the request and redirect to a generic Tomcat `Error Page` ("Sorry! An error has occurred").

### Decision
Transmit only short, standard routing parameters (`requestType`, `actionVal`, `portal`, `_csrf`) on the URL while packaging all form inputs (survey numbers, village ID, SRO ID, dates, CAPTCHA, hidden form tokens) directly in the `application/x-www-form-urlencoded` HTTP POST body. Empirical verification proved that Tomcat parses this body completely and routes to the real EC search engine without triggering URL buffer overflows.


