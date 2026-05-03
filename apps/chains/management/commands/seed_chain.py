from __future__ import annotations

from django.conf import settings
from django.core.management.base import BaseCommand

from apps.chains.models import Chain


def _require_addr(val: str, name: str) -> str:
    v = (val or "").strip()
    if not v or len(v) != 42 or not v.startswith("0x"):
        raise ValueError(f"{name} must be a 20-byte EVM address (got: {v!r})")
    return v


class Command(BaseCommand):
    help = "Seed or update the Base Sepolia chain record with current contract addresses"

    def handle(self, *args, **options):
        chain_id = settings.BASE_SEPOLIA_CHAIN_ID
        rpc_url  = settings.BASE_SEPOLIA_RPC_URL

        ct   = _require_addr(settings.CONFIDENTIALTOKEN_ADDRESS, "CONFIDENTIALTOKEN_ADDRESS")
        pv   = _require_addr(settings.PAYROLLVAULT_ADDRESS,      "PAYROLLVAULT_ADDRESS")
        sr   = _require_addr(settings.SWAPROUTER_ADDRESS,        "SWAPROUTER_ADDRESS")
        usdc = _require_addr(settings.USDC_ADDRESS,              "USDC_ADDRESS")

        obj, created = Chain.objects.update_or_create(
            chain_id=chain_id,
            defaults={
                "name":                       "Base Sepolia",
                "rpc_url":                    rpc_url,
                "usdc_address":               usdc,
                "confidentialtoken_address":  ct,
                "payrollvault_address":       pv,
                "swaprouter_address":         sr,
                "confirmations_required":     settings.CONFIRMATIONS_REQUIRED,
                "is_active":                  True,
            },
        )

        verb = "Created" if created else "Updated"
        self.stdout.write(self.style.SUCCESS(
            f"{verb} Chain id={obj.id} chain_id={obj.chain_id} rpc={obj.rpc_url}\n"
            f"  ConfidentialToken : {obj.confidentialtoken_address}\n"
            f"  PayrollVault      : {obj.payrollvault_address}\n"
            f"  SwapRouter        : {obj.swaprouter_address}\n"
            f"  USDC              : {obj.usdc_address}"
        ))