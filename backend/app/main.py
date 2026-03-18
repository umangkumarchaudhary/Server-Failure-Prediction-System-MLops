"""PredictrAI Backend - Universal Predictive Maintenance API."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.services import get_automation_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    del app
    print(f"Starting PredictrAI API v{settings.VERSION}")
    automation_scheduler = get_automation_scheduler()
    await automation_scheduler.start()
    try:
        yield
    finally:
        await automation_scheduler.stop()
        print("Shutting down PredictrAI API")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Universal Predictive Maintenance SaaS API",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": settings.VERSION}
