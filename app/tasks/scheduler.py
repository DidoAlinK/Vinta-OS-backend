"""
Vinta School OS — APScheduler Setup
Initializes and manages the background task scheduler.
"""
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from app.tasks.cron_jobs import CRON_JOBS

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def init_scheduler(app):
    """
    Initialize APScheduler with all configured cron jobs.
    Called during application startup.
    """
    with app.app_context():
        for job_config in CRON_JOBS:
            job_id = job_config["id"]
            func = job_config["func"]
            trigger = job_config["trigger"]

            # Extract trigger-specific kwargs
            trigger_kwargs = {}
            for key in ("minutes", "hour", "minute", "day", "month", "day_of_week"):
                if key in job_config:
                    trigger_kwargs[key] = job_config[key]

            scheduler.add_job(
                func,
                trigger=trigger,
                id=job_id,
                replace_existing=True,
                **trigger_kwargs,
            )
            logger.info(f"Scheduled job: {job_id} — {job_config.get('description', '')}")

        scheduler.start()
        logger.info("APScheduler started")


def shutdown_scheduler():
    """Gracefully shut down the scheduler."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("APScheduler shut down")
