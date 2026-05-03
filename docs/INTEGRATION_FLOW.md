# Integration Flow

This document explains how Zalary’s Wave 3 backend coordinates the flow between the client/API consumer, Django API, viem worker, CoFHE SDK inputs, and deployed payroll contracts.

← Back to README

---

## Integration Summary

Zalary’s backend integration flow is built around one core idea:

> The backend should coordinate payroll state while the contracts enforce confidential payroll execution.

The flow connects:

- client/API actions
- encrypted CoFHE inputs
- Django REST endpoints
- backend data model
- viem worker calls
- PayrollVault transactions
- SwapRouter transactions
- transaction receipt polling
- payroll/claim/withdrawal state updates

---

## High-Level Flow

```text
User/client action
        │
        ▼
API request
        │
        ▼
Django REST API
        │
        ▼
Backend state validation
        │
        ▼
Worker interface
        │
        ▼
Contract transaction
        │
        ▼
Transaction hash stored
        │
        ▼
Receipt/finality sync
        │
        ▼
Backend lifecycle state updated
```

---

# 1. Employer Setup Integration

The employer setup flow starts with payroll template creation.

## Flow

```text
Employer/API consumer
        │
        ▼
POST /templates/
        │
        ▼
Backend creates PayrollTemplate
        │
        ▼
Backend stores employee allocation rows
        │
        ▼
POST /templates/{id}/activate/
        │
        ▼
Template becomes active
```

## Integration Purpose

This flow creates the backend foundation for payroll execution.

No on-chain payroll exists yet.

The backend is only preparing the payroll structure.

---

# 2. Payroll Run Integration

A payroll run is generated from a template.

## Flow

```text
Active PayrollTemplate
        │
        ▼
POST /templates/{id}/create_next_run/
        │
        ▼
Backend creates PayrollRun
        │
        ▼
Backend copies employee allocations into run allocations
        │
        ▼
Run waits for encrypted salary payloads
```

## Integration Purpose

The run is the backend object that maps to one on-chain PayrollVault payroll.

It becomes the anchor for:

- encrypted allocation storage
- createPayroll
- uploadAllocations
- finalizeAllocations
- fundPayroll
- activatePayroll
- employee claims

---

# 3. Encrypted Salary Input Integration

The client/API consumer prepares encrypted salary inputs using CoFHE-compatible SDK flows.

## Flow

```text
Employee salaries
        │
        ▼
CoFHE SDK encryption
        │
        ▼
Encrypted salary payloads
        │
        ▼
POST /runs/{id}/set_ciphertexts/
        │
        ▼
Backend attaches payloads to run allocations
        │
        ▼
GET /runs/{id}/missing_ciphertexts/
        │
        ▼
Backend confirms all ciphertexts are present
```

## Integration Purpose

This connects off-chain payroll setup to confidential on-chain payroll input.

The backend does not need to expose salary values publicly.

It stores the encrypted payload references needed for contract upload.

---

# 4. createPayroll Integration

The backend creates an on-chain payroll record through the worker.

## Flow

```text
PayrollRun ready
        │
        ▼
POST /runs/{id}/create_payroll/
        │
        ▼
Django validates run state
        │
        ▼
Django calls viem worker interface
        │
        ▼
Worker broadcasts PayrollVault.createPayroll
        │
        ▼
tx_hash returned
        │
        ▼
Backend stores create tx hash
        │
        ▼
Backend waits/syncs receipt
        │
        ▼
Backend stores onchain_payroll_id
```

## State Change

```text
scheduled → created
```

## Integration Purpose

This is the bridge between a backend payroll run and an on-chain PayrollVault payroll.

---

# 5. uploadAllocations Integration

The backend uploads encrypted salary allocations.

## Flow

```text
Run status: created
        │
        ▼
Encrypted allocations ready
        │
        ▼
POST /runs/{id}/upload_allocations/
        │
        ▼
Backend validates allocation payloads
        │
        ▼
Backend calls viem worker
        │
        ▼
Worker broadcasts PayrollVault.uploadAllocations
        │
        ▼
tx_hash returned
        │
        ▼
Backend stores upload tx hash
        │
        ▼
Backend marks allocations uploaded after receipt/finality
```

## State Change

```text
created → alloc_uploaded
```

## Integration Purpose

This proves that real confidential salary inputs can move from backend state into the contract flow.

---

# 6. finalizeAllocations Integration

The backend finalizes allocation upload.

## Flow

```text
Run status: alloc_uploaded
        │
        ▼
POST /runs/{id}/finalize_allocations/
        │
        ▼
Backend calls viem worker
        │
        ▼
Worker broadcasts PayrollVault.finalizeAllocations
        │
        ▼
tx_hash returned
        │
        ▼
Backend stores finalize tx hash
        │
        ▼
Backend updates run state
```

## State Change

```text
alloc_uploaded → alloc_finalized
```

## Integration Purpose

Finalization creates a clean boundary between allocation setup and payroll funding.

---

# 7. fundPayroll Integration

The backend coordinates encrypted payroll funding.

## Flow

```text
Run status: alloc_finalized
        │
        ▼
Client/API consumer prepares encrypted funding input
        │
        ▼
POST /runs/{id}/fund_payroll/
        │
        ▼
Backend validates run state
        │
        ▼
Backend calls viem worker
        │
        ▼
Worker broadcasts PayrollVault.fundPayroll
        │
        ▼
tx_hash returned
        │
        ▼
Backend stores fund tx hash
        │
        ▼
Backend updates run state after confirmation
```

## State Change

```text
alloc_finalized → funded
```

## Integration Purpose

Payroll funding uses confidential encrypted input rather than public salary totals.

---

# 8. Activation Proof Integration

After funding, activation requires proof-backed validation.

## Flow

```text
Run status: funded
        │
        ▼
GET /runs/{id}/funded_once_handle/
        │
        ▼
Backend returns fundedOnce handle
        │
        ▼
Client/API consumer performs decryptForTx/proof flow
        │
        ▼
POST /runs/{id}/activate_payroll/
        │
        ▼
Backend calls viem worker
        │
        ▼
Worker broadcasts PayrollVault.activatePayroll
        │
        ▼
tx_hash returned
        │
        ▼
Backend stores activation tx hash
        │
        ▼
Run becomes active after confirmation
```

## State Change

```text
funded → active
```

## Integration Purpose

Activation makes payroll claimable by employees.

---

# 9. Employee Claim Discovery Integration

Employees discover claimable payroll by wallet address.

## Flow

```text
Employee/API consumer
        │
        ▼
GET /employees/{address}/claimables/
        │
        ▼
Backend checks active payroll runs
        │
        ▼
Backend checks employee allocations
        │
        ▼
Backend returns claimable records
```

## Integration Purpose

Employees should not need to manually know payroll IDs.

The backend returns claimable salary records for the connected wallet.

---

# 10. Claim Request Integration

Employee claim starts with a request.

## Flow

```text
Claimable payroll exists
        │
        ▼
POST /claims/{id}/submit_request_claim/
        │
        ▼
Backend creates/updates ClaimRecord
        │
        ▼
Backend calls viem worker
        │
        ▼
Worker broadcasts PayrollVault.requestClaim
        │
        ▼
Backend stores request tx hash
        │
        ▼
Claim moves into requested/pending state
```

## Integration Purpose

This starts the confidential salary claim lifecycle.

---

# 11. Claim Sync Integration

Pending claim data must be synchronized before finalization.

## Flow

```text
Claim request submitted
        │
        ▼
POST /claims/{id}/sync_pending/
        │
        ▼
Backend reads pending claim state
        │
        ▼
Backend stores pending request/handles
        │
        ▼
Claim can move to finalization path
```

## Integration Purpose

This makes the claim flow resumable.

The user can refresh or return later without losing claim state.

---

# 12. Claim Finalization Integration

Finalization completes a successful claim.

## Flow

```text
Claim pending
        │
        ▼
Client/API consumer prepares proof-backed result
        │
        ▼
POST /claims/{id}/submit_finalize_claim/
        │
        ▼
Backend calls viem worker
        │
        ▼
Worker broadcasts PayrollVault.finalizeClaim
        │
        ▼
Backend stores finalize tx hash
        │
        ▼
Claim becomes finalized
```

## Integration Purpose

This completes the employee salary claim.

---

# 13. Claim Cancellation / Retry Integration

A pending claim can be cancelled if it needs retry.

## Flow

```text
Claim pending
        │
        ▼
POST /claims/{id}/submit_cancel_claim/
        │
        ▼
Backend calls worker
        │
        ▼
Worker broadcasts cancelPendingClaim
        │
        ▼
Backend clears pending claim state
        │
        ▼
Claim becomes retryable
```

## Integration Purpose

Confidential flows need safe retry paths.

The backend prevents employees from getting stuck.

---

# 14. Withdrawal Request Integration

After claiming salary, an employee may withdraw to public USDC.

## Flow

```text
Employee has confidential balance
        │
        ▼
POST /swaprouter/withdraws/{id}/submit_request/
        │
        ▼
Backend creates/updates withdrawal record
        │
        ▼
Backend calls viem worker
        │
        ▼
Worker broadcasts SwapRouter.requestWithdraw
        │
        ▼
Backend stores request tx hash
        │
        ▼
Withdrawal becomes pending
```

## Integration Purpose

This starts the confidential-to-public withdrawal path.

---

# 15. Withdrawal Sync Integration

Pending withdrawal data must be synchronized.

## Flow

```text
Withdrawal requested
        │
        ▼
POST /swaprouter/withdraws/{id}/sync_pending/
        │
        ▼
Backend reads pending withdrawal state
        │
        ▼
Backend stores pending handles/request ID
        │
        ▼
Withdrawal can move to finalization
```

## Integration Purpose

This makes withdrawal resumable and trackable.

---

# 16. Withdrawal Finalization Integration

Finalization completes the withdrawal.

## Flow

```text
Withdrawal pending
        │
        ▼
Client/API consumer prepares proof-backed result
        │
        ▼
POST /swaprouter/withdraws/{id}/submit_finalize/
        │
        ▼
Backend calls viem worker
        │
        ▼
Worker broadcasts SwapRouter.finalizeWithdraw
        │
        ▼
Backend stores finalize tx hash
        │
        ▼
Withdrawal becomes finalized
```

## Integration Purpose

This completes the salary lifecycle from confidential payroll claim to public USDC withdrawal.

---

# 17. Transaction Sync Integration

Transaction state must be synchronized after worker calls.

## Flow

```text
Worker returns tx_hash
        │
        ▼
Backend stores tx_hash
        │
        ▼
Celery/background sync polls receipt
        │
        ▼
Backend updates transaction status
        │
        ▼
Backend updates related object state
```

## Related Objects

Transaction sync can update:

- payroll run
- claim record
- withdrawal record
- allocation upload state

## Integration Purpose

The backend must know whether transactions succeeded, failed, reverted, or finalized.

---

# 18. Real Confidential Input Test Integration

The Wave 3 confidential-input test validates the key employer-side integration path.

## Tested Path

```text
Django API
  → viem worker
  → CoFHE SDK encrypted salary inputs
  → PayrollVault transactions
  → transaction receipt polling
  → backend run state updates
  → fundedOnce proof
  → payroll activation
```

## Proven Steps

| Step | Proven |
|---|---|
| API readiness | ✅ |
| Worker readiness | ✅ |
| Real salary encryption | ✅ |
| Ciphertext storage | ✅ |
| Payroll creation | ✅ |
| Allocation upload | ✅ |
| Allocation finalization | ✅ |
| Encrypted funding | ✅ |
| fundedOnce proof | ✅ |
| Payroll activation | ✅ |

See:

```text
docs/TESTS.md
```

---

# 19. Full Integration Lifecycle

```text
Employer onboarding
        │
        ▼
Template creation
        │
        ▼
Template activation
        │
        ▼
Run creation
        │
        ▼
Encrypted salary input preparation
        │
        ▼
Ciphertext storage
        │
        ▼
PayrollVault.createPayroll
        │
        ▼
PayrollVault.uploadAllocations
        │
        ▼
PayrollVault.finalizeAllocations
        │
        ▼
PayrollVault.fundPayroll
        │
        ▼
fundedOnce proof
        │
        ▼
PayrollVault.activatePayroll
        │
        ▼
Employee claim discovery
        │
        ▼
PayrollVault.requestClaim
        │
        ▼
PayrollVault.finalizeClaim
        │
        ▼
SwapRouter.requestWithdraw
        │
        ▼
SwapRouter.finalizeWithdraw
```

---

# 20. Why This Integration Matters

Wave 2 proved that the confidential payroll protocol works.

Wave 3 proves that the protocol can be driven by a backend.

That backend must coordinate:

- API requests
- encrypted inputs
- worker calls
- contract transactions
- transaction finality
- payroll state
- claim state
- withdrawal state

This is what turns Zalary from contract infrastructure into payroll infrastructure.