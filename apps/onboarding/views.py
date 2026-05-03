from __future__ import annotations

import logging

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone
from eth_account import Account
from eth_account.messages import encode_defunct
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.onboarding.auth import issue_token, require_profile
from apps.onboarding.models import (
    EmailVerificationCode,
    EmployeeProfile,
    EmployerProfile,
    ROLE_EMPLOYEE,
    ROLE_EMPLOYER,
    UserProfile,
    WalletAuthNonce,
    normalize_wallet,
)
from apps.onboarding.serializers import profile_payload, refresh_completion

log = logging.getLogger(__name__)


def _bad(message: str, status: int = 400) -> Response:
    return Response({"detail": message}, status=status)


def _valid_role(value: str) -> bool:
    return value in {ROLE_EMPLOYER, ROLE_EMPLOYEE}


def _send_code_email(email: str, code: str) -> None:
    subject = "Your Zalary verification code"

    body = f"""Hello,

Use this code to verify your Zalary onboarding email:

{code}

This code expires in 15 minutes.

If you did not request this code, you can safely ignore this email.

 Zalary
"""

    send_mail(
        subject=subject,
        message=body,
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "Zalary <noreply@zalary.app>"),
        recipient_list=[email],
        fail_silently=False,
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def auth_nonce(request):
    wallet = request.data.get("wallet_address", "")
    try:
        obj = WalletAuthNonce.issue(wallet)
    except ValueError as exc:
        return _bad(str(exc))

    return Response({
        "wallet_address": obj.wallet_address,
        "message": obj.message,
        "expires_at": obj.expires_at.isoformat(),
    })


@api_view(["POST"])
@permission_classes([AllowAny])
@transaction.atomic
def auth_verify(request):
    wallet_raw = request.data.get("wallet_address", "")
    signature = (request.data.get("signature", "") or "").strip()
    role = (request.data.get("role", "") or "").strip().lower()

    if not _valid_role(role):
        return _bad("role must be employer or employee")

    try:
        wallet = normalize_wallet(wallet_raw)
    except ValueError as exc:
        return _bad(str(exc))

    if not signature.startswith("0x"):
        return _bad("signature must be a 0x-prefixed signature")

    try:
        nonce_obj = WalletAuthNonce.objects.select_for_update().get(wallet_address=wallet)
    except WalletAuthNonce.DoesNotExist:
        return _bad("sign-in nonce not found. request a new nonce first", 404)

    if nonce_obj.is_expired:
        return _bad("sign-in message expired. request a new nonce", 400)
    if nonce_obj.is_consumed:
        return _bad("sign-in message already used. request a new nonce", 400)

    try:
        message = encode_defunct(text=nonce_obj.message)
        recovered = Account.recover_message(message, signature=signature).lower()
    except Exception as exc:
        log.warning("wallet signature recovery failed: %s", exc)
        return _bad("invalid wallet signature")

    if recovered != wallet:
        return _bad("signature does not match connected wallet", 401)

    user, _ = UserProfile.objects.get_or_create(wallet_address=wallet)
    user.last_selected_role = role
    user.last_login_at = timezone.now()
    user.save(update_fields=["last_selected_role", "last_login_at", "updated_at"])

    if role == ROLE_EMPLOYER:
        EmployerProfile.objects.get_or_create(user=user)
    else:
        EmployeeProfile.objects.get_or_create(user=user)

    nonce_obj.consumed_at = timezone.now()
    nonce_obj.save(update_fields=["consumed_at"])

    refresh_completion(user)
    token = issue_token(user)

    return Response({
        "token": token,
        "profile": profile_payload(user),
    })


@api_view(["GET"])
@require_profile
def profile_me(request):
    user = request.onboarding_profile
    refresh_completion(user)
    return Response(profile_payload(user))


@api_view(["POST"])
@require_profile
@transaction.atomic
def employer_profile_update(request):
    user: UserProfile = request.onboarding_profile
    employer, _ = EmployerProfile.objects.get_or_create(user=user)

    company_name = (request.data.get("company_name", "") or "").strip()
    work_email = (request.data.get("email", "") or request.data.get("work_email", "") or "").strip().lower()
    company_size = (request.data.get("company_size", "") or "").strip()

    if not company_name:
        return _bad("company_name is required")
    if not work_email:
        return _bad("email is required")

    # Reset verification if email changes.
    if user.email.lower() != work_email:
        user.email = work_email
        user.email_verified = False
        user.save(update_fields=["email", "email_verified", "updated_at"])

    employer.company_name = company_name
    employer.work_email = work_email
    employer.company_size = company_size
    employer.save(update_fields=["company_name", "work_email", "company_size", "updated_at"])

    code_obj, code = EmailVerificationCode.issue(user, work_email)
    _send_code_email(work_email, code)
    refresh_completion(user)

    payload = {"profile": profile_payload(user), "email_verification_required": not user.email_verified}
    if getattr(settings, "DEBUG", False):
        payload["dev_email_code"] = code
    return Response(payload)


@api_view(["POST"])
@require_profile
@transaction.atomic
def employee_profile_update(request):
    user: UserProfile = request.onboarding_profile
    employee, _ = EmployeeProfile.objects.get_or_create(user=user)

    display_name = (request.data.get("display_name", "") or "").strip()
    email = (request.data.get("email", "") or request.data.get("notification_email", "") or "").strip().lower()

    if not email:
        return _bad("email is required")

    if user.email.lower() != email:
        user.email = email
        user.email_verified = False
        user.save(update_fields=["email", "email_verified", "updated_at"])

    employee.display_name = display_name
    employee.notification_email = email
    employee.save(update_fields=["display_name", "notification_email", "updated_at"])

    code_obj, code = EmailVerificationCode.issue(user, email)
    _send_code_email(email, code)
    refresh_completion(user)

    payload = {"profile": profile_payload(user), "email_verification_required": not user.email_verified}
    if getattr(settings, "DEBUG", False):
        payload["dev_email_code"] = code
    return Response(payload)


@api_view(["POST"])
@require_profile
def email_request_code(request):
    user: UserProfile = request.onboarding_profile
    email = (request.data.get("email", "") or user.email or "").strip().lower()
    if not email:
        return _bad("email is required")

    code_obj, code = EmailVerificationCode.issue(user, email)
    _send_code_email(email, code)

    payload = {"detail": "verification code sent", "email": email}
    if getattr(settings, "DEBUG", False):
        payload["dev_email_code"] = code
    return Response(payload)


@api_view(["POST"])
@require_profile
@transaction.atomic
def email_verify(request):
    user: UserProfile = request.onboarding_profile
    code = (request.data.get("code", "") or "").strip()
    email = (request.data.get("email", "") or user.email or "").strip().lower()

    if not code:
        return _bad("code is required")

    obj = (
        EmailVerificationCode.objects
        .select_for_update()
        .filter(user=user, email=email, purpose=EmailVerificationCode.PURPOSE_ONBOARDING)
        .order_by("-created_at")
        .first()
    )
    if not obj or not obj.verify(code):
        return _bad("invalid or expired verification code")

    user.email = email
    user.email_verified = True
    user.save(update_fields=["email", "email_verified", "updated_at"])
    refresh_completion(user)

    return Response({"profile": profile_payload(user)})


@api_view(["POST"])
@require_profile
@transaction.atomic
def employee_private_access_enabled(request):
    user: UserProfile = request.onboarding_profile
    employee, _ = EmployeeProfile.objects.get_or_create(user=user)
    employee.private_access_enabled = True
    employee.save(update_fields=["private_access_enabled", "updated_at"])
    refresh_completion(user)
    return Response({"profile": profile_payload(user)})


@api_view(["POST"])
@require_profile
def logout(request):
    # Token is stateless; frontend removes it from localStorage.
    return Response({"detail": "logged out"})
