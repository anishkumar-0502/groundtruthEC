"""Ground Truth — TNREGINET Encumbrance Certificate Retrieval Service.

Main FastAPI application entry point with lifespan management, routes, and UI mounting.
"""

import asyncio
from contextlib import asynccontextmanager
import logging
from pathlib import Path
import re
from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from app.api import ec, health, locations
from app.config import settings
from app.errors import GroundTruthError, ground_truth_error_handler
from app.portal.sessions import session_manager
from app.services.location_service import location_service

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("ground_truth.main")


async def periodic_session_cleanup():
    """Background task to remove expired sessions and release resources."""
    while True:
        try:
            await asyncio.sleep(settings.session_cleanup_interval_seconds)
            await session_manager.cleanup_expired()
        except asyncio.CancelledError:
            break
        except Exception as exc:
            logger.error(f"Error during periodic session cleanup: {exc}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management for startup and graceful shutdown."""
    logger.info("Starting Ground Truth EC Retrieval Service...")
    cleanup_task = asyncio.create_task(periodic_session_cleanup())

    yield

    logger.info("Shutting down Ground Truth service, releasing resources...")
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass

    await location_service.close()
    await session_manager.close_all()
    logger.info("Shutdown complete.")


app = FastAPI(
    title="Ground Truth — TNREGINET EC Retrieval Service",
    description=(
        "Production-grade service to retrieve Encumbrance Certificate (EC) "
        "information from the Tamil Nadu Registration Department's TNREGINET portal."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS Middleware (allows local tools / browsers)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register custom domain error handlers
app.add_exception_handler(GroundTruthError, ground_truth_error_handler)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Format Pydantic 422 validation errors into clean, human-readable messages."""
    errors = []
    for err in exc.errors():
        msg = err.get("msg", "Validation error")
        msg = re.sub(r"^Value error,\s*", "", msg, flags=re.IGNORECASE)
        loc = err.get("loc", [])
        field = loc[-1] if loc else "input"
        errors.append(f"{field}: {msg}")
    error_summary = "; ".join(errors)
    return JSONResponse(
        status_code=422,
        content={"status": "validation_error", "message": error_summary, "detail": jsonable_encoder(exc.errors())},
    )

# Include API routers
app.include_router(health.router)
app.include_router(locations.router)
app.include_router(ec.router)

# Serve Frontend Demonstration UI
frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")

    @app.api_route("/", methods=["GET", "HEAD"], tags=["Demonstration UI"])
    async def serve_ui_root():
        index_file = frontend_dir / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        return {"message": "Ground Truth EC API is running. UI not found."}
