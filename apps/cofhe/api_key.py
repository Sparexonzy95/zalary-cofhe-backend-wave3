from __future__ import annotations

from django.conf import settings
from rest_framework.permissions import BasePermission
from rest_framework.response import Response


class ApiKeyPermission(BasePermission):
    """
    Gate every endpoint with a static API key.
    Accept via:  X-API-Key: <key>
              or Authorization: Api-Key <key>
    """
    def has_permission(self, request, view) -> bool:
        required = (getattr(settings, "API_KEY", "") or "").strip()
        if not required:
            return True  # no key configured — open in dev
        got = (
            request.headers.get("X-API-Key", "")
            or request.headers.get("X-API-KEY", "")
        ).strip()
        if not got:
            auth = (request.headers.get("Authorization", "") or "").strip()
            if auth.lower().startswith("api-key "):
                got = auth.split(" ", 1)[1].strip()
        return got == required


def require_api_key(request) -> Response | None:
    """Functional version for @api_view endpoints."""
    key      = (request.headers.get("X-API-Key", "") or
                request.headers.get("X-API-KEY", "")).strip()
    if not key:
        auth = (request.headers.get("Authorization", "") or "").strip()
        if auth.lower().startswith("api-key "):
            key = auth.split(" ", 1)[1].strip()
    expected = (getattr(settings, "API_KEY", "") or "").strip()
    if not expected:
        return None
    if key != expected:
        return Response({"detail": "unauthorized"}, status=401)
    return None