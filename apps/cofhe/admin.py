from django.contrib import admin
from apps.cofhe.models import (
    AllocationUploadChunk,
    Claim,
    ChainTx,
    PayrollRun,
    PayrollTemplate,
    RunAllocation,
    ScheduleConfig,
    SwapRouterWithdraw,
    TemplateEmployee,
)

admin.site.register(ScheduleConfig)
admin.site.register(PayrollTemplate)
admin.site.register(TemplateEmployee)
admin.site.register(PayrollRun)
admin.site.register(RunAllocation)
admin.site.register(AllocationUploadChunk)
admin.site.register(ChainTx)
admin.site.register(Claim)
admin.site.register(SwapRouterWithdraw)