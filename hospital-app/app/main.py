"""
OpenCareOS - Main Application Entry Point
Apache License 2.0
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import logging
import time
import uuid

from app.core.config.settings import get_settings
from app.core.database import init_database, close_database
from app.core.exceptions import OpenCareException, open_care_exception_to_http
from app.api.routers import (
    auth_router,
    patients_router,
    encounters_router,
    documents_router,
    ai_router,
)

settings = get_settings()

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Templates
templates = Jinja2Templates(directory="app/templates")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    logger.info("Starting OpenCareOS...")
    await init_database()
    logger.info("OpenCareOS started successfully")

    yield

    # Shutdown
    logger.info("Shutting down OpenCareOS...")
    await close_database()
    logger.info("OpenCareOS shut down complete")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=settings.APP_DESCRIPTION,
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL] if not settings.DEBUG else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests."""
    request_id = str(uuid.uuid4())[:8]
    request.state.request_id = request_id

    start_time = time.time()
    logger.info(
        f"Request {request_id}: {request.method} {request.url.path} "
        f"from {request.client.host if request.client else 'unknown'}"
    )

    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        logger.info(
            f"Request {request_id}: {response.status_code} "
            f"({process_time:.3f}s)"
        )
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(process_time)
        return response
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(
            f"Request {request_id}: Error ({process_time:.3f}s) - {str(e)}"
        )
        raise


# Global exception handler
@app.exception_handler(OpenCareException)
async def open_care_exception_handler(request: Request, exc: OpenCareException):
    """Handle OpenCare exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.code,
            "message": exc.message,
            "details": exc.details,
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions."""
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "code": "INTERNAL_ERROR",
            "message": "An internal server error occurred",
            "details": {"error": str(exc)} if settings.DEBUG else {},
        },
    )


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    from datetime import datetime
    from app.core.database import get_database
    from app.models.base import HealthCheckResponse

    services = {}
    try:
        db = await get_database()
        await db.command("ping")
        services["database"] = "healthy"
    except Exception:
        services["database"] = "unhealthy"

    return HealthCheckResponse(
        status="healthy" if all(v == "healthy" for v in services.values()) else "degraded",
        version=settings.APP_VERSION,
        timestamp=datetime.utcnow(),
        services=services,
    )


# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include routers
app.include_router(auth_router)
app.include_router(patients_router)
app.include_router(encounters_router)
app.include_router(documents_router)
app.include_router(ai_router)


# Root endpoint - serve main page
@app.get("/", tags=["Root"])
async def root(request: Request):
    """Serve the main application page."""
    return templates.TemplateResponse(
        "base.html",
        {"request": request, "title": settings.APP_NAME},
    )


# Patient dashboard
@app.get("/patient/dashboard", tags=["Patient"])
async def patient_dashboard(request: Request):
    """Patient dashboard page."""
    return templates.TemplateResponse(
        "patient/dashboard.html",
        {"request": request, "title": "Patient Dashboard - OpenCareOS"},
    )


# Doctor dashboard
@app.get("/doctor/dashboard", tags=["Doctor"])
async def doctor_dashboard(request: Request):
    """Doctor dashboard page."""
    return templates.TemplateResponse(
        "doctor/dashboard.html",
        {"request": request, "title": "Doctor Dashboard - OpenCareOS"},
    )


# Chat page
@app.get("/chat", tags=["Chat"])
async def chat_page(request: Request):
    """AI chat page."""
    return templates.TemplateResponse(
        "chat/index.html",
        {"request": request, "title": "AI Assistant - OpenCareOS"},
    )


# Login page
@app.get("/login", tags=["Auth"])
async def login_page(request: Request):
    """Login page."""
    return templates.TemplateResponse(
        "auth/login.html",
        {"request": request, "title": "Login - OpenCareOS"},
    )


# Register page
@app.get("/register", tags=["Auth"])
async def register_page(request: Request):
    """Registration page."""
    return templates.TemplateResponse(
        "auth/register.html",
        {"request": request, "title": "Register - OpenCareOS"},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )