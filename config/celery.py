from __future__ import annotations

import os

from celery import Celery
from celery.schedules import crontab
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("zalary")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


# ─────────────────────────────────────────────────────────────────────────────
# Beat schedule — periodic tasks
# ─────────────────────────────────────────────────────────────────────────────
#
# In development / production, run Celery with:
#
#   celery -A config worker -l info
#   celery -A config beat -l info
#
# scheduler_tick:
#   Runs every minute.
#   Creates PayrollRun records for active templates whose next_run_at has passed.
#
# send_payroll_deadline_reminders:
#   Runs every 30 minutes.
#   Sends 3-day and 24-hour claim deadline reminders.
#
# send_pending_claim_completion_reminders:
#   Runs every hour.
#   Reminds employees who started a claim but have not completed it.
#
app.conf.beat_schedule = {
    "scheduler-tick-every-minute": {
        "task": "apps.cofhe.tasks.scheduler_tick",
        "schedule": crontab(minute="*"),
    },

    "payroll-deadline-reminders-every-30-minutes": {
        "task": "apps.cofhe.tasks.send_payroll_deadline_reminders",
        "schedule": crontab(minute="*/30"),
    },

    "pending-claim-completion-reminders-hourly": {
        "task": "apps.cofhe.tasks.send_pending_claim_completion_reminders",
        "schedule": crontab(minute=0),
    },
}

# Keep Celery aligned with Django settings.py.
# Your settings.py already defines CELERY_TIMEZONE from TIME_ZONE.
app.conf.timezone = getattr(settings, "CELERY_TIMEZONE", "Africa/Lagos")