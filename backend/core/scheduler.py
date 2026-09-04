import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from api.reviews import run_autonomous_pipeline

logger = logging.getLogger(__name__)

# Single instance of the scheduler
scheduler = AsyncIOScheduler()

def start_scheduler():
    """
    Initializes and starts the background task scheduler.
    Adds the autonomous scraper job to run daily at 11 AM.
    """
    if scheduler.running:
        return
        
    # Schedule the autonomous pipeline daily at 11:00 AM
    scheduler.add_job(
        run_autonomous_pipeline,
        'cron',
        hour=11,
        minute=0,
        id='autonomous_daily_fetch',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("APScheduler started. Autonomous pipeline scheduled daily at 11:00 AM.")

def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()
        logger.info("APScheduler stopped.")
