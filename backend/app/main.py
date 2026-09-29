from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.database import initialize_database
from app.routes import upload, analysis, incidents, reports, settings as settings_routes, evaluation, samples


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite database tables on startup
    initialize_database()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="TRACE AI: AI-powered log analysis and incident investigation platform",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register route modules under /api
app.include_router(upload.router, prefix=settings.API_V1_STR)
app.include_router(analysis.router, prefix=settings.API_V1_STR)
app.include_router(incidents.router, prefix=settings.API_V1_STR)
app.include_router(reports.router, prefix=settings.API_V1_STR)
app.include_router(settings_routes.router, prefix=settings.API_V1_STR)
app.include_router(evaluation.router, prefix=settings.API_V1_STR)
app.include_router(samples.router, prefix=settings.API_V1_STR)


@app.get("/")
def root():
    return {
        "service": "TRACE AI API",
        "status": "operational",
        "version": settings.VERSION,
        "docs_url": "/docs"
    }


@app.get("/api/health")
def healthcheck():
    return {
        "status": "healthy",
        "demo_mode": settings.DEMO_MODE,
        "jev_configured": bool(settings.JEV_API_KEY)
    }
