"""
PayrollVault log parser interface.
"""

def parse_payroll_created(*args, **kwargs):
    raise NotImplementedError("Public interface only.")


def parse_claim_requested(*args, **kwargs):
    raise NotImplementedError("Public interface only.")


def parse_withdrawal_events(*args, **kwargs):
    raise NotImplementedError("Public interface only.")
