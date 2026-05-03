from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone as dt_timezone

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from apps.cofhe.models import Claim, PayrollRun, RunAllocation
from apps.cofhe.services.funding import ensure_run_snapshot

log = logging.getLogger(__name__)


CLAIM_DONE_STATUSES = {
    "finalized_success",
    "cancelled",
    "finalized_revert",
}


def _frontend_url(path: str) -> str:
    base = getattr(settings, "FRONTEND_BASE_URL", "http://localhost:5173").rstrip("/")
    return f"{base}{path}"


def _deadline_dt(run: PayrollRun):
    try:
        return datetime.fromtimestamp(int(run.deadline_u64), tz=dt_timezone.utc)
    except Exception:
        return None


def _display_name(alloc: RunAllocation) -> str:
    return (alloc.employee_name or "there").strip()


def _send_email(to_email: str, subject: str, body: str) -> bool:
    to_email = (to_email or "").strip().lower()

    if not to_email:
        return False

    try:
        sent = send_mail(
            subject=subject,
            message=body,
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "Zalary <noreply@zalary.app>"),
            recipient_list=[to_email],
            fail_silently=False,
        )

        return sent > 0
    except Exception as exc:
        log.exception("Failed to send notification email to %s: %s", to_email, exc)
        return False


def _claim_for_alloc(alloc: RunAllocation) -> Claim | None:
    return (
        Claim.objects
        .filter(run=alloc.run, employee_address__iexact=alloc.employee_address)
        .first()
    )


def _claim_is_done(alloc: RunAllocation) -> bool:
    claim = _claim_for_alloc(alloc)

    if not claim:
        return False

    return claim.status in CLAIM_DONE_STATUSES


def send_claim_invitations_for_run(run_id: int) -> dict:
    """
    Sends claim invitation emails when a payroll run becomes active.
    Idempotent: each RunAllocation has claim_invitation_sent_at.
    """
    try:
        run = (
            PayrollRun.objects
            .select_related("template")
            .get(id=run_id)
        )
    except PayrollRun.DoesNotExist:
        return {"run_id": run_id, "sent": 0, "skipped": 0, "error": "run_not_found"}

    if run.status != "active":
        return {"run_id": run.id, "sent": 0, "skipped": 0, "error": "run_not_active"}

    ensure_run_snapshot(run)

    claim_url = _frontend_url("/verify/employee")
    deadline = _deadline_dt(run)
    deadline_text = deadline.astimezone(timezone.get_current_timezone()).strftime("%B %d, %Y %I:%M %p") if deadline else "the claim deadline"

    sent = 0
    skipped = 0
    now = timezone.now()

    allocations = RunAllocation.objects.select_related("run", "run__template").filter(run=run)

    for alloc in allocations:
        if not alloc.employee_email:
            skipped += 1
            continue

        if alloc.claim_invitation_sent_at:
            skipped += 1
            continue

        if _claim_is_done(alloc):
            skipped += 1
            continue

        subject = "You have a private salary claim on Zalary"

        body = f"""Hello {_display_name(alloc)},

You have a private salary claim waiting on Zalary.

Payroll: {run.template.title or "Payroll Run"}
Claim deadline: {deadline_text}

Claim your salary here:
{claim_url}

Use the wallet linked to this payroll:
{alloc.employee_address}

Your salary details remain protected and are only available through your verified wallet.

— Zalary
"""

        if _send_email(alloc.employee_email, subject, body):
            alloc.claim_invitation_sent_at = now
            alloc.save(update_fields=["claim_invitation_sent_at"])
            sent += 1
        else:
            skipped += 1

    return {"run_id": run.id, "sent": sent, "skipped": skipped}


def send_deadline_reminders() -> dict:
    """
    Sends one 3-day and one 24-hour reminder before payroll claim deadline.
    Intended to run periodically via Celery Beat.
    """
    now = timezone.now()
    sent = 0
    skipped = 0

    runs = PayrollRun.objects.select_related("template").filter(status="active")

    for run in runs:
        deadline = _deadline_dt(run)

        if not deadline:
            skipped += 1
            continue

        if deadline <= now:
            skipped += 1
            continue

        remaining = deadline - now

        allocations = RunAllocation.objects.select_related("run", "run__template").filter(run=run)

        for alloc in allocations:
            if not alloc.employee_email:
                skipped += 1
                continue

            if _claim_is_done(alloc):
                skipped += 1
                continue

            deadline_text = deadline.astimezone(timezone.get_current_timezone()).strftime("%B %d, %Y %I:%M %p")
            claim_url = _frontend_url("/verify/employee")

            if remaining <= timedelta(hours=24):
                if alloc.deadline_24h_reminder_sent_at:
                    skipped += 1
                    continue

                subject = "Reminder: your Zalary salary claim expires soon"

                body = f"""Hello {_display_name(alloc)},

Your private salary claim on Zalary expires soon.

Payroll: {run.template.title or "Payroll Run"}
Claim deadline: {deadline_text}

Complete your claim here:
{claim_url}

— Zalary
"""

                if _send_email(alloc.employee_email, subject, body):
                    alloc.deadline_24h_reminder_sent_at = now
                    alloc.save(update_fields=["deadline_24h_reminder_sent_at"])
                    sent += 1
                else:
                    skipped += 1

            elif remaining <= timedelta(days=3):
                if alloc.deadline_3d_reminder_sent_at:
                    skipped += 1
                    continue

                subject = "Reminder: you have a private salary claim on Zalary"

                body = f"""Hello {_display_name(alloc)},

You still have a private salary claim waiting on Zalary.

Payroll: {run.template.title or "Payroll Run"}
Claim deadline: {deadline_text}

Claim your salary here:
{claim_url}

— Zalary
"""

                if _send_email(alloc.employee_email, subject, body):
                    alloc.deadline_3d_reminder_sent_at = now
                    alloc.save(update_fields=["deadline_3d_reminder_sent_at"])
                    sent += 1
                else:
                    skipped += 1

    return {"sent": sent, "skipped": skipped}


def send_claim_completion_reminders() -> dict:
    """
    Sends one reminder when a claim was started but not completed.
    """
    sent = 0
    skipped = 0
    now = timezone.now()
    claim_url = _frontend_url("/verify/employee")

    claims = (
        Claim.objects
        .select_related("run", "run__template")
        .filter(status__in=["request_broadcasted", "pending_ready"])
    )

    for claim in claims:
        alloc = (
            RunAllocation.objects
            .select_related("run", "run__template")
            .filter(run=claim.run, employee_address__iexact=claim.employee_address)
            .first()
        )

        if not alloc or not alloc.employee_email:
            skipped += 1
            continue

        if alloc.claim_completion_reminder_sent_at:
            skipped += 1
            continue

        subject = "Complete your Zalary salary claim"

        body = f"""Hello {_display_name(alloc)},

You started a private salary claim on Zalary, but it is not completed yet.

Payroll: {claim.run.template.title or "Payroll Run"}

Continue here:
{claim_url}

— Zalary
"""

        if _send_email(alloc.employee_email, subject, body):
            alloc.claim_completion_reminder_sent_at = now
            alloc.save(update_fields=["claim_completion_reminder_sent_at"])
            sent += 1
        else:
            skipped += 1

    return {"sent": sent, "skipped": skipped}