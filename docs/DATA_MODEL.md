# Data Model

This document explains the backend data model used to coordinate Zalary’s Wave 3 confidential payroll flow.

← Back to README

---

## Data Model Purpose

Zalary’s backend needs persistent state because payroll cannot rely only on smart contract calls or client-side memory.

The backend must track:

- employers
- employees
- payroll templates
- payroll runs
- encrypted salary allocations
- on-chain payroll IDs
- claim state
- withdrawal state
- transaction status
- errors and retry paths

The data model turns the confidential payroll protocol into a stateful payroll application.

---

## Model Groups

| Model Group | Purpose |
|---|---|
| Chain configuration | Stores active network and contract addresses |
| Onboarding | Stores employer/employee setup state |
| Payroll template | Stores reusable payroll setup |
| Payroll run | Stores one executable payroll cycle |
| Run allocation | Stores employee allocation for a payroll run |
| Claim record | Stores employee claim lifecycle |
| SwapRouter withdrawal | Stores withdrawal lifecycle |
| Transaction record | Stores blockchain transaction status |

---

# 1. Chain Configuration Model

The chain configuration model stores the network and contract settings used by the backend.

## Fields

| Field | Purpose |
|---|---|
| `chain_id` | Network chain ID |
| `name` | Human-readable network name |
| `rpc_url` | RPC endpoint |
| `usdc_address` | Public USDC token address |
| `confidential_token_address` | ConfidentialToken/cUSDC contract |
| `payroll_vault_address` | PayrollVault contract |
| `swap_router_address` | SwapRouter contract |
| `confirmations_required` | Number of confirmations needed for finality |
| `is_active` | Whether this chain is active |

## Purpose

The chain model prevents the backend from hardcoding contract addresses everywhere.

It gives payroll, claim, withdrawal, and worker logic a shared source of chain configuration.

---

# 2. Onboarding Models

The onboarding layer stores employer and employee setup state.

## Employer Onboarding

Employer onboarding may track:

| Field | Purpose |
|---|---|
| `wallet_address` | Employer wallet |
| `email` | Employer email |
| `company_name` | Employer/company profile |
| `verified_wallet` | Whether wallet verification is complete |
| `verified_email` | Whether email verification is complete |
| `role` | Employer role |
| `created_at` | Onboarding creation time |
| `updated_at` | Last update time |

## Employee Onboarding

Employee onboarding may track:

| Field | Purpose |
|---|---|
| `wallet_address` | Employee wallet |
| `email` | Employee email |
| `verified_wallet` | Wallet verification status |
| `verified_email` | Email verification status |
| `role` | Employee role |
| `created_at` | Onboarding creation time |
| `updated_at` | Last update time |

## Purpose

Onboarding provides identity context.

Payroll actions should not be treated as anonymous requests.

---

# 3. Payroll Template Model

A payroll template is the reusable employer payroll setup.

It exists before a payroll run is generated.

## Fields

| Field | Purpose |
|---|---|
| `id` | Backend template ID |
| `chain` | Related chain configuration |
| `token_address` | Confidential token address |
| `employer_address` | Employer wallet |
| `title` | Payroll title |
| `description` | Optional description |
| `schedule` | Schedule configuration |
| `status` | Template lifecycle state |
| `next_run_at` | Next scheduled run time |
| `created_at` | Creation timestamp |
| `updated_at` | Last update timestamp |

## Template Statuses

| Status | Meaning |
|---|---|
| `draft` | Template is created but not active |
| `active` | Template can generate payroll runs |
| `paused` | Template is temporarily stopped |
| `completed` | Template is no longer used |

## Purpose

Templates allow employers to prepare payroll once and generate payroll runs from it.

A template can support:

- one-time payroll
- instant payroll
- recurring payroll
- scheduled payroll

---

# 4. Template Employee Allocation Model

A template employee allocation stores employee payroll data at the template level.

## Fields

| Field | Purpose |
|---|---|
| `template` | Related payroll template |
| `employee_address` | Employee wallet |
| `employee_name` | Optional employee name |
| `employee_email` | Optional employee email |
| `amount_atomic` | Salary allocation metadata |
| `created_at` | Creation timestamp |
| `updated_at` | Last update timestamp |

## Purpose

Template allocations are copied into run allocations when a payroll run is created.

This allows recurring payrolls to reuse employee setup.

---

# 5. Payroll Run Model

A payroll run is one executable payroll cycle.

It is generated from a payroll template.

## Fields

| Field | Purpose |
|---|---|
| `id` | Backend run ID |
| `template` | Related payroll template |
| `chain` | Related chain configuration |
| `token_address` | Confidential token address |
| `employer_address` | Employer wallet |
| `run_at` | Scheduled run time |
| `deadline` | Claim deadline |
| `employee_count` | Number of employees |
| `required_total_atomic` | Total payroll amount metadata |
| `onchain_payroll_id` | PayrollVault payroll ID |
| `status` | Run lifecycle status |
| `create_tx_hash` | createPayroll transaction |
| `upload_tx_hash` | uploadAllocations transaction |
| `finalize_tx_hash` | finalizeAllocations transaction |
| `fund_tx_hash` | fundPayroll transaction |
| `activate_tx_hash` | activatePayroll transaction |
| `last_error` | Last backend/worker/chain error |
| `created_at` | Creation timestamp |
| `updated_at` | Last update timestamp |

## Payroll Run Statuses

| Status | Meaning |
|---|---|
| `scheduled` | Run exists but no on-chain payroll yet |
| `created` | On-chain payroll created |
| `alloc_uploaded` | Encrypted allocations uploaded |
| `alloc_finalized` | Allocation set finalized |
| `funded` | Payroll funded |
| `active` | Payroll is active and claimable |
| `closed` | Payroll is closed |
| `failed` | Run encountered an unrecovered error |

## Purpose

The payroll run model connects backend payroll operations to the on-chain payroll lifecycle.

---

# 6. Run Allocation Model

A run allocation connects one employee to one payroll run.

## Fields

| Field | Purpose |
|---|---|
| `run` | Related payroll run |
| `employee_address` | Employee wallet |
| `employee_name` | Optional employee name |
| `employee_email` | Optional employee email |
| `amount_atomic` | Salary allocation metadata |
| `encrypted_amount` | Encrypted salary payload reference |
| `uploaded` | Whether allocation was uploaded |
| `upload_tx_hash` | Upload transaction hash |
| `claim_invited_at` | Claim invitation timestamp |
| `claim_reminded_at` | Reminder timestamp |
| `claimed_at` | Claim completion timestamp |
| `created_at` | Creation timestamp |
| `updated_at` | Last update timestamp |

## Purpose

Run allocations are the employee-specific salary records for one payroll cycle.

They allow the backend to track:

- who is included
- whether encrypted salary input exists
- whether allocation was uploaded
- whether the employee has claimed

---

# 7. Claim Record Model

A claim record tracks an employee salary claim.

## Fields

| Field | Purpose |
|---|---|
| `id` | Claim ID |
| `run` | Related payroll run |
| `employee_address` | Employee wallet |
| `allocation` | Related run allocation |
| `status` | Claim lifecycle state |
| `request_tx_hash` | requestClaim transaction |
| `finalize_tx_hash` | finalizeClaim transaction |
| `cancel_tx_hash` | cancel transaction |
| `pending_request_id` | Pending request ID |
| `pending_handles` | Pending encrypted handles |
| `withdrawal` | Related withdrawal if any |
| `last_error` | Last error |
| `created_at` | Creation timestamp |
| `updated_at` | Last update timestamp |

## Claim Statuses

| Status | Meaning |
|---|---|
| `available` | Employee can request claim |
| `requested` | Claim request submitted |
| `pending` | Waiting for proof/finalization |
| `finalized` | Claim completed |
| `cancelled` | Claim cancelled |
| `retryable` | Claim can be retried |
| `failed` | Claim failed |

## Purpose

Claim records make employee claim flows resumable.

If a user refreshes or leaves the client, the backend still knows claim state.

---

# 8. SwapRouter Withdrawal Model

A withdrawal record tracks the employee’s withdrawal from confidential balance to public USDC.

## Fields

| Field | Purpose |
|---|---|
| `id` | Withdrawal ID |
| `user_address` | Employee/user wallet |
| `withdraw_key` | Unique withdrawal key |
| `status` | Withdrawal lifecycle state |
| `request_tx_hash` | requestWithdraw transaction |
| `finalize_tx_hash` | finalizeWithdraw transaction |
| `pending_amount_handle` | Pending encrypted amount handle |
| `pending_ok_handle` | Pending ok handle |
| `pending_request_id` | Pending request ID |
| `plaintext_amount` | Amount revealed through proof flow when available |
| `signature_ref` | Signature/proof reference |
| `last_error` | Last error |
| `created_at` | Creation timestamp |
| `updated_at` | Last update timestamp |

## Withdrawal Statuses

| Status | Meaning |
|---|---|
| `created` | Withdrawal record exists |
| `requested` | Request transaction submitted |
| `pending` | Waiting for proof/finalization |
| `finalized` | Withdrawal completed |
| `cancelled` | Withdrawal cancelled |
| `failed` | Withdrawal failed |

## Purpose

Withdrawals are multi-step confidential flows.

The backend tracks request, sync, proof, and finalization state.

---

# 9. Transaction Record Model

A transaction record tracks blockchain transaction state.

## Fields

| Field | Purpose |
|---|---|
| `id` | Backend transaction ID |
| `chain` | Related chain |
| `tx_hash` | Transaction hash |
| `action` | Payroll/claim/withdraw action |
| `status` | Transaction status |
| `related_type` | Related object type |
| `related_id` | Related object ID |
| `block_number` | Mined block |
| `confirmations` | Confirmation count |
| `finalized_at` | Finality timestamp |
| `error` | Error/revert information |
| `created_at` | Creation timestamp |
| `updated_at` | Last update timestamp |

## Transaction Statuses

| Status | Meaning |
|---|---|
| `created` | Transaction intent exists |
| `submitted` | Transaction hash received |
| `pending` | Waiting for mining/finality |
| `confirmed` | Transaction mined |
| `finalized` | Required confirmations reached |
| `failed` | Transaction failed |
| `reverted` | Contract reverted |
| `replaced` | Transaction was replaced/dropped |

## Purpose

Transaction tracking protects payroll reliability.

The backend should not assume an action succeeded just because a transaction hash exists.

---

# 10. Data Relationships

## Template to Run

```text
PayrollTemplate
        │
        ├── TemplateEmployeeAllocation
        │
        ▼
PayrollRun
        │
        └── RunAllocation
```

## Run to Claims

```text
PayrollRun
        │
        └── RunAllocation
                │
                ▼
             ClaimRecord
```

## Claims to Withdrawals

```text
ClaimRecord
        │
        ▼
SwapRouterWithdraw
```

## Actions to Transactions

```text
PayrollRun / ClaimRecord / SwapRouterWithdraw
        │
        ▼
ChainTransaction
```

---

# 11. Payroll Lifecycle State Model

```text
PayrollTemplate active
        │
        ▼
PayrollRun scheduled
        │
        ▼
PayrollRun created
        │
        ▼
PayrollRun alloc_uploaded
        │
        ▼
PayrollRun alloc_finalized
        │
        ▼
PayrollRun funded
        │
        ▼
PayrollRun active
        │
        ▼
Employee claims
        │
        ▼
Withdrawals
        │
        ▼
Payroll closed
```

---

# 12. Why This Data Model Matters

Confidential payroll is not just about encrypted values.

It also needs reliable operational state.

The backend data model makes it possible to answer:

- Which employer created this payroll?
- Which employees are included?
- Which encrypted salaries are ready?
- Which transaction created the payroll?
- Was allocation upload completed?
- Was payroll funded?
- Was payroll activated?
- Which employees can claim?
- Which claims are pending?
- Which claims are finalized?
- Which withdrawals are pending?
- Which transactions failed?

This is why the data model is central to Wave 3.

Wave 2 proved the protocol.

Wave 3 proves the backend state layer needed to drive the protocol.