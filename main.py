import asyncio
import logging
import os

from dotenv import load_dotenv
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
import pytz

from bot.telegram_handler import (
    handle_start,
    handle_help,
    handle_brief,
    handle_debrief,
    handle_patterns,
    handle_jobs,
    handle_cover,
    handle_profile,
    handle_clear,
    handle_message,
    handle_photo,
    send_reminder_brief,
)
from memory.store import get_upcoming_interviews
from memory.pattern_tracker import analyse_patterns, format_pattern_report

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

SGT = pytz.timezone("Asia/Singapore")

# Chat ID to send scheduled messages to.
# Set TELEGRAM_CHAT_ID in your .env to your personal chat ID (get it from @userinfobot).
TELEGRAM_CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID", "0"))


async def job_reminder_check(app: Application):
    """Hourly job: check for interviews within 24 hours and send reminder briefs."""
    if TELEGRAM_CHAT_ID == 0:
        logger.warning("TELEGRAM_CHAT_ID not set — skipping reminder check.")
        return

    upcoming = get_upcoming_interviews()
    for interview in upcoming:
        company = interview.get("company", "Unknown")
        role = interview.get("role", "Unknown")
        logger.info("Sending reminder brief for %s - %s", company, role)
        try:
            await send_reminder_brief(app, company, role, TELEGRAM_CHAT_ID)
        except Exception as e:
            logger.error("Failed to send reminder brief: %s", e)


async def weekly_pattern_report(app: Application):
    """Monday 8am SGT: send weekly pattern report."""
    if TELEGRAM_CHAT_ID == 0:
        logger.warning("TELEGRAM_CHAT_ID not set — skipping weekly report.")
        return

    analysis = analyse_patterns()
    report = format_pattern_report(analysis)
    header = "*Weekly Pattern Report* — Monday Check-in\n\n"
    try:
        await app.bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=header + report,
            parse_mode="Markdown",
        )
        logger.info("Weekly pattern report sent.")
    except Exception as e:
        logger.error("Failed to send weekly report: %s", e)


def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN is not set in .env")

    # Scheduler
    scheduler = AsyncIOScheduler(timezone=SGT)

    async def on_startup(application: Application):
        scheduler.add_job(
            job_reminder_check,
            trigger=IntervalTrigger(hours=1),
            args=[application],
            id="reminder_check",
            replace_existing=True,
        )
        scheduler.add_job(
            weekly_pattern_report,
            trigger=CronTrigger(day_of_week="mon", hour=8, minute=0, timezone=SGT),
            args=[application],
            id="weekly_report",
            replace_existing=True,
        )
        scheduler.start()
        logger.info("Scheduler started. InternBrief is running.")

    async def on_shutdown(application: Application):
        scheduler.shutdown()

    app = (
        Application.builder()
        .token(token)
        .post_init(on_startup)
        .post_shutdown(on_shutdown)
        .build()
    )

    # Command handlers
    app.add_handler(CommandHandler("start", handle_start))
    app.add_handler(CommandHandler("help", handle_help))
    app.add_handler(CommandHandler("brief", handle_brief))
    app.add_handler(CommandHandler("debrief", handle_debrief))
    app.add_handler(CommandHandler("patterns", handle_patterns))
    app.add_handler(CommandHandler("jobs", handle_jobs))
    app.add_handler(CommandHandler("cover", handle_cover))
    app.add_handler(CommandHandler("profile", handle_profile))
    app.add_handler(CommandHandler("clear", handle_clear))

    # Photo handler for interview invitation screenshots
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    # General message handler (also handles debrief step routing and question answers)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
