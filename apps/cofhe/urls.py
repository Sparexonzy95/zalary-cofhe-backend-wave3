from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.cofhe.api import (
    ClaimViewSet,
    PayrollRunViewSet,
    PayrollTemplateViewSet,
    employee_claimables_view,
    swaprouter_submit_cancel_withdraw,
    swaprouter_submit_cancel_withdraw_with_payload,
    swaprouter_submit_finalize_withdraw,
    swaprouter_submit_finalize_withdraw_with_payload,
    swaprouter_submit_request_withdraw,
    swaprouter_sync_pending,
    swaprouter_withdraw_create,
    swaprouter_withdraw_detail,
)

router = DefaultRouter()
router.register(r"templates", PayrollTemplateViewSet, basename="template")
router.register(r"runs", PayrollRunViewSet, basename="run")
router.register(r"claims", ClaimViewSet, basename="claim")

urlpatterns = [
    path("", include(router.urls)),
    path("employees/<str:address>/claimables/", employee_claimables_view),

    path("swaprouter/withdraws/", swaprouter_withdraw_create),
    path("swaprouter/withdraws/<int:withdraw_id>/", swaprouter_withdraw_detail),
    path("swaprouter/withdraws/<int:withdraw_id>/submit_request/", swaprouter_submit_request_withdraw),
    path("swaprouter/withdraws/<int:withdraw_id>/sync_pending/", swaprouter_sync_pending),
    path("swaprouter/withdraws/<int:withdraw_id>/submit_finalize/", swaprouter_submit_finalize_withdraw),
    path("swaprouter/withdraws/<int:withdraw_id>/submit_finalize_with_payload/", swaprouter_submit_finalize_withdraw_with_payload),
    path("swaprouter/withdraws/<int:withdraw_id>/submit_cancel/", swaprouter_submit_cancel_withdraw),
    path("swaprouter/withdraws/<int:withdraw_id>/submit_cancel_with_payload/", swaprouter_submit_cancel_withdraw_with_payload),
]