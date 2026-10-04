from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import logger, log_event
from app.db.session import SessionLocal
from app.services.crawl_service import CrawlService

scheduler = AsyncIOScheduler(timezone="Asia/Ho_Chi_Minh")


async def scheduled_crawl_job():
    """
    Background job triggered by APScheduler at scheduled times.
    """
    log_event("scheduler_job_started", "Scheduled crawl cycle triggered.")
    db: Session = SessionLocal()
    try:
        service = CrawlService(db)
        if service.is_running():
            log_event("scheduler_job_skipped", "Crawl already running, skipping scheduled trigger.")
            return
        await service.execute_crawl(source="scheduled")
    except Exception as e:
        logger.error(f"Scheduled crawl job error: {e}")
    finally:
        db.close()


def setup_scheduler() -> AsyncIOScheduler:
    """
    Configures scheduler with times defined in settings.crawl_schedule.
    """
    times = [t.strip() for t in settings.crawl_schedule.split(",") if t.strip()]
    
    for time_str in times:
        try:
            parts = time_str.split(":")
            hour = int(parts[0])
            minute = int(parts[1]) if len(parts) > 1 else 0
            
            scheduler.add_job(
                scheduled_crawl_job,
                trigger=CronTrigger(hour=hour, minute=minute, timezone=scheduler.timezone),
                id=f"crawl_job_{hour:02d}_{minute:02d}",
                replace_existing=True,
            )
            log_event("scheduler_job_registered", f"Registered crawl job at {hour:02d}:{minute:02d}")
        except Exception as e:
            logger.warning(f"Failed to register crawl schedule time '{time_str}': {e}")
            
    return scheduler


def start_scheduler():
    if not scheduler.running:
        setup_scheduler()
        scheduler.start()
        log_event("scheduler_started", f"APScheduler started with schedule: {settings.crawl_schedule}")


def shutdown_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
        log_event("scheduler_stopped", "APScheduler stopped.")
