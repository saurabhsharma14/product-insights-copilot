from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
import uuid
import datetime
import logging
from typing import Dict, Any

from core.database import get_db_connection
from core.config import settings
from services.review_scraper import GooglePlayScraperProvider
from services.review_cleaner import ReviewCleaner
from models.review import ReviewRecord
from api.analysis import run_analysis_pipeline

router = APIRouter(prefix="/api/reviews", tags=["reviews"])
logger = logging.getLogger(__name__)

async def run_autonomous_pipeline():
    """
    Autonomous pipeline function that fetches reviews and then triggers
    the analysis pipeline. Designed to be run by a background scheduler.
    """
    batch_id = str(uuid.uuid4())
    logger.info(f"Starting autonomous pipeline for batch {batch_id}")
    
    conn = await get_db_connection()
    try:
        await conn.execute("INSERT INTO analysis_runs (batch_id, status) VALUES ($1, $2)", batch_id, 'running')
    except Exception as e:
        await conn.close()
        logger.error(f"Database error on autonomous startup: {e}")
        return
        
    provider = GooglePlayScraperProvider()
    cleaner = ReviewCleaner()
    
    end_date = datetime.datetime.now(datetime.timezone.utc)
    start_date = end_date - datetime.timedelta(days=settings.review_lookback_days)
    
    try:
        raw_reviews = await provider.get_reviews(settings.package_name, start_date, end_date)
        if not raw_reviews:
            logger.warning("No reviews found during autonomous fetch.")
            await conn.execute("UPDATE analysis_runs SET status='failed' WHERE batch_id=$1", batch_id)
            await conn.close()
            return
    except Exception as e:
        await conn.execute("UPDATE analysis_runs SET status='failed' WHERE batch_id=$1", batch_id)
        await conn.close()
        logger.error(f"Scraper error: {str(e)}")
        return
        
    cleaned_reviews, stats = cleaner.clean(raw_reviews)
    
    # Cap the number of reviews to prevent hitting LLM token limits
    MAX_REVIEWS = 50
    if len(cleaned_reviews) > MAX_REVIEWS:
        logger.info(f"Capping reviews at {MAX_REVIEWS} to avoid LLM limits.")
        cleaned_reviews = cleaned_reviews[:MAX_REVIEWS]
    
    if len(cleaned_reviews) == 0:
        await conn.execute("UPDATE analysis_runs SET status='failed' WHERE batch_id=$1", batch_id)
        await conn.close()
        logger.warning("All retrieved reviews were filtered out.")
        return
        
    avg_rating = sum(r.rating for r in cleaned_reviews) / len(cleaned_reviews)
    
    try:
        for r in cleaned_reviews:
            await conn.execute('''
                INSERT INTO reviews (review_id, review_text, rating, review_date, app_version, developer_reply, source, source_url, batch_id)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ON CONFLICT (review_id) DO NOTHING
            ''', r.review_id, r.review_text, r.rating, r.review_date, r.app_version, r.developer_reply, r.source, r.source_url, batch_id)
            
        await conn.execute('''
            UPDATE analysis_runs 
            SET status='completed', review_count=$1, review_period_start=$2, review_period_end=$3, avg_rating=$4
            WHERE batch_id=$5
        ''', len(cleaned_reviews), start_date.isoformat(), end_date.isoformat(), avg_rating, batch_id)
    finally:
        await conn.close()
        
    logger.info(f"Autonomous fetch complete. Found {len(cleaned_reviews)} reviews. Starting analysis pipeline.")
    
    # Trigger the analysis pipeline directly
    await run_analysis_pipeline(batch_id)


class FetchResponse(BaseModel):
    batch_id: str
    stats: dict
    review_count: int
    review_period_start: str
    review_period_end: str
    avg_rating: float

@router.post("/fetch", response_model=FetchResponse)
async def fetch_reviews(background_tasks: BackgroundTasks):
    batch_id = str(uuid.uuid4())
    conn = await get_db_connection()
    try:
        await conn.execute("INSERT INTO analysis_runs (batch_id, status) VALUES ($1, $2)", batch_id, 'running')
    except Exception as e:
        await conn.close()
        raise HTTPException(status_code=500, detail="Database error")
        
    provider = GooglePlayScraperProvider()
    cleaner = ReviewCleaner()
    
    end_date = datetime.datetime.now(datetime.timezone.utc)
    start_date = end_date - datetime.timedelta(days=settings.review_lookback_days)
    
    try:
        raw_reviews = await provider.get_reviews(settings.package_name, start_date, end_date)
        if not raw_reviews:
            raise ValueError("No reviews found for the specified period. Verify the app package ID and try again.")
    except ValueError as e:
        await conn.execute("UPDATE analysis_runs SET status='failed' WHERE batch_id=$1", batch_id)
        await conn.close()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        await conn.execute("UPDATE analysis_runs SET status='failed' WHERE batch_id=$1", batch_id)
        await conn.close()
        logger.error(f"Scraper error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
        
    cleaned_reviews, stats = cleaner.clean(raw_reviews)
    
    # Cap the number of reviews to prevent hitting LLM token limits
    MAX_REVIEWS = 100
    if len(cleaned_reviews) > MAX_REVIEWS:
        logger.info(f"Capping reviews at {MAX_REVIEWS} to avoid LLM limits.")
        cleaned_reviews = cleaned_reviews[:MAX_REVIEWS]
    
    if len(cleaned_reviews) == 0:
        await conn.execute("UPDATE analysis_runs SET status='failed' WHERE batch_id=$1", batch_id)
        await conn.close()
        raise HTTPException(status_code=400, detail="All retrieved reviews were filtered out.")
        
    avg_rating = sum(r.rating for r in cleaned_reviews) / len(cleaned_reviews)
    
    try:
        for r in cleaned_reviews:
            await conn.execute('''
                INSERT INTO reviews (review_id, review_text, rating, review_date, app_version, developer_reply, source, source_url, batch_id)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ON CONFLICT (review_id) DO NOTHING
            ''', r.review_id, r.review_text, r.rating, r.review_date, r.app_version, r.developer_reply, r.source, r.source_url, batch_id)
            
        await conn.execute('''
            UPDATE analysis_runs 
            SET status='completed', review_count=$1, review_period_start=$2, review_period_end=$3, avg_rating=$4
            WHERE batch_id=$5
        ''', len(cleaned_reviews), start_date.isoformat(), end_date.isoformat(), avg_rating, batch_id)
    finally:
        await conn.close()
        
    return {
        "batch_id": batch_id,
        "stats": stats,
        "review_count": len(cleaned_reviews),
        "review_period_start": start_date.isoformat(),
        "review_period_end": end_date.isoformat(),
        "avg_rating": avg_rating
    }

@router.get("/status/{batch_id}")
async def get_fetch_status(batch_id: str):
    conn = await get_db_connection()
    try:
        row = await conn.fetchrow("SELECT status, review_count, review_period_start, review_period_end, avg_rating FROM analysis_runs WHERE batch_id=$1", batch_id)
        if not row:
            raise HTTPException(status_code=404, detail="Batch not found")
        return dict(row)
    finally:
        await conn.close()

@router.get("/{batch_id}")
async def get_reviews(batch_id: str):
    conn = await get_db_connection()
    try:
        rows = await conn.fetch("SELECT * FROM reviews WHERE batch_id=$1", batch_id)
        return [dict(r) for r in rows]
    finally:
        await conn.close()
