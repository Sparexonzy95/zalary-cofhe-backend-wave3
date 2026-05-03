from __future__ import annotations

from functools import wraps
from typing import Callable

from django.conf import settings
from django.core import signing
from rest_framework.response import Response

from apps.onboarding.models import UserProfile, normalize_wallet

TOKEN_SALT = "zalary.onboarding.auth.v1"
TOKEN_MAX_AGE_SECONDS = 60 * 60 * 24 * 7  # 7 days


def issue_token(profile: UserProfile) -> str:
    payload = {
        "profile_id": profile.id,
        "wallet": profile.wallet_address,
    }
    return signing.dumps(payload, salt=TOKEN_SALT)


def read_bearer_token(request) -> str:
    auth = (request.headers.get("Authorization", "") or "").strip()
    if auth.lower().startswith("bearer "):
        return auth.split(" ", 1)[1].strip()
    return ""


def get_profile_from_request(request) -> UserProfile | None:
    token = read_bearer_token(request)
    if not token:
        return None

    try:
        payload = signing.loads(token, salt=TOKEN_SALT, max_age=TOKEN_MAX_AGE_SECONDS)
        profile_id = payload.get("profile_id")
        wallet = normalize_wallet(payload.get("wallet", ""))
        return UserProfile.objects.get(id=profile_id, wallet_address=wallet, is_active=True)
    except Exception:
        return None


def require_profile(view_func: Callable):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        profile = get_profile_from_request(request)
        if profile is None:
            return Response({"detail": "authentication required"}, status=401)
        request.onboarding_profile = profile
        return view_func(request, *args, **kwargs)
    return wrapper


def is_debug() -> bool:
    return bool(getattr(settings, "DEBUG", False))
