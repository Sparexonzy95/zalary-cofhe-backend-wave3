from __future__ import annotations

from typing import Any, Dict, List

from django.db import transaction
from rest_framework import serializers

from apps.cofhe.models import (
    AllocationUploadChunk,
    Claim,
    PayrollRun,
    PayrollTemplate,
    RunAllocation,
    ScheduleConfig,
    SwapRouterWithdraw,
    TemplateEmployee,
)


def _model_field_names(model_cls) -> set[str]:
    return {
        f.name
        for f in model_cls._meta.get_fields()
        if getattr(f, "concrete", False) and not getattr(f, "many_to_many", False)
    }


def _build_schedule_kwargs(data: dict) -> dict:
    allowed = _model_field_names(ScheduleConfig)
    return {k: v for k, v in data.items() if k in allowed}


def _normalize_wallet_address(value: Any, label: str = "wallet address") -> str:
    address = str(value or "").strip().lower()

    if not (address.startswith("0x") and len(address) == 42):
        raise serializers.ValidationError(
            {"employees": [f"Invalid {label}: {value or 'empty'}"]}
        )

    try:
        int(address[2:], 16)
    except ValueError:
        raise serializers.ValidationError(
            {"employees": [f"Invalid {label}: {value}"]}
        )

    return address


def _normalize_email(value: Any, employee_address: str) -> str:
    email = str(value or "").strip().lower()

    if not email:
        raise serializers.ValidationError(
            {
                "employees": [
                    f"employee_email is required for employee {employee_address}"
                ]
            }
        )

    validator = serializers.EmailField()

    try:
        return str(validator.run_validation(email)).strip().lower()
    except serializers.ValidationError:
        raise serializers.ValidationError(
            {
                "employees": [
                    f"Invalid employee_email for employee {employee_address}: {email}"
                ]
            }
        )


def _normalize_amount(value: Any, employee_address: str) -> int:
    try:
        amount = int(value)
    except (TypeError, ValueError):
        raise serializers.ValidationError(
            {
                "employees": [
                    f"amount_atomic must be a valid integer for employee {employee_address}"
                ]
            }
        )

    if amount <= 0:
        raise serializers.ValidationError(
            {
                "employees": [
                    f"amount_atomic must be greater than zero for employee {employee_address}"
                ]
            }
        )

    return amount


def _normalize_template_employees(employees_data: list) -> list[dict]:
    normalized: list[dict] = []
    seen_addresses: set[str] = set()

    for index, item in enumerate(employees_data, start=1):
        if not isinstance(item, dict):
            raise serializers.ValidationError(
                {"employees": [f"Employee row {index} must be an object."]}
            )

        employee_address = _normalize_wallet_address(
            item.get("employee_address"),
            label=f"employee wallet address at row {index}",
        )

        if employee_address in seen_addresses:
            raise serializers.ValidationError(
                {
                    "employees": [
                        f"Duplicate employee wallet address detected: {employee_address}"
                    ]
                }
            )

        seen_addresses.add(employee_address)

        employee_email = _normalize_email(
            item.get("employee_email"),
            employee_address,
        )

        amount_atomic = _normalize_amount(
            item.get("amount_atomic"),
            employee_address,
        )

        employee_name = str(item.get("employee_name", "") or "").strip()
        is_active = bool(item.get("is_active", True))

        normalized.append(
            {
                "employee_address": employee_address,
                "employee_name": employee_name,
                "employee_email": employee_email,
                "amount_atomic": amount_atomic,
                "is_active": is_active,
            }
        )

    return normalized


class ScheduleConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScheduleConfig
        fields = "__all__"


class TemplateEmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TemplateEmployee
        fields = [
            "employee_address",
            "employee_name",
            "employee_email",
            "amount_atomic",
            "is_active",
        ]

    def validate_employee_address(self, value):
        return _normalize_wallet_address(value, label="employee wallet address")

    def validate_employee_email(self, value):
        email = str(value or "").strip().lower()

        if not email:
            raise serializers.ValidationError("Employee email is required.")

        return str(serializers.EmailField().run_validation(email)).strip().lower()

    def validate_amount_atomic(self, value):
        amount = int(value)

        if amount <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")

        return amount


class PayrollTemplateSerializer(serializers.ModelSerializer):
    schedule = ScheduleConfigSerializer()
    employees = TemplateEmployeeSerializer(many=True)

    class Meta:
        model = PayrollTemplate
        fields = "__all__"
        read_only_fields = ["next_run_at", "last_run_at", "status"]

    @transaction.atomic
    def create(self, validated_data: Dict[str, Any]) -> PayrollTemplate:
        schedule_data = validated_data.pop("schedule", None)
        employees_data = validated_data.pop("employees", [])

        if not isinstance(schedule_data, dict):
            raise serializers.ValidationError({"schedule": ["Expected an object."]})

        if not isinstance(employees_data, list):
            raise serializers.ValidationError({"employees": ["Expected a list."]})

        if len(employees_data) == 0:
            raise serializers.ValidationError(
                {"employees": ["At least one employee is required."]}
            )

        normalized_employees = _normalize_template_employees(employees_data)

        schedule = ScheduleConfig.objects.create(**_build_schedule_kwargs(schedule_data))

        allowed = _model_field_names(PayrollTemplate)
        tmpl_kwargs = {k: v for k, v in validated_data.items() if k in allowed}
        tmpl_kwargs.setdefault("status", "draft")

        if tmpl_kwargs.get("employer_address"):
            tmpl_kwargs["employer_address"] = str(
                tmpl_kwargs["employer_address"]
            ).strip().lower()

        tmpl = PayrollTemplate.objects.create(schedule=schedule, **tmpl_kwargs)

        to_create: List[TemplateEmployee] = [
            TemplateEmployee(
                template=tmpl,
                employee_address=e["employee_address"],
                employee_name=e["employee_name"],
                employee_email=e["employee_email"],
                amount_atomic=e["amount_atomic"],
                is_active=e["is_active"],
            )
            for e in normalized_employees
        ]

        TemplateEmployee.objects.bulk_create(to_create)

        return tmpl


class PayrollRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayrollRun
        fields = "__all__"
        read_only_fields = [
            "required_total_atomic",
            "onchain_payroll_id",
            "employer_address",
            "status",
            "create_tx_hash",
            "fund_tx_hash",
            "activate_tx_hash",
            "funded_once_handle",
            "funded_plaintext",
            "funded_sig",
        ]


class RunAllocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = RunAllocation
        fields = "__all__"
        read_only_fields = [
            "uploaded",
            "upload_tx_hash",
            "claim_invitation_sent_at",
            "deadline_3d_reminder_sent_at",
            "deadline_24h_reminder_sent_at",
            "claim_completion_reminder_sent_at",
        ]


class AllocationUploadChunkSerializer(serializers.ModelSerializer):
    class Meta:
        model = AllocationUploadChunk
        fields = "__all__"
        read_only_fields = ["tx_hash", "status", "error", "created_at"]


class ClaimSerializer(serializers.ModelSerializer):
    run_onchain_payroll_id = serializers.IntegerField(
        source="run.onchain_payroll_id", read_only=True
    )

    withdraw_id = serializers.SerializerMethodField()
    withdraw_key = serializers.SerializerMethodField()
    withdraw_status = serializers.SerializerMethodField()
    withdraw_request_tx_hash = serializers.SerializerMethodField()
    withdraw_finalize_tx_hash = serializers.SerializerMethodField()
    withdraw_cancel_tx_hash = serializers.SerializerMethodField()

    class Meta:
        model = Claim
        fields = "__all__"
        read_only_fields = [
            "request_tx_hash",
            "finalize_tx_hash",
            "cancel_tx_hash",
            "pending_ok_handle",
            "pending_request_id",
            "ok_plaintext",
            "ok_sig",
            "status",
            "last_error",
            "run_onchain_payroll_id",
            "withdraw_id",
            "withdraw_key",
            "withdraw_status",
            "withdraw_request_tx_hash",
            "withdraw_finalize_tx_hash",
            "withdraw_cancel_tx_hash",
        ]

    def _withdraw(self, obj: Claim) -> SwapRouterWithdraw | None:
        return getattr(obj, "withdraw", None)

    def get_withdraw_id(self, obj: Claim):
        w = self._withdraw(obj)
        return w.id if w else None

    def get_withdraw_key(self, obj: Claim):
        w = self._withdraw(obj)
        return w.withdraw_key if w else None

    def get_withdraw_status(self, obj: Claim):
        w = self._withdraw(obj)
        return w.status if w else None

    def get_withdraw_request_tx_hash(self, obj: Claim):
        w = self._withdraw(obj)
        return w.request_tx_hash if w else None

    def get_withdraw_finalize_tx_hash(self, obj: Claim):
        w = self._withdraw(obj)
        return w.finalize_tx_hash if w else None

    def get_withdraw_cancel_tx_hash(self, obj: Claim):
        w = self._withdraw(obj)
        return w.cancel_tx_hash if w else None


class SwapRouterWithdrawSerializer(serializers.ModelSerializer):
    class Meta:
        model = SwapRouterWithdraw
        fields = "__all__"
        read_only_fields = [
            "withdraw_key",
            "request_tx_hash",
            "finalize_tx_hash",
            "cancel_tx_hash",
            "pending_amount_handle",
            "pending_ok_handle",
            "pending_request_id",
            "amount_plaintext",
            "amount_sig",
            "ok_plaintext",
            "ok_sig",
            "status",
            "last_error",
            "created_at",
            "updated_at",
        ]