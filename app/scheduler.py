import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlmodel import Session, select

from .database import engine
from .models import Subscriber
from .services.giveaway_service import sync_giveaways, get_unsent_giveaways, mark_as_sent
from .services.email_service import send_daily_emails
from .services.settings_service import get_sync_interval, get_email_time
from .config import settings as env_settings

log = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()


async def sync_job() -> None:
    log.info("Scheduler: syncing giveaways")
    with Session(engine) as session:
        new = await sync_giveaways(session)
        log.info("Scheduler: sync done — %d new giveaway(s)", len(new))


async def email_job() -> None:
    log.info("Scheduler: starting email job")
    with Session(engine) as session:
        unsent = get_unsent_giveaways(session)
        if not unsent:
            log.info("Scheduler: no new giveaways, skipping email")
            return
        subscribers = session.exec(
            select(Subscriber).where(Subscriber.is_active == True)
        ).all()
        send_daily_emails(unsent, list(subscribers), env_settings.base_url)
        mark_as_sent(session, unsent)
        log.info(
            "Scheduler: sent %d giveaway(s) to %d subscriber(s)",
            len(unsent), len(subscribers),
        )


def reschedule_sync(interval_minutes: int) -> None:
    scheduler.reschedule_job(
        "sync_job",
        trigger=IntervalTrigger(minutes=interval_minutes),
    )
    log.info("Sync interval updated to %d minutes", interval_minutes)


def reschedule_email(hour: int, minute: int) -> None:
    scheduler.reschedule_job(
        "email_job",
        trigger=CronTrigger(hour=hour, minute=minute),
    )
    log.info("Email time updated to %02d:%02d UTC", hour, minute)


async def start_scheduler() -> None:
    with Session(engine) as session:
        interval = get_sync_interval(session)
        hour, minute = get_email_time(session)

    scheduler.add_job(
        sync_job,
        IntervalTrigger(minutes=interval),
        id="sync_job",
        replace_existing=True,
        misfire_grace_time=None,
        coalesce=True,
    )
    scheduler.add_job(
        email_job,
        CronTrigger(hour=hour, minute=minute),
        id="email_job",
        replace_existing=True,
        misfire_grace_time=None,
        coalesce=True,
    )

    scheduler.start()
    log.info(
        "Scheduler started — sync every %d min, email daily at %02d:%02d UTC",
        interval, hour, minute,
    )

    await sync_job()
