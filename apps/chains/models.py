from __future__ import annotations

from django.db import models


class Chain(models.Model):
    chain_id   = models.IntegerField(unique=True)
    name       = models.CharField(max_length=64)
    rpc_url    = models.CharField(max_length=256)

    # Contract addresses
    usdc_address              = models.CharField(max_length=42, blank=True)
    confidentialtoken_address = models.CharField(max_length=42, blank=True)
    payrollvault_address      = models.CharField(max_length=42, blank=True)
    swaprouter_address        = models.CharField(max_length=42, blank=True)

    confirmations_required = models.PositiveIntegerField(default=3)
    reorg_finality_buffer  = models.PositiveIntegerField(default=12)
    is_active              = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.name} ({self.chain_id})"