"""
Transaction service interface.
"""

def record_chain_tx(*args, **kwargs):
    raise NotImplementedError("Public interface only.")


def sync_chain_tx(*args, **kwargs):
    raise NotImplementedError("Public interface only.")


def mark_finalized_success(*args, **kwargs):
    raise NotImplementedError("Public interface only.")


def mark_finalized_revert(*args, **kwargs):
    raise NotImplementedError("Public interface only.")
