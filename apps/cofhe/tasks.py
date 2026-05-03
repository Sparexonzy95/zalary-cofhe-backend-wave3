"""
Zalary Wave 3 Celery task interface.
"""

from config.celery import app


@app.task
def scheduler_tick():
    return {"detail": "Public interface only."}


@app.task
def send_payroll_deadline_reminders():
    return {"detail": "Public interface only."}


@app.task
def send_pending_claim_completion_reminders():
    return {"detail": "Public interface only."}


@app.task
def sync_chain_transactions():
    return {"detail": "Public interface only."}
