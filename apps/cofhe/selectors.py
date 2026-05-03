from __future__ import annotations

from apps.cofhe.models import RunAllocation, Claim


def employee_claimables(employee: str) -> list[dict]:
    """
    Return payroll runs relevant to this employee.

    Show:
    - active runs that can still be claimed
    - runs that already have a claim row for this employee, even if the run
      later changed out of active
    """
    employee = (employee or "").strip().lower()
    if not employee:
        return []

    allocs = (
        RunAllocation.objects.filter(
            employee_address__iexact=employee,
            run__onchain_payroll_id__isnull=False,
        )
        .select_related("run", "run__template")
        .order_by("-run__run_at", "-run_id")
    )

    out = []

    for alloc in allocs:
        run = alloc.run
        if not run.onchain_payroll_id:
            continue

        claim = (
            Claim.objects.filter(run=run, employee_address__iexact=employee)
            .order_by("-id")
            .first()
        )

        # Keep visible if:
        # - run is still active, or
        # - employee already has a claim row for it
        if run.status != "active" and claim is None:
            continue

        out.append({
            "run_id": run.id,
            "template_id": run.template_id,
            "run_at": run.run_at.isoformat(),
            "deadline_u64": str(run.deadline_u64),
            "onchain_payroll_id": str(run.onchain_payroll_id),
            "token_address": run.template.token_address,
            "run_status": run.status,
            "claim_status": claim.status if claim else "not_started",
            "claim_id": claim.id if claim else None,
        })

    return out