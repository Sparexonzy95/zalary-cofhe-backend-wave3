from django.contrib import admin

from apps.onboarding.models import (
    EmailVerificationCode,
    EmployeeProfile,
    EmployerProfile,
    UserProfile,
    WalletAuthNonce,
)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("wallet_address", "email", "email_verified", "last_selected_role", "is_active", "created_at")
    search_fields = ("wallet_address", "email")


@admin.register(EmployerProfile)
class EmployerProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "company_name", "work_email", "onboarding_completed", "created_at")
    search_fields = ("user__wallet_address", "company_name", "work_email")


@admin.register(EmployeeProfile)
class EmployeeProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "display_name", "notification_email", "private_access_enabled", "onboarding_completed", "created_at")
    search_fields = ("user__wallet_address", "display_name", "notification_email")


@admin.register(WalletAuthNonce)
class WalletAuthNonceAdmin(admin.ModelAdmin):
    list_display = ("wallet_address", "expires_at", "consumed_at", "created_at")
    search_fields = ("wallet_address",)


@admin.register(EmailVerificationCode)
class EmailVerificationCodeAdmin(admin.ModelAdmin):
    list_display = ("user", "email", "purpose", "expires_at", "used_at", "attempts", "created_at")
    search_fields = ("user__wallet_address", "email")
