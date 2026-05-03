from __future__ import annotations

from django.db import models
from apps.chains.models import Chain


# ─────────────────────────────────────────────────────────────────────────────
# Schedule
# ─────────────────────────────────────────────────────────────────────────────

class ScheduleConfig(models.Model):
    TYPE = [
        ("instant",  "instant"),
        ("daily",    "daily"),
        ("weekly",   "weekly"),
        ("monthly",  "monthly"),
        ("yearly",   "yearly"),
    ]
    type          = models.CharField(max_length=16, choices=TYPE)
    start_at      = models.DateTimeField()
    end_at        = models.DateTimeField(null=True, blank=True)
    hour          = models.PositiveSmallIntegerField(default=9)
    minute        = models.PositiveSmallIntegerField(default=0)
    weekday       = models.PositiveSmallIntegerField(null=True, blank=True)
    day_of_month  = models.PositiveSmallIntegerField(null=True, blank=True)
    month_of_year = models.PositiveSmallIntegerField(null=True, blank=True)


# ─────────────────────────────────────────────────────────────────────────────
# Payroll Template
# ─────────────────────────────────────────────────────────────────────────────

class PayrollTemplate(models.Model):
    STATUS = [
        ("draft",     "draft"),
        ("active",    "active"),
        ("paused",    "paused"),
        ("completed", "completed"),
    ]
    chain            = models.ForeignKey(Chain, on_delete=models.PROTECT)
    token_address    = models.CharField(max_length=42)
    schedule         = models.ForeignKey(ScheduleConfig, on_delete=models.PROTECT)

    title            = models.CharField(max_length=255, blank=True)
    description      = models.TextField(blank=True)
    employer_address = models.CharField(max_length=42, blank=True, default="")

    status       = models.CharField(max_length=16, choices=STATUS, default="draft")
    next_run_at  = models.DateTimeField(null=True, blank=True)
    last_run_at  = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["status", "next_run_at"]),
            models.Index(fields=["employer_address"]),
        ]


class TemplateEmployee(models.Model):
    template          = models.ForeignKey(PayrollTemplate, on_delete=models.CASCADE, related_name="employees")
    employee_address  = models.CharField(max_length=42)
    employee_name     = models.CharField(max_length=255, blank=True, default="")
    employee_email    = models.EmailField(blank=True, default="")
    amount_atomic     = models.BigIntegerField()
    is_active         = models.BooleanField(default=True)

    class Meta:
        unique_together = ("template", "employee_address")
        indexes = [
            models.Index(fields=["employee_address"]),
            models.Index(fields=["employee_email"]),
        ]


# ─────────────────────────────────────────────────────────────────────────────
# Payroll Run
# ─────────────────────────────────────────────────────────────────────────────

class PayrollRun(models.Model):
    STATUS = [
        ("scheduled",           "scheduled"),
        ("create_broadcasted",  "create_broadcasted"),
        ("created",             "created"),
        ("alloc_uploading",     "alloc_uploading"),
        ("alloc_uploaded",      "alloc_uploaded"),
        ("alloc_finalizing",    "alloc_finalizing"),
        ("alloc_finalized",     "alloc_finalized"),
        ("funding",             "funding"),
        ("funded",              "funded"),
        ("activating",          "activating"),
        ("active",              "active"),
        ("closed",              "closed"),
        ("cancelled",           "cancelled"),
        ("failed",              "failed"),
    ]
    template              = models.ForeignKey(PayrollTemplate, on_delete=models.CASCADE, related_name="runs")
    chain                 = models.ForeignKey(Chain, on_delete=models.PROTECT)

    run_at                = models.DateTimeField()
    deadline_u64          = models.BigIntegerField()
    employee_count_u32    = models.PositiveIntegerField()
    required_total_atomic = models.BigIntegerField(default=0)

    onchain_payroll_id    = models.BigIntegerField(null=True, blank=True)
    employer_address      = models.CharField(max_length=42, blank=True)

    status                = models.CharField(max_length=32, choices=STATUS, default="scheduled")
    last_error            = models.TextField(blank=True)

    create_tx_hash        = models.CharField(max_length=80, blank=True)
    fund_tx_hash          = models.CharField(max_length=66, blank=True, default="")
    activate_tx_hash      = models.CharField(max_length=66, blank=True, default="")

    funded_once_handle    = models.CharField(max_length=66, blank=True)
    funded_plaintext      = models.BooleanField(null=True, blank=True)
    funded_sig            = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("template", "run_at")
        indexes = [
            models.Index(fields=["status", "run_at"]),
            models.Index(fields=["onchain_payroll_id"]),
        ]


class RunAllocation(models.Model):
    """
    Snapshot of one employee's allocation for a specific run.

    CoFHE: amount_ciphertext_hex stores the InEuint64 struct serialised
    as a JSON hex string produced by the frontend SDK's encryptInputs().
    """
    run                   = models.ForeignKey(PayrollRun, on_delete=models.CASCADE, related_name="allocations")
    employee_address      = models.CharField(max_length=42)
    employee_name         = models.CharField(max_length=255, blank=True, default="")
    employee_email        = models.EmailField(blank=True, default="")
    amount_atomic         = models.BigIntegerField()
    amount_ciphertext_hex = models.TextField(blank=True)
    uploaded              = models.BooleanField(default=False)
    upload_tx_hash        = models.CharField(max_length=80, blank=True)

    claim_invitation_sent_at          = models.DateTimeField(null=True, blank=True)
    deadline_3d_reminder_sent_at      = models.DateTimeField(null=True, blank=True)
    deadline_24h_reminder_sent_at     = models.DateTimeField(null=True, blank=True)
    claim_completion_reminder_sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("run", "employee_address")
        indexes = [
            models.Index(fields=["employee_address"]),
            models.Index(fields=["employee_email"]),
            models.Index(fields=["claim_invitation_sent_at"]),
            models.Index(fields=["deadline_3d_reminder_sent_at"]),
            models.Index(fields=["deadline_24h_reminder_sent_at"]),
        ]


class AllocationUploadChunk(models.Model):
    """
    Tracks a batch uploadAllocations() call.
    Each chunk is idempotent — identified by idempotency_key.
    """
    run             = models.ForeignKey(PayrollRun, on_delete=models.CASCADE, related_name="upload_chunks")
    idempotency_key = models.CharField(max_length=80)
    employee_count  = models.PositiveIntegerField()

    tx_hash   = models.CharField(max_length=80, blank=True)
    status    = models.CharField(max_length=32, default="draft")
    error     = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("run", "idempotency_key")


# ─────────────────────────────────────────────────────────────────────────────
# Chain Transactions
# ─────────────────────────────────────────────────────────────────────────────

class ChainTx(models.Model):
    STATUS = [
        ("broadcasted",       "broadcasted"),
        ("mined_success",     "mined_success"),
        ("mined_revert",      "mined_revert"),
        ("dropped",           "dropped"),
        ("replaced",          "replaced"),
        ("unknown",           "unknown"),
        ("finalized_success", "finalized_success"),
        ("finalized_revert",  "finalized_revert"),
    ]
    INTENT = [
        ("PV_CREATE_PAYROLL",       "PV_CREATE_PAYROLL"),
        ("PV_UPLOAD_ALLOCATIONS",   "PV_UPLOAD_ALLOCATIONS"),
        ("PV_FINALIZE_ALLOCATIONS", "PV_FINALIZE_ALLOCATIONS"),
        ("PV_FUND_PAYROLL",         "PV_FUND_PAYROLL"),
        ("PV_ACTIVATE_PAYROLL",     "PV_ACTIVATE_PAYROLL"),
        ("PV_REQUEST_CLAIM",        "PV_REQUEST_CLAIM"),
        ("PV_FINALIZE_CLAIM",       "PV_FINALIZE_CLAIM"),
        ("PV_CANCEL_CLAIM",         "PV_CANCEL_CLAIM"),
        ("SR_DEPOSIT",              "SR_DEPOSIT"),
        ("SR_REQUEST_WITHDRAW",     "SR_REQUEST_WITHDRAW"),
        ("SR_FINALIZE_WITHDRAW",    "SR_FINALIZE_WITHDRAW"),
        ("SR_CANCEL_WITHDRAW",      "SR_CANCEL_WITHDRAW"),
    ]

    chain         = models.ForeignKey(Chain, on_delete=models.PROTECT)
    tx_hash       = models.CharField(max_length=80)
    sender        = models.CharField(max_length=42, blank=True)
    to            = models.CharField(max_length=42, blank=True)
    nonce         = models.BigIntegerField(null=True, blank=True)

    intent_type   = models.CharField(max_length=64, choices=INTENT)
    ref_model     = models.CharField(max_length=64, blank=True)
    ref_id        = models.CharField(max_length=64, blank=True)

    status        = models.CharField(max_length=32, choices=STATUS, default="broadcasted")

    block_number  = models.BigIntegerField(null=True, blank=True)
    block_hash    = models.CharField(max_length=80, blank=True)
    gas_used      = models.BigIntegerField(null=True, blank=True)
    replaced_by   = models.CharField(max_length=80, blank=True)
    error_message = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("chain", "tx_hash")
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["ref_model", "ref_id"]),
        ]


# ─────────────────────────────────────────────────────────────────────────────
# Claim
# ─────────────────────────────────────────────────────────────────────────────

class Claim(models.Model):
    STATUS = [
        ("draft",                "draft"),
        ("request_broadcasted",  "request_broadcasted"),
        ("pending_ready",        "pending_ready"),
        ("finalize_broadcasted", "finalize_broadcasted"),
        ("finalized_success",    "finalized_success"),
        ("finalized_revert",     "finalized_revert"),
        ("cancel_broadcasted",   "cancel_broadcasted"),
        ("cancelled",            "cancelled"),
        ("failed",               "failed"),
    ]
    run                = models.ForeignKey(PayrollRun, on_delete=models.CASCADE, related_name="claims")
    employee_address   = models.CharField(max_length=42)

    request_tx_hash    = models.CharField(max_length=80, blank=True)
    finalize_tx_hash   = models.CharField(max_length=80, blank=True)
    cancel_tx_hash     = models.CharField(max_length=80, blank=True)

    request_id         = models.CharField(max_length=66, blank=True)
    pending_ok_handle  = models.CharField(max_length=66, blank=True)
    pending_request_id = models.CharField(max_length=66, blank=True)

    ok_plaintext       = models.BooleanField(null=True, blank=True)
    ok_sig             = models.TextField(blank=True)

    status             = models.CharField(max_length=32, choices=STATUS, default="draft")
    last_error         = models.TextField(blank=True)

    class Meta:
        unique_together = ("run", "employee_address")


# ─────────────────────────────────────────────────────────────────────────────
# SwapRouter Withdraw
# ─────────────────────────────────────────────────────────────────────────────

class SwapRouterWithdraw(models.Model):
    STATUS = [
        ("draft",                "draft"),
        ("request_broadcasted",  "request_broadcasted"),
        ("pending_ready",        "pending_ready"),
        ("finalize_broadcasted", "finalize_broadcasted"),
        ("cancel_broadcasted",   "cancel_broadcasted"),
        ("finalized_success",    "finalized_success"),
        ("finalized_revert",     "finalized_revert"),
        ("cancelled",            "cancelled"),
        ("failed",               "failed"),
    ]

    claim                 = models.OneToOneField("Claim", on_delete=models.CASCADE, related_name="withdraw")
    chain                 = models.ForeignKey(Chain, on_delete=models.PROTECT)

    user_address          = models.CharField(max_length=42)
    withdraw_key          = models.CharField(max_length=66, null=True, blank=True, unique=True)

    request_tx_hash       = models.CharField(max_length=80, blank=True)
    finalize_tx_hash      = models.CharField(max_length=80, blank=True)
    cancel_tx_hash        = models.CharField(max_length=80, blank=True)

    request_id            = models.CharField(max_length=66, blank=True)
    pending_amount_handle = models.CharField(max_length=66, blank=True)
    pending_ok_handle     = models.CharField(max_length=66, blank=True)
    pending_request_id    = models.CharField(max_length=66, blank=True)

    amount_plaintext      = models.BigIntegerField(null=True, blank=True)
    amount_sig            = models.TextField(blank=True)
    ok_plaintext          = models.BooleanField(null=True, blank=True)
    ok_sig                = models.TextField(blank=True)

    status                = models.CharField(max_length=32, choices=STATUS, default="draft")
    last_error            = models.TextField(blank=True)

    created_at            = models.DateTimeField(auto_now_add=True)
    updated_at            = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["user_address"]),
        ]