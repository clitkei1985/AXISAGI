# core/scheduler.py

import os
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from typing import Callable, Dict
from datetime import datetime

logger = logging.getLogger("axis.scheduler")
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler("db/audit.log")
fh.setFormatter(logging.Formatter("%(asctime)s | SCHEDULER | %(levelname)s | %(message)s"))
logger.addHandler(fh)

_scheduler: BackgroundScheduler = None

def initialize_scheduler(app=None):
    """
    Initialize APScheduler with a persistent SQLite job store,
    schedule core jobs (memory re-index, backup, weekly summary).
    The 'app' can be used to call into memory/analytics modules by setting a global variable.
    """
    global _scheduler, _scheduler_app
    _scheduler_app = app  # store for job functions to reference

    if _scheduler and _scheduler.running:
        return _scheduler

    jobstore = {
        'default': SQLAlchemyJobStore(url=os.getenv("AXIS_SCHEDULER_DB", "sqlite:///db/jobs.sqlite"))
    }
    _scheduler = BackgroundScheduler(jobstores=jobstore, timezone="UTC")
    _scheduler.start()
    logger.info("BackgroundScheduler started with jobstore at db/jobs.sqlite")

    # Schedule re-index every day at 03:00 UTC
    _scheduler.add_job(
        func=reindex_memory,
        trigger='cron', hour=3, minute=0, id="daily_memory_reindex", replace_existing=True
    )

    # Schedule backup every day at 04:00 UTC
    _scheduler.add_job(
        func=backup_memory,
        trigger='cron', hour=4, minute=0, id="daily_memory_backup", replace_existing=True
    )

    # Schedule weekly summary every Monday at 05:00 UTC
    _scheduler.add_job(
        func=weekly_memory_summary,
        trigger='cron', day_of_week='mon', hour=5, minute=0, id="weekly_memory_summary", replace_existing=True
    )

    logger.info("Scheduled core jobs: reindex, backup, weekly summary")
    return _scheduler

def reindex_memory():
    """
    Called daily to force FAISS reindex (if needed).
    Uses the stored `_scheduler_app` to import and call the Memory module.
    """
    try:
        app = globals().get("_scheduler_app")
        if app:
            from modules.memory.memory import AIMemory
            # Replace "default-session" with appropriate session logic as needed
            mem = AIMemory("default-session")
            mem.reindex()
            logger.info("Memory reindex completed.")
    except Exception as e:
        logger.exception(f"Error during memory reindex: {e}")

def backup_memory():
    """
    Called daily to backup memory index.
    Uses the stored `_scheduler_app` to import and call BackupRestore.
    """
    try:
        app = globals().get("_scheduler_app")
        if app:
            from modules.memory.backup_restore import BackupRestore
            BackupRestore.backup_now()
            logger.info("Memory backup completed.")
    except Exception as e:
        logger.exception(f"Error during memory backup: {e}")

def weekly_memory_summary():
    """
    Called weekly to produce a summary of memory growth.
    Uses the stored `_scheduler_app` to import and call the Analytics module.
    """
    try:
        app = globals().get("_scheduler_app")
        if app:
            from modules.analytics_reporting.memory_reports import MemoryReports
            MemoryReports.generate_weekly_summary()
            logger.info("Weekly memory summary generated.")
    except Exception as e:
        logger.exception(f"Error during weekly memory summary: {e}")

def schedule_reminder(user_id: str, run_time: datetime, message: str, session_id: str = None):
    """
    Schedule a one-off reminder for a user.
    When triggered, it pushes a chat message into the appropriate session via the Chat Module.
    """
    def send_reminder():
        from modules.chat.handler import ChatHandler
        ChatHandler.push_system_message(
            session_id=session_id,
            text=f"Reminder for user {user_id}: {message}"
        )
        logger.info(f"Sent reminder to session {session_id}: {message}")

    job_id = f"reminder_{user_id}_{run_time.strftime('%Y%m%d%H%M%S')}"
    _scheduler.add_job(
        func=send_reminder,
        trigger='date',
        run_date=run_time,
        id=job_id,
        replace_existing=True
    )
    logger.info(f"Scheduled reminder job {job_id} at {run_time}")
    return job_id

def schedule_recurring(user_id: str, cron_expression: Dict[str, int], message: str, session_id: str = None):
    """
    Schedule a recurring reminder via a cron expression
    (e.g., {'hour':9,'minute':0,'day_of_week':'mon-fri'}).
    """
    job_id = f"recurring_{user_id}_{message}"
    def send_recurring():
        from modules.chat.handler import ChatHandler
        ChatHandler.push_system_message(
            session_id=session_id,
            text=f"Recurring Reminder for user {user_id}: {message}"
        )
        logger.info(f"Sent recurring reminder to session {session_id}: {message}")

    _scheduler.add_job(
        func=send_recurring,
        trigger='cron',
        id=job_id,
        replace_existing=True,
        **cron_expression
    )
    logger.info(f"Scheduled recurring job {job_id} with cron {cron_expression}")
    return job_id
