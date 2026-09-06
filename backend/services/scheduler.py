import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from api.reviews import run_autonomous_pipeline
from core.database import init_db

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = AsyncIOScheduler()

async def scheduled_task():
    """
    Wrapper task to run the autonomous pipeline inside the scheduler.
    The entire body is wrapped in try/except so that NO unhandled exception
    can ever propagate up and cause APScheduler to silently drop the job.
    """
    try:
        logger.info("Scheduler: Running autonomous 11:00 AM IST pipeline...")
        # Ensure DB is initialized before running the autonomous fetch
        await init_db()
        # Call the autonomous pipeline
        await run_autonomous_pipeline()
        logger.info("Scheduler: Autonomous pipeline completed successfully.")
    except Exception as e:
        # Log and swallow — the job must survive for the next scheduled run
        logger.error(f"Scheduler: Autonomous pipeline failed: {e}", exc_info=True)

def start_scheduler():
    """Starts the APScheduler with the daily 11:00 AM IST job."""
    if scheduler.running:
        logger.info("Scheduler already running, skipping start.")
        return

    # Run every day at 11:00 AM IST (Asia/Kolkata)
    trigger = CronTrigger(hour=11, minute=0, timezone="Asia/Kolkata")

    scheduler.add_job(
        scheduled_task,
        trigger=trigger,
        id="daily_autonomous_pipeline",
        name="Daily review fetch and analysis pipeline",
        replace_existing=True,
        misfire_grace_time=3600,  # 1 hour grace time if server was down at 11 AM
        coalesce=True,           # If multiple misfires, run only once on recovery
    )

    scheduler.start()
    logger.info("APScheduler started. Autonomous pipeline scheduled for 11:00 AM IST daily.")

def stop_scheduler():
    """Shuts down the APScheduler."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("APScheduler shut down.")
