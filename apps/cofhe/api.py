"""
Zalary Wave 3 API interface.

This public module exposes the backend route surface used by the Wave 3
submission without publishing private orchestration internals.
"""

from __future__ import annotations

from rest_framework import viewsets
from rest_framework.decorators import action, api_view
from rest_framework.response import Response

from .models import Claim, PayrollRun, PayrollTemplate, SwapRouterWithdraw
from .serializers import (
    ClaimSerializer,
    PayrollRunSerializer,
    PayrollTemplateSerializer,
    SwapRouterWithdrawSerializer,
)


PUBLIC_INTERFACE_RESPONSE = {
    "detail": "Endpoint interface included for Wave 3 review."
}


class PayrollTemplateViewSet(viewsets.ModelViewSet):
    queryset = PayrollTemplate.objects.all().order_by("-id")
    serializer_class = PayrollTemplateSerializer

    @action(detail=True, methods=["post"])
    def activate(self, request, pk=None):
        return Response(PUBLIC_INTERFACE_RESPONSE)

    @action(detail=True, methods=["get"])
    def preview_runs(self, request, pk=None):
        return Response(PUBLIC_INTERFACE_RESPONSE)

    @action(detail=True, methods=["post"])
    def create_next_run(self, request, pk=None):
        return Response(PUBLIC_INTERFACE_RESPONSE)


class PayrollRunViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PayrollRun.objects.all().order_by("-id")
    serializer_class = PayrollRunSerializer

    @action(detail=True, methods=["post"])
    def set_ciphertexts(self, request, pk=None):
        return Response(PUBLIC_INTERFACE_RESPONSE)

    @action(detail=True, methods=["get"])
    def missing_ciphertexts(self, request, pk=None):
        return Response(PUBLIC_INTERFACE_RESPONSE)

    @action(detail=True, methods=["get"])
    def funding_quote(self, request, pk=None):
        return Response(PUBLIC_INTERFACE_RESPONSE)

    @action(detail=True, methods=["get"])
    def funding_context(self, request, pk=None):
        return Response(PUBLIC_INTERFACE_RESPONSE)

    @action(detail=True, methods=["post"])
    def create_payroll(self, request, pk=None):
        return Response(PUBLIC_INTERFACE_RESPONSE)

    @action(detail=True, methods=["post"])
    def upload_allocations(self, request, pk=None):
        return Response(PUBLIC_INTERFACE_RESPONSE)

    @action(detail=True, methods=["post"])
    def finalize_allocations(self, request, pk=None):
        return Response(PUBLIC_INTERFACE_RESPONSE)

    @action(detail=True, methods=["post"])
    def fund_payroll(self, request, pk=None):
        return Response(PUBLIC_INTERFACE_RESPONSE)

    @action(detail=True, methods=["get"])
    def funded_once_handle(self, request, pk=None):
        return Response(PUBLIC_INTERFACE_RESPONSE)

    @action(detail=True, methods=["post"])
    def activate_payroll(self, request, pk=None):
        return Response(PUBLIC_INTERFACE_RESPONSE)


class ClaimViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Claim.objects.all().order_by("-id")
    serializer_class = ClaimSerializer

    @action(detail=True, methods=["post"])
    def submit_request_claim(self, request, pk=None):
        return Response(PUBLIC_INTERFACE_RESPONSE)

    @action(detail=True, methods=["post"])
    def sync_pending(self, request, pk=None):
        return Response(PUBLIC_INTERFACE_RESPONSE)

    @action(detail=True, methods=["post"])
    def submit_finalize_claim(self, request, pk=None):
        return Response(PUBLIC_INTERFACE_RESPONSE)

    @action(detail=True, methods=["post"])
    def submit_cancel_claim(self, request, pk=None):
        return Response(PUBLIC_INTERFACE_RESPONSE)


class SwapRouterWithdrawViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SwapRouterWithdraw.objects.all().order_by("-id")
    serializer_class = SwapRouterWithdrawSerializer

    @action(detail=True, methods=["post"])
    def submit_request(self, request, pk=None):
        return Response(PUBLIC_INTERFACE_RESPONSE)

    @action(detail=True, methods=["post"])
    def sync_pending(self, request, pk=None):
        return Response(PUBLIC_INTERFACE_RESPONSE)

    @action(detail=True, methods=["post"])
    def submit_finalize(self, request, pk=None):
        return Response(PUBLIC_INTERFACE_RESPONSE)

    @action(detail=True, methods=["post"])
    def submit_cancel(self, request, pk=None):
        return Response(PUBLIC_INTERFACE_RESPONSE)


@api_view(["GET"])
def employee_claimables_view(request, address: str):
    return Response(
        {
            "employee_address": address,
            "detail": "Employee claimables interface included for Wave 3 review.",
            "claimables": [],
        }
    )


@api_view(["GET", "POST"])
def swaprouter_withdraw_create(request):
    return Response(PUBLIC_INTERFACE_RESPONSE)


@api_view(["GET"])
def swaprouter_withdraw_detail(request, withdraw_id: int):
    return Response(
        {
            "withdraw_id": withdraw_id,
            "detail": "SwapRouter withdrawal detail interface included for Wave 3 review.",
        }
    )


@api_view(["POST"])
def swaprouter_submit_request_withdraw(request, withdraw_id: int):
    return Response(PUBLIC_INTERFACE_RESPONSE)


@api_view(["POST"])
def swaprouter_sync_pending(request, withdraw_id: int):
    return Response(PUBLIC_INTERFACE_RESPONSE)


@api_view(["POST"])
def swaprouter_submit_finalize_withdraw(request, withdraw_id: int):
    return Response(PUBLIC_INTERFACE_RESPONSE)


@api_view(["POST"])
def swaprouter_submit_finalize_withdraw_with_payload(request, withdraw_id: int):
    return Response(PUBLIC_INTERFACE_RESPONSE)


@api_view(["POST"])
def swaprouter_submit_cancel_withdraw(request, withdraw_id: int):
    return Response(PUBLIC_INTERFACE_RESPONSE)


@api_view(["POST"])
def swaprouter_submit_cancel_withdraw_with_payload(request, withdraw_id: int):
    return Response(PUBLIC_INTERFACE_RESPONSE)