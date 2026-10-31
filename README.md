# Ground Truth — TNREGINET Encumbrance Certificate Retrieval Service

A robust, maintainable Python service to retrieve Encumbrance Certificate (EC) data and original PDFs from the Tamil Nadu Registration Department's [TNREGINET portal](https://tnreginet.gov.in/portal/).

Built for the Backend Engineer position take-home assignment at **IPPO RE Technologies LLP**.

---

## Table of Contents
- [1. Overview](#1-overview)
- [2. Technology Stack](#2-technology-stack)
- [3. Architecture & Key Features](#3-architecture--key-features)
- [4. Prerequisites](#4-prerequisites)
- [5. Installation & Setup](#5-installation--setup)
- [6. One-Command Startup](#6-one-command-startup)
- [7. Interactive API Documentation & Demonstration UI](#7-interactive-api-documentation--demonstration-ui)
- [8. API Reference & Workflow](#8-api-reference--workflow)
  - [8.1 Health Endpoint](#81-health-endpoint)
  - [8.2 Dynamic Location Endpoints](#82-dynamic-location-endpoints)
  - [8.3 Start Search Session (Step 1)](#83-start-search-session-step-1)
  - [8.4 Retrieve CAPTCHA Image](#84-retrieve-captcha-image)
  - [8.5 Submit Search (Step 2)](#85-submit-search-step-2)
  - [8.6 Original PDF Download](#86-original-pdf-download)
- [9. Automated Offline Tests](#9-automated-offline-tests)
- [10. Live Verification Report](#10-live-verification-report)
- [11. Security Considerations](#11-security-considerations)
- [12. Limitations & Production Readiness](#12-limitations--production-readiness)

---

## 1. Overview

An Encumbrance Certificate (EC) contains the transaction history (sales, mortgages, leases, partitions) registered on a property over a specified time window.

This service reverse-engineers the stateful TNREGINET Java/JSP portal workflow into an intuitive, modern REST API:
- **Dynamic location hierarchy**: Zones, Districts, SROs, Villages, Wards, and Blocks are discovered from the real portal without hardcoding.
- **Human CAPTCHA entry**: Real CAPTCHA images are retrieved from the portal and presented to a human; no bypasses, OCR, or third-party CAPTCHA solving services.
- **Process-wide Rate Limiter**: Maximum 1 outbound request every 2.0 seconds with serialized execution (`asyncio.Lock`).
- **Structured JSON Results**: Table rows, consideration amounts (exact `Decimal`), market values, parties (executants/claimants), and survey numbers are cleanly extracted while preserving Tamil and English script.
- **Original PDF Retrieval**: The official signed EC PDF is retrieved, validated with `%PDF-` signature verification, and streamed to the user.
- **Truthful Status Classification**: Explicitly distinguishes between `found`, `no_records`, `wrong_captcha`, `session_expired`, `too_many_records`, and `portal_error`.

---

## 2. Technology Stack

- **Language:** Python 3.12+ (tested on Python 3.14)
- **Web Framework:** FastAPI (Asynchronous ASGI)
- **ASGI Server:** Uvicorn (Single worker for process-wide rate limiting)
- **HTTP Client:** HTTPX (`AsyncClient`) with isolated cookie jars and connection pooling
- **HTML/XML Parser:** BeautifulSoup4
- **Data Validation & Schemas:** Pydantic v2
- **Testing:** pytest, pytest-asyncio (100% offline suite)
- **Demonstration UI:** Vanilla HTML5, CSS3, and JavaScript (served statically by FastAPI)

---

## 3. Architecture & Key Features

```
ground-truth-ec/
├── app/
│   ├── api/             # FastAPI routers (health, locations, ec)
│   ├── schemas/         # Pydantic request & response models
│   ├── services/        # Orchestration layer (location_service, ec_service)
│   ├── portal/          # TNREGINET client, rate limiter, session manager, parser, pdf
│   ├── config.py        # Centralized settings & environment variables
│   ├── errors.py        # Domain exceptions and JSON error handlers
│   └── main.py          # ASGI application entrypoint & static mount
├── frontend/            # Optional demonstration UI (HTML/CSS/JS)
├── tests/               # 100% offline automated tests with sanitized fixtures
│   └── fixtures/        # HTML and XML mock responses
├── DECISIONS.md         # Detailed architectural decisions log
├── FINDINGS.md          # Reverse-engineering and portal findings report
├── requirements.txt     # Locked production dependencies
├── run.sh               # Single-command executable startup script
└── .env.example         # Example environment settings
```

---

## 4. Prerequisites

- macOS or Linux
- Python 3.12 or higher (`python3 --version`)
- Standard internet connection (for live portal interactions; test suite runs completely offline)

---

## 5. Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone <repo-url>
   cd groundtruthEC
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **(Optional) Configure environment variables:**
   ```bash
   cp .env.example .env
   ```

---

## 6. One-Command Startup

Start the service with the executable startup script:

```bash
./run.sh
```

Alternatively, run manually:
```bash
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1
```

*Note: The local service runs with `--workers 1` to ensure the process-wide 2.0-second rate limiter is strictly enforced across all outbound requests.*

---

## 7. Interactive API Documentation & Demonstration UI

Once started:
- **Interactive Swagger Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **OpenAPI ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Demonstration UI:** [http://localhost:8000/](http://localhost:8000/)
  - Features an instant **Language Switcher** in the header (**English** by default, with **Tamil** toggle).
  - Automatically loads and populates location dropdowns in the selected language.
  - Updates all interface labels, prompts, status messages, and table headers dynamically.

---

## 8. API Reference & Workflow

### 8.1 Health Endpoint
```http
GET /health
```
**Response (200 OK):**
```json
{
  "status": "healthy",
  "service": "ground-truth-ec",
  "timestamp": "2026-10-30T13:30:00.000000Z",
  "version": "1.0.0"
}
```

---

### 8.2 Dynamic Location Endpoints

All location endpoints accept an optional `lang` query parameter (`en` for English [default], or `ta` for Tamil). In-memory caching isolates cache entries by language (`{id}:{lang}`).

#### 1. List All Registration Zones
```http
GET /locations/zones?lang=en
```
**Response (200 OK):**
```json
{
  "status": "success",
  "data": [
    { "id": "2", "name": "Coimbatore" },
    { "id": "1", "name": "Chennai" },
    { "id": "4", "name": "Madurai" }
  ]
}
```
*(When queried with `?lang=ta`, returns Tamil names: `{"id": "2", "name": "கோயம்புத்தூர்"}`)*

#### 2. List Districts under a Zone
```http
GET /locations/districts?zone_id=2&lang=en
```
**Response (200 OK):**
```json
{
  "status": "success",
  "data": [
    { "id": "50006", "name": "Coimbatore South" },
    { "id": "20006", "name": "Coimbatore North" }
  ]
}
```

#### 3. List SROs under a District
```http
GET /locations/sros?district_id=50006&lang=en
```
**Response (200 OK):**
```json
{
  "status": "success",
  "data": [
    { "id": "20120:1", "name": "Madukkarai" },
    { "id": "20117:1", "name": "Singanallur" }
  ]
}
```

#### 4. List Villages under an SRO
```http
GET /locations/villages?sro_id=20120:1&lang=en
```
**Response (200 OK):**
```json
{
  "status": "success",
  "data": [
    { "id": "2739", "name": "Madukkarai" },
    { "id": "2740", "name": "Ettimadai" }
  ]
}
```

---

### 8.3 Start Search Session (Step 1)

Initiates an isolated session on the portal, traverses the combo states, and fetches the real CAPTCHA image. Accepts optional `"lang": "en"` (default) or `"ta"`.

#### Mode A: Survey Number Search
```http
POST /ec/sessions
Content-Type: application/json

{
  "search_mode": "survey_number",
  "lang": "en",
  "zone_id": "2",
  "district_id": "50006",
  "sro_id": "20120:1",
  "village_id": "2739",
  "survey_number": "999",
  "subdivision_number": "1A",
  "start_date": "01/01/2010",
  "end_date": "31/12/2010"
}
```

#### Mode B: Town Ward / Block Search
```http
POST /ec/sessions
Content-Type: application/json

{
  "search_mode": "ward_block",
  "zone_id": "2",
  "district_id": "50006",
  "sro_id": "20120:1",
  "village_id": "2739",
  "town_code": "T01",
  "ward_code": "W05",
  "block_code": "B02",
  "start_date": "01/01/2010",
  "end_date": "31/12/2010"
}
```

**Response (200 OK):**
```json
{
  "status": "captcha_required",
  "session_id": "gA4yF7V9xP_rT5mK9sW2...",
  "captcha_image_url": "/ec/sessions/gA4yF7V9xP_rT5mK9sW2.../captcha",
  "expires_at": "2026-10-30T13:45:00+00:00"
}
```

---

### 8.4 Retrieve CAPTCHA Image

Retrieves the genuine binary CAPTCHA image for human inspection.

```http
GET /ec/sessions/{session_id}/captcha
```
**Response:** Binary stream with `Content-Type: image/png`.

---

### 8.5 Submit Search (Step 2)

Submits the human-entered CAPTCHA characters and executes the search query across the portal session.

```http
POST /ec/sessions/{session_id}/search
Content-Type: application/json

{
  "captcha_text": "M47KY"
}
```

**Response (200 OK) — Records Found:**
```json
{
  "status": "found",
  "records": [
    {
      "document_number": "1234/2010",
      "document_year": 2010,
      "registration_date": "15/06/2010",
      "document_type": "கிரைய ஆவணம் (Sale Deed)",
      "executants": ["முருகன் (Murugan)"],
      "claimants": ["கந்தன் (Kandhan)"],
      "consideration_value": 250000.00,
      "market_value": 300000.00,
      "survey_numbers": ["999", "1A"]
    }
  ],
  "total_records": 1,
  "message": null,
  "pdf_available": true,
  "pdf_url": "/ec/sessions/{session_id}/pdf"
}
```

**Response (200 OK) — No Records Found:**
```json
{
  "status": "no_records",
  "records": [],
  "total_records": 0,
  "message": "No transactions registered during the selected period",
  "pdf_available": false,
  "pdf_url": null
}
```

**Response (200 OK) — Wrong CAPTCHA:**
```json
{
  "status": "wrong_captcha",
  "records": [],
  "total_records": 0,
  "message": "Invalid CAPTCHA code: தயவுசெய்து சரியான காப்புக் குறியீட்டினை உள்ளிடவும்",
  "pdf_available": false,
  "pdf_url": null
}
```

---

### 8.6 Original PDF Download

Downloads the authentic signed EC PDF file produced by the portal.

```http
GET /ec/sessions/{session_id}/pdf
```
**Response:** Binary PDF download (`Content-Type: application/pdf`, `Content-Disposition: attachment; filename="TNREGINET_EC_{session_id}.pdf"`).

---

## 9. Automated Offline Tests

The repository includes a comprehensive, 100% offline automated test suite using `pytest` and `pytest-asyncio`.

Run tests:
```bash
source .venv/bin/activate
pytest tests/ -v
```

### Coverage Areas:
- **`test_health.py`**: Validates health check response structure and timestamp.
- **`test_locations.py`**: XML and HTML `<select>` option parsing, placeholder filtering, and Tamil text preservation.
- **`test_parser.py`**: Status classification (`found`, `no_records`, `wrong_captcha`, `session_expired`, `too_many_records`, `portal_error`), currency `Decimal` parsing, year extraction, multiple records, and PDF parameter extraction.
- **`test_ec.py`**: Search input validation, date range order validation, year >= 1900 boundary, mode requirements, and process-wide rate limiter timing.
- **`test_pdf.py`**: Canonical `%PDF-` signature check, rejection of disguised HTML errors, and safe streaming.
- **`test_sessions.py`**: Cryptographic session ID generation, TTL expiration, invalidation, and background cleanup.
- **`test_api.py`**: Mocked end-to-end API integration tests for all workflows.

---

## 10. Live Verification Report

| Test Case | Parameters | Verified Portal Evidence | Outcome Status |
|:---|:---|:---|:---|
| **Primary Test Case** | District: Coimbatore South (`50006`)<br>SRO: Madukkarai (`20120:1`)<br>Village: Madukkarai (`2739`)<br>Survey No: `999`<br>Year: `2010` (01/01/2010 – 31/12/2010) | Hierarchy resolved dynamically from live portal. Captcha retrieved (`SimpleCaptcha?ts`). Submitted search through portal state machine. Portal returned explicit `divNothingFound` (`தேடுதல் காலத்தில் எந்த ஆவணங்களும் பதிவு செய்யப்படவில்லை`). | **`no_records`** (Accurately classified; no fake records injected). |
| **Town Ward / Block Search** | District: Coimbatore South (`50006`)<br>SRO: Madukkarai (`20120:1`)<br>Village: Madukkarai (`2739`)<br>Mode: `ward_block` (`DOC_SEARCH=4`) | `openBlockWardWiseSearch` loaded. Town, ward, block combo chain resolved. Request verified against live portal. | **`verified`** (Properly routes and validates ward/block inputs). |
| **Additional Survey Search** | SRO: Madukkarai (`20120:1`)<br>Village: Ettimadai (`2740`)<br>Survey No: `123`<br>Date: `01/01/2015` – `31/12/2015` | Location resolved from dynamic list. Form submission executed with live session. | **`no_records`** (Accurately verified against portal response). |

*Note: In compliance with the assignment rules, results are strictly based on live portal responses. No fake EC documents or mock records are committed.*

---

## 11. Security Considerations

1. **No Hardcoded Secrets:** No secrets, credentials, or personal tokens are committed.
2. **Session Isolation:** Portal cookies and internal tokens (`authToken`, `_csrf`) are kept server-side and never leaked to API clients.
3. **Data Minimization:** No personal data, citizen names, or email delivery forms (`feedBackForm`) are stored or submitted.
4. **Rate Limiting:** A process-wide 2.0-second rate limiter prevents overwhelming external infrastructure.

---

## 12. Limitations & Production Readiness

- **Single Worker Limitation:** In this local implementation, sessions and rate limiting are managed process-internally (`asyncio.Lock` and in-memory dictionary). In a multi-worker production environment, session state and rate limiting must be offloaded to a distributed store like **Redis**.
- **Human CAPTCHA:** Because CAPTCHAs must be solved by a human, searches are asynchronous two-step workflows. For high-volume production use, integration with official government API access (if granted to authorized entities) is recommended over web scraping.

