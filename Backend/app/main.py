from datetime import datetime, timezone
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy import text
from app.api.v1 import api_router
from app.core.config import settings
from app.core.db import engine

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description=(
        "Personalized Medicine Clinical Decision Support System (PM-CDSS) "
        "tailored for clinical workflows (e.g., Levy Mwanawasa Teaching Hospital, Zambia). "
        "Strict decision-support guidance only; never autonomously diagnoses or prescribes."
    ),
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
)

# Configure CORS for Vue 3 frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/docs", include_in_schema=False)
async def docs_redirect():
    return RedirectResponse(url=f"{settings.API_V1_STR}/docs")


@app.get("/redoc", include_in_schema=False)
async def redoc_redirect():
    return RedirectResponse(url=f"{settings.API_V1_STR}/redoc")


@app.get("/health", tags=["System Health"])
async def health_check():
    """Lightweight health check endpoint verifying database connectivity."""
    db_status = "unhealthy"
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
            db_status = "connected"
    except Exception as e:
        db_status = f"disconnected ({str(e)})"

    return {
        "status": "online",
        "institution": settings.INSTITUTION_NAME,
        "database": db_status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": settings.PROJECT_VERSION,
    }


# Include V1 API Router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Ensure fault-tolerant error responses for intermittent infrastructure
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An internal clinical system error occurred. Please try again or notify IT support.",
            "error_type": exc.__class__.__name__,
        },
    )
