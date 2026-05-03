from __future__ import annotations

import secrets
from datetime import timedelta

from django.contrib.auth.hashers import check_password, make_password
from django.db import models
from django.utils import timezone


ROLE_EMPLOYER = "employer"
ROLE_EMPLOYEE = "employee"
ROLE_CHOICES = [
    (ROLE_EMPLOYER, "Employer"),
    (ROLE_EMPLOYEE, "Employee"),
]


def normalize_wallet(address: str) -> str:
    value = (address or "").strip().lower()
    if not value.startswith("0x") or len(value) != 42:
        raise ValueError("wallet_address must be a 20-byte EVM address")
    return value


def default_expiry(minutes: int = 10):
    return timezone.now() + timedelta(minutes=minutes)


class WalletAuthNonce(models.Model):
    wallet_address = models.CharField(max_length=42, unique=True, db_index=True)
    nonce = models.CharField(max_length=80)
    message = models.TextField()
    expires_at = models.DateTimeField()
    consumed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @classmethod
    def issue(cls, wallet_address: str) -> "WalletAuthNonce":
        wallet = normalize_wallet(wallet_address)
        nonce = secrets.token_urlsafe(24)
        issued_at = timezone.now().isoformat()
        message = (
            "Sign in to Zalary\\n\\n"
            "This confirms you own this wallet. It does not cost gas.\\n\\n"
            f"Wallet: {wallet}\\n"
            f"Nonce: {nonce}\\n"
            f"Issued At: {issued_at}"
        )
        obj, _ = cls.objects.update_or_create(
            wallet_address=wallet,
            defaults={
                "nonce": nonce,
                "message": message,
                "expires_at": default_expiry(10),
                "consumed_at": None,
            },
        )
        return obj

    @property
    def is_expired(self) -> bool:
        return timezone.now() >= self.expires_at

    @property
    def is_consumed(self) -> bool:
        return self.consumed_at is not None


class UserProfile(models.Model):
    wallet_address = models.CharField(max_length=42, unique=True, db_index=True)
    email = models.EmailField(blank=True, default="")
    email_verified = models.BooleanField(default=False)
    last_selected_role = models.CharField(max_length=16, choices=ROLE_CHOICES, blank=True, default="")
    last_login_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=["email"]), models.Index(fields=["last_selected_role"])]

    def save(self, *args, **kwargs):
        if self.wallet_address:
            self.wallet_address = normalize_wallet(self.wallet_address)
        if self.last_selected_role and self.last_selected_role not in {ROLE_EMPLOYER, ROLE_EMPLOYEE}:
            raise ValueError("invalid selected role")
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.wallet_address


class EmployerProfile(models.Model):
    user = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name="employer_profile")
    company_name = models.CharField(max_length=180, blank=True, default="")
    work_email = models.EmailField(blank=True, default="")
    company_size = models.CharField(max_length=50, blank=True, default="")
    onboarding_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def recompute_completion(self) -> bool:
        complete = bool(self.company_name.strip() and self.work_email.strip() and self.user.email_verified)
        if complete and not self.onboarding_completed:
            self.completed_at = timezone.now()
        if not complete:
            self.completed_at = None
        self.onboarding_completed = complete
        self.save(update_fields=["onboarding_completed", "completed_at", "updated_at"])
        return complete


class EmployeeProfile(models.Model):
    user = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name="employee_profile")
    display_name = models.CharField(max_length=120, blank=True, default="")
    notification_email = models.EmailField(blank=True, default="")
    private_access_enabled = models.BooleanField(default=False)
    onboarding_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def recompute_completion(self) -> bool:
        complete = bool(self.notification_email.strip() and self.user.email_verified and self.private_access_enabled)
        if complete and not self.onboarding_completed:
            self.completed_at = timezone.now()
        if not complete:
            self.completed_at = None
        self.onboarding_completed = complete
        self.save(update_fields=["onboarding_completed", "completed_at", "updated_at"])
        return complete


class EmailVerificationCode(models.Model):
    PURPOSE_ONBOARDING = "onboarding"
    PURPOSE_CHOICES = [(PURPOSE_ONBOARDING, "Onboarding")]

    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name="email_codes")
    email = models.EmailField()
    code_hash = models.CharField(max_length=256)
    purpose = models.CharField(max_length=32, choices=PURPOSE_CHOICES, default=PURPOSE_ONBOARDING)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    attempts = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    @classmethod
    def issue(cls, user: UserProfile, email: str, purpose: str = PURPOSE_ONBOARDING) -> tuple["EmailVerificationCode", str]:
        code = f"{secrets.randbelow(1000000):06d}"
        obj = cls.objects.create(
            user=user,
            email=email.strip().lower(),
            code_hash=make_password(code),
            purpose=purpose,
            expires_at=default_expiry(15),
        )
        return obj, code

    @property
    def is_expired(self) -> bool:
        return timezone.now() >= self.expires_at

    @property
    def is_used(self) -> bool:
        return self.used_at is not None

    def verify(self, code: str) -> bool:
        self.attempts += 1
        self.save(update_fields=["attempts"])
        if self.is_used or self.is_expired or self.attempts > 5:
            return False
        if not check_password((code or "").strip(), self.code_hash):
            return False
        self.used_at = timezone.now()
        self.save(update_fields=["used_at"])
        return True
