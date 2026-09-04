from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os

from core.database import init_db
from services.scheduler import start_scheduler, stop_scheduler
from api import reviews, analysis, outputs, approval, auth

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize the database on startup
    await init_db()
    # Start background scheduler
    start_scheduler()
    
    yield
    
    # Cleanup on shutdown
    stop_scheduler()

app = FastAPI(title="Groww Intelligence API", lifespan=lifespan)

# CORS middleware
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
allow_origins = [url.strip() for url in frontend_url.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(reviews.router)
app.include_router(analysis.router)
app.include_router(outputs.router)
app.include_router(approval.router)
app.include_router(auth.router)

@app.get("/api/config")
async def get_config():
    from core.config import settings
    return {
        "app_name": settings.app_name,
        "package_name": settings.package_name,
        "review_lookback_days": settings.review_lookback_days
    }
