# API Overview

Zalary Wave 3 exposes the backend API surface required to coordinate confidential payroll workflows across employers, employees, encrypted salary allocations, PayrollVault actions, claims, withdrawals, and transaction state.

This document explains the public API groups, what each endpoint does, and how the endpoints fit into the backend payroll lifecycle.

← Back to README

---

## API Purpose

The backend API is the coordination layer between the client/API consumer and the confidential payroll contracts.

It is designed to coordinate:

- employer onboarding
- employee onboarding
- payroll template setup
- payroll run generation
- encrypted salary allocation storage
- PayrollVault transaction actions
- funding and activation state
- employee claim discovery
- claim request and finalization
- SwapRouter withdrawal lifecycle
- transaction status tracking
- background scheduler and reminder flows

The API does not replace the contracts.

It coordinates state around the contracts so payroll can behave like a real product instead of a set of isolated smart contract calls.

---

## Base API Structure

The local API base path used during development/testing is:

~~~text
http://127.0.0.1:8000/api/v1
~~~

Example:

~~~text
GET http://127.0.0.1:8000/api/v1/templates/
~~~

---

## Authentication / API Key

Backend calls can use an API key header.

~~~text
X-API-Key: <API_KEY>
Content-Type: application/json
~~~

Example:

~~~http
X-API-Key: cofhe-local-key
Content-Type: application/json
~~~

The API key is configured through environment variables.

See:

~~~text
.env.example
~~~

---

## Main API Groups

| Group | Purpose |
|---|---|
| Templates | Employer payroll template creation and activation |
| Payroll Runs | Run lifecycle, encrypted allocation upload, funding, activation |
| Employee Claimables | Employee discovery of claimable payroll |
| Claims | Employee claim request, sync, finalization, cancellation |
| Withdrawals | SwapRouter withdrawal request, sync, finalization |
| Chain Config | Active network and deployed contract configuration |
| Onboarding | Employer/employee identity and wallet/email flow |
| Transactions | Chain transaction tracking and status updates |

---

# 1. Templates API

Payroll templates define reusable payroll setup.

A template is the planning layer before an actual payroll run exists.

Templates can represent:

- one-time payroll
- recurring payroll
- instant payroll
- scheduled payroll
- employer payroll group
- employee allocation list

---

## Template Object

A payroll template can include:

| Field | Description |
|---|---|
| `id` | Backend template ID |
| `chain` | Chain record ID |
| `token_address` | Confidential token address |
| `employer_address` | Employer wallet address |
| `title` | Payroll title |
| `description` | Optional payroll description |
| `schedule` | Schedule configuration |
| `employees` | Employee allocation list |
| `status` | Template status |
| `next_run_at` | Next scheduled run time |
| `created_at` | Creation timestamp |
| `updated_at` | Last update timestamp |

---

## Template Statuses

| Status | Meaning |
|---|---|
| `draft` | Template exists but is not active |
| `active` | Template can generate payroll runs |
| `paused` | Template is temporarily stopped |
| `completed` | Template is no longer generating runs |

---

## `GET /templates/`

Returns payroll templates.

### Purpose

Used by the employer dashboard/API consumer to list payroll templates.

### Example Request

~~~http
GET /api/v1/templates/
~~~

### Expected Response

~~~json
[
  {
    "id": 1,
    "title": "April Core Team Payroll",
    "employer_address": "0x...",
    "token_address": "0x...",
    "status": "active",
    "next_run_at": "2026-05-03T12:00:00Z"
  }
]
~~~

### Why it matters

Employers need to see the payroll structures they have created.

---

## `POST /templates/`

Creates a new payroll template.

### Purpose

Used when an employer creates a payroll setup with employees, schedule, and token information.

### Example Request

~~~http
POST /api/v1/templates/
~~~

### Example Body

~~~json
{
  "chain": 1,
  "token_address": "0xConfidentialToken",
  "employer_address": "0xEmployerWallet",
  "title": "Real CoFHE Payroll Test",
  "schedule": {
    "type": "instant",
    "start_at": "2026-05-03T12:00:00Z"
  },
  "employees": [
    {
      "employee_address": "0x1111111111111111111111111111111111111111",
      "amount_atomic": 5000
    },
    {
      "employee_address": "0x2222222222222222222222222222222222222222",
      "amount_atomic": 5000
    }
  ]
}
~~~

### Expected Response

~~~json
{
  "id": 1,
  "title": "Real CoFHE Payroll Test",
  "status": "draft",
  "employee_count": 2
}
~~~

### Used In Test

The real confidential-input test creates a payroll template before activating it and generating a run.

### Why it matters

This is the first backend step in the employer payroll lifecycle.

---

## `GET /templates/{id}/`

Returns a single payroll template.

### Purpose

Used to inspect one template and its current configuration.

### Example Request

~~~http
GET /api/v1/templates/1/
~~~

### Expected Response

~~~json
{
  "id": 1,
  "title": "Real CoFHE Payroll Test",
  "status": "active",
  "employer_address": "0xEmployerWallet",
  "token_address": "0xConfidentialToken"
}
~~~

---

## `POST /templates/{id}/activate/`

Activates a payroll template.

### Purpose

Moves a template from draft/inactive state into an active state so that payroll runs can be generated.

### Example Request

~~~http
POST /api/v1/templates/1/activate/
~~~

### Expected Response

~~~json
{
  "id": 1,
  "status": "active"
}
~~~

### Used In Test

The real confidential-input test activates the template before creating the payroll run.

### Why it matters

Only active templates should be eligible to generate payroll runs.

---

## `GET /templates/{id}/preview_runs/`

Previews upcoming payroll runs for a template.

### Purpose

Allows the backend/client to show upcoming scheduled payroll runs before creating them.

### Example Request

~~~http
GET /api/v1/templates/1/preview_runs/
~~~

### Expected Response

~~~json
{
  "template_id": 1,
  "upcoming_runs": [
    {
      "run_at": "2026-05-03T12:00:00Z",
      "deadline": "2026-05-10T12:00:00Z"
    }
  ]
}
~~~

### Why it matters

Employers should understand upcoming payroll schedules before activation or execution.

---

## `POST /templates/{id}/create_next_run/`

Creates the next payroll run from a template.

### Purpose

Turns an active template into an executable payroll run.

### Example Request

~~~http
POST /api/v1/templates/1/create_next_run/
~~~

### Example Body

~~~json
{
  "deadline_seconds": 604800
}
~~~

### Expected Response

~~~json
{
  "id": 15,
  "template": 1,
  "status": "scheduled",
  "employee_count": 2
}
~~~

### Used In Test

The real confidential-input test creates a payroll run after template activation.

### Why it matters

This creates the backend object that later maps to an on-chain PayrollVault payroll.

---

# 2. Payroll Runs API

A payroll run is one executable payroll cycle.

A run moves through the backend and contract lifecycle:

~~~text
scheduled
  → created
  → alloc_uploaded
  → alloc_finalized
  → funded
  → active
  → closed
~~~

---

## Payroll Run Object

A payroll run can include:

| Field | Description |
|---|---|
| `id` | Backend run ID |
| `template` | Related payroll template |
| `chain` | Chain record |
| `token_address` | Confidential token address |
| `employer_address` | Employer wallet |
| `run_at` | Scheduled run time |
| `deadline` | Claim deadline |
| `employee_count` | Number of employees |
| `required_total_atomic` | Total required funding metadata |
| `onchain_payroll_id` | PayrollVault payroll ID |
| `status` | Run lifecycle status |
| `create_tx_hash` | createPayroll transaction |
| `upload_tx_hash` | uploadAllocations transaction |
| `finalize_tx_hash` | finalizeAllocations transaction |
| `fund_tx_hash` | fundPayroll transaction |
| `activate_tx_hash` | activatePayroll transaction |
| `last_error` | Last backend/worker/chain error |

---

## `GET /runs/`

Returns payroll runs.

### Purpose

Used to list payroll runs for employer dashboards, admin views, and backend review.

### Example Request

~~~http
GET /api/v1/runs/
~~~

### Expected Response

~~~json
[
  {
    "id": 15,
    "template": 1,
    "status": "active",
    "onchain_payroll_id": 4,
    "employee_count": 2
  }
]
~~~

---

## `GET /runs/{id}/`

Returns one payroll run.

### Purpose

Used to poll run state after blockchain transactions.

### Example Request

~~~http
GET /api/v1/runs/15/
~~~

### Expected Response

~~~json
{
  "id": 15,
  "status": "funded",
  "onchain_payroll_id": 4,
  "create_tx_hash": "0x...",
  "fund_tx_hash": "0x..."
}
~~~

### Used In Test

The real confidential-input test repeatedly polls this endpoint to confirm run state progression after transactions.

### Why it matters

The backend must confirm whether a payroll run has moved from created to uploaded, finalized, funded, and active.

---

## `POST /runs/{id}/set_ciphertexts/`

Stores encrypted salary payloads for employee allocations.

### Purpose

Connects real CoFHE encrypted salary inputs to the backend run allocation rows.

### Example Request

~~~http
POST /api/v1/runs/15/set_ciphertexts/
~~~

### Example Body

~~~json
{
  "allocations": [
    {
      "employee_address": "0x1111111111111111111111111111111111111111",
      "encrypted_amount": {
        "ctHash": "0x...",
        "handles": ["0x..."],
        "inputProof": "0x..."
      }
    },
    {
      "employee_address": "0x2222222222222222222222222222222222222222",
      "encrypted_amount": {
        "ctHash": "0x...",
        "handles": ["0x..."],
        "inputProof": "0x..."
      }
    }
  ]
}
~~~

### Expected Response

~~~json
{
  "updated": 2
}
~~~

### Used In Test

The real confidential-input test stores Alice and Bob’s real encrypted salary payloads through this endpoint.

### Why it matters

Payroll cannot upload allocations until every employee has an encrypted salary payload.

---

## `GET /runs/{id}/missing_ciphertexts/`

Checks whether any run allocation is missing encrypted salary data.

### Purpose

Prevents allocation upload from starting with incomplete encrypted salary data.

### Example Request

~~~http
GET /api/v1/runs/15/missing_ciphertexts/
~~~

### Expected Response

~~~json
{
  "missing": []
}
~~~

### Used In Test

The real confidential-input test confirms there are no missing ciphertexts before `uploadAllocations`.

### Why it matters

This protects payroll integrity before on-chain upload.

---

## `GET /runs/{id}/funding_quote/`

Returns funding quote information for a payroll run.

### Purpose

Helps the employer/client understand the amount required to fund the payroll run.

### Example Request

~~~http
GET /api/v1/runs/15/funding_quote/
~~~

### Expected Response

~~~json
{
  "run_id": 15,
  "employee_count": 2,
  "required_total_atomic": 10000,
  "token_address": "0xConfidentialToken"
}
~~~

### Why it matters

Employers need funding context before submitting confidential funding inputs.

---

## `GET /runs/{id}/funding_context/`

Returns funding context for the payroll run.

### Purpose

Provides the contextual data needed by the client/API consumer to prepare a funding action.

### Example Request

~~~http
GET /api/v1/runs/15/funding_context/
~~~

### Expected Response

~~~json
{
  "run_id": 15,
  "onchain_payroll_id": 4,
  "employer_address": "0xEmployerWallet",
  "token_address": "0xConfidentialToken"
}
~~~

---

## `POST /runs/{id}/create_payroll/`

Broadcasts the PayrollVault `createPayroll` action through the worker interface.

### Purpose

Creates the on-chain PayrollVault payroll record that corresponds to the backend payroll run.

### Example Request

~~~http
POST /api/v1/runs/15/create_payroll/
~~~

### Expected Response

~~~json
{
  "tx_hash": "0x..."
}
~~~

### Used In Test

The real confidential-input test calls this endpoint and waits for the transaction to mine.

### Expected State Change

~~~text
scheduled → created
~~~

### Why it matters

This links the backend payroll run to an on-chain payroll ID.

---

## `POST /runs/{id}/upload_allocations/`

Broadcasts encrypted employee salary allocations to PayrollVault.

### Purpose

Uploads the encrypted salary payloads for employees in the run.

### Example Request

~~~http
POST /api/v1/runs/15/upload_allocations/
~~~

### Example Body

~~~json
{
  "idempotency_key": "real-chunk-123456",
  "employee_addresses": [
    "0x1111111111111111111111111111111111111111",
    "0x2222222222222222222222222222222222222222"
  ],
  "encrypted_amounts": [
    {
      "ctHash": "0x...",
      "handles": ["0x..."],
      "inputProof": "0x..."
    },
    {
      "ctHash": "0x...",
      "handles": ["0x..."],
      "inputProof": "0x..."
    }
  ]
}
~~~

### Expected Response

~~~json
{
  "tx_hash": "0x..."
}
~~~

### Used In Test

The real confidential-input test uploads Alice and Bob’s real encrypted salaries.

### Expected State Change

~~~text
created → alloc_uploaded
~~~

### Why it matters

This is the main encrypted salary allocation upload step.

---

## `POST /runs/{id}/finalize_allocations/`

Finalizes uploaded allocations.

### Purpose

Confirms that the payroll allocation set is complete and ready for funding.

### Example Request

~~~http
POST /api/v1/runs/15/finalize_allocations/
~~~

### Expected Response

~~~json
{
  "tx_hash": "0x..."
}
~~~

### Used In Test

The real confidential-input test finalizes allocations after upload.

### Expected State Change

~~~text
alloc_uploaded → alloc_finalized
~~~

### Why it matters

Payroll should not move to funding until allocation setup is finalized.

---

## `POST /runs/{id}/fund_payroll/`

Funds the payroll using a real encrypted funding input.

### Purpose

Coordinates PayrollVault `fundPayroll`.

### Example Request

~~~http
POST /api/v1/runs/15/fund_payroll/
~~~

### Example Body

~~~json
{
  "encrypted_amount": {
    "ctHash": "0x...",
    "handles": ["0x..."],
    "inputProof": "0x..."
  }
}
~~~

### Expected Response

~~~json
{
  "tx_hash": "0x..."
}
~~~

### Used In Test

The real confidential-input test encrypts a funding amount and submits it through this endpoint.

### Expected State Change

~~~text
alloc_finalized → funded
~~~

### Why it matters

Funding uses confidential inputs rather than public salary totals.

---

## `GET /runs/{id}/funded_once_handle/`

Returns the fundedOnce encrypted handle required for activation.

### Purpose

Provides the handle needed for proof-backed activation.

### Example Request

~~~http
GET /api/v1/runs/15/funded_once_handle/
~~~

### Expected Response

~~~json
{
  "funded_once_handle": "0x..."
}
~~~

### Used In Test

The real confidential-input test reads this handle and runs a real `decryptForTx` proof flow.

### Why it matters

Activation should depend on proof-backed funding state.

---

## `POST /runs/{id}/activate_payroll/`

Activates the payroll after funding proof.

### Purpose

Coordinates PayrollVault `activatePayroll`.

### Example Request

~~~http
POST /api/v1/runs/15/activate_payroll/
~~~

### Example Body

~~~json
{
  "funded_plaintext": true,
  "funded_sig": "0x..."
}
~~~

### Expected Response

~~~json
{
  "tx_hash": "0x..."
}
~~~

### Used In Test

The real confidential-input test activates payroll using a real fundedOnce proof result.

### Expected State Change

~~~text
funded → active
~~~

### Why it matters

This is the boundary where payroll becomes claimable by employees.

---

# 3. Employee Claimables API

Employee claimables let an employee discover available payroll claims by wallet address.

---

## `GET /employees/{address}/claimables/`

Returns claimable payroll records for an employee address.

### Purpose

Allows an employee to see salary claims available to their wallet.

### Example Request

~~~http
GET /api/v1/employees/0x1111111111111111111111111111111111111111/claimables/
~~~

### Expected Response

~~~json
[
  {
    "run_id": 15,
    "claim_id": 27,
    "employer_address": "0xEmployerWallet",
    "status": "available",
    "deadline": "2026-05-10T12:00:00Z"
  }
]
~~~

### Why it matters

Employees should not manually search for payroll IDs.

The backend should answer:

~~~text
What salary claims are available for this wallet?
~~~

---

# 4. Claims API

Claims coordinate the employee salary claim lifecycle.

A claim can move through states similar to:

~~~text
available
  → requested
  → pending
  → finalized
~~~

or:

~~~text
available
  → requested
  → pending
  → cancelled/retryable
~~~

---

## Claim Object

A claim record can include:

| Field | Description |
|---|---|
| `id` | Claim ID |
| `run` | Payroll run |
| `employee_address` | Employee wallet |
| `request_tx_hash` | requestClaim transaction |
| `finalize_tx_hash` | finalizeClaim transaction |
| `cancel_tx_hash` | cancel transaction |
| `pending_request_id` | Pending request ID |
| `pending_handles` | Pending encrypted handles |
| `status` | Claim lifecycle state |
| `last_error` | Last error |

---

## `GET /claims/`

Returns claim records.

### Example Request

~~~http
GET /api/v1/claims/
~~~

### Expected Response

~~~json
[
  {
    "id": 27,
    "run": 15,
    "employee_address": "0x1111111111111111111111111111111111111111",
    "status": "available"
  }
]
~~~

---

## `GET /claims/{id}/`

Returns a single claim record.

### Example Request

~~~http
GET /api/v1/claims/27/
~~~

### Expected Response

~~~json
{
  "id": 27,
  "run": 15,
  "employee_address": "0x1111111111111111111111111111111111111111",
  "status": "pending",
  "request_tx_hash": "0x..."
}
~~~

---

## `POST /claims/{id}/submit_request_claim/`

Starts the employee claim request.

### Purpose

Coordinates PayrollVault `requestClaim`.

### Example Request

~~~http
POST /api/v1/claims/27/submit_request_claim/
~~~

### Expected Response

~~~json
{
  "tx_hash": "0x..."
}
~~~

### Expected State Change

~~~text
available → requested / pending
~~~

### Why it matters

This starts the confidential salary claim flow.

---

## `POST /claims/{id}/sync_pending/`

Syncs pending claim state.

### Purpose

Reads and stores pending claim request data needed for finalization or cancellation.

### Example Request

~~~http
POST /api/v1/claims/27/sync_pending/
~~~

### Expected Response

~~~json
{
  "status": "pending",
  "pending_request_id": "..."
}
~~~

### Why it matters

Claim state must be resumable after refreshes, delays, or multi-step proof flows.

---

## `POST /claims/{id}/submit_finalize_claim/`

Finalizes a successful claim.

### Purpose

Coordinates PayrollVault `finalizeClaim`.

### Example Request

~~~http
POST /api/v1/claims/27/submit_finalize_claim/
~~~

### Example Body

~~~json
{
  "claim_plaintext": true,
  "claim_sig": "0x..."
}
~~~

### Expected Response

~~~json
{
  "tx_hash": "0x..."
}
~~~

### Expected State Change

~~~text
pending → finalized
~~~

### Why it matters

This completes the employee salary claim.

---

## `POST /claims/{id}/submit_cancel_claim/`

Cancels a pending claim.

### Purpose

Coordinates the cancellation path for failed/stuck/retryable claims.

### Example Request

~~~http
POST /api/v1/claims/27/submit_cancel_claim/
~~~

### Expected Response

~~~json
{
  "tx_hash": "0x..."
}
~~~

### Expected State Change

~~~text
pending → cancelled / retryable
~~~

### Why it matters

Confidential operations can require retry paths.

The backend must prevent employees from getting stuck in pending claim state.

---

# 5. SwapRouter Withdrawals API

Withdrawals coordinate the movement from confidential salary balance back to public USDC.

A withdrawal can move through states similar to:

~~~text
created
  → requested
  → pending
  → finalized
~~~

---

## Withdrawal Object

A withdrawal record can include:

| Field | Description |
|---|---|
| `id` | Withdrawal ID |
| `user_address` | Employee/user wallet |
| `withdraw_key` | Unique withdrawal key |
| `request_tx_hash` | requestWithdraw transaction |
| `finalize_tx_hash` | finalizeWithdraw transaction |
| `pending_amount_handle` | Pending encrypted amount handle |
| `pending_ok_handle` | Pending ok handle |
| `pending_request_id` | Pending request ID |
| `plaintext_amount` | Plaintext amount when available |
| `status` | Withdrawal lifecycle state |
| `last_error` | Last error |

---

## `GET /swaprouter/withdraws/`

Returns withdrawal records.

### Example Request

~~~http
GET /api/v1/swaprouter/withdraws/
~~~

### Expected Response

~~~json
[
  {
    "id": 4,
    "user_address": "0x1111111111111111111111111111111111111111",
    "status": "pending"
  }
]
~~~

---

## `GET /swaprouter/withdraws/{id}/`

Returns one withdrawal record.

### Example Request

~~~http
GET /api/v1/swaprouter/withdraws/4/
~~~

### Expected Response

~~~json
{
  "id": 4,
  "user_address": "0x1111111111111111111111111111111111111111",
  "status": "pending",
  "request_tx_hash": "0x..."
}
~~~

---

## `POST /swaprouter/withdraws/{id}/submit_request/`

Starts a withdrawal request.

### Purpose

Coordinates SwapRouter `requestWithdraw`.

### Example Request

~~~http
POST /api/v1/swaprouter/withdraws/4/submit_request/
~~~

### Expected Response

~~~json
{
  "tx_hash": "0x..."
}
~~~

### Expected State Change

~~~text
created → requested / pending
~~~

### Why it matters

This starts the withdrawal path from confidential balance to public USDC.

---

## `POST /swaprouter/withdraws/{id}/sync_pending/`

Syncs pending withdrawal state.

### Purpose

Stores pending withdrawal handles and request IDs needed for finalization.

### Example Request

~~~http
POST /api/v1/swaprouter/withdraws/4/sync_pending/
~~~

### Expected Response

~~~json
{
  "status": "pending",
  "pending_request_id": "..."
}
~~~

### Why it matters

Withdrawal is a multi-step confidential flow and must be resumable.

---

## `POST /swaprouter/withdraws/{id}/submit_finalize/`

Finalizes a withdrawal.

### Purpose

Coordinates SwapRouter `finalizeWithdraw`.

### Example Request

~~~http
POST /api/v1/swaprouter/withdraws/4/submit_finalize/
~~~

### Example Body

~~~json
{
  "amount_plaintext": "5000",
  "amount_sig": "0x...",
  "ok_plaintext": true,
  "ok_sig": "0x..."
}
~~~

### Expected Response

~~~json
{
  "tx_hash": "0x..."
}
~~~

### Expected State Change

~~~text
pending → finalized
~~~

### Why it matters

This completes the salary withdrawal path.

---

# 6. Chain Configuration API

The chain configuration layer supports active network and contract settings.

The backend needs access to:

- chain ID
- RPC URL
- deployed contract addresses
- confirmation requirements
- active/inactive status

Possible chain configuration fields:

| Field | Description |
|---|---|
| `chain_id` | Network chain ID |
| `name` | Network name |
| `rpc_url` | RPC endpoint |
| `usdc_address` | USDC token address |
| `confidential_token_address` | cUSDC/ConfidentialToken address |
| `payroll_vault_address` | PayrollVault address |
| `swap_router_address` | SwapRouter address |
| `confirmations_required` | Required confirmations |
| `is_active` | Whether the network is active |

---

# 7. Onboarding API

The onboarding module supports role-aware employer and employee setup.

The onboarding layer is designed to support:

- employer wallet onboarding
- employee wallet onboarding
- email capture
- email verification
- wallet verification
- onboarding token flow
- role-aware access

## Employer Onboarding Purpose

Employer onboarding prepares the backend to associate payroll templates and payroll runs with the employer’s wallet/profile.

## Employee Onboarding Purpose

Employee onboarding prepares the backend to associate claim discovery and claim actions with an employee wallet/profile.

---

# 8. Transaction Tracking API

Transaction tracking supports asynchronous chain status.

Payroll actions are not complete just because an API call returned a transaction hash.

The backend must track:

- transaction intent
- transaction hash
- pending state
- receipt state
- finality state
- failed/reverted/replaced state
- related payroll/claim/withdrawal object

## Transaction lifecycle

~~~text
created
  → submitted
  → pending
  → confirmed
  → finalized
~~~

Failure paths:

~~~text
submitted
  → failed
  → reverted
  → replaced
~~~

## Why it matters

Payroll is high-trust infrastructure.

The backend must know whether each payroll transaction actually succeeded.

---

# 9. End-to-End API Flow

## Employer Setup to Payroll Activation

~~~text
POST /templates/
  ↓
POST /templates/{id}/activate/
  ↓
POST /templates/{id}/create_next_run/
  ↓
POST /runs/{id}/set_ciphertexts/
  ↓
GET /runs/{id}/missing_ciphertexts/
  ↓
POST /runs/{id}/create_payroll/
  ↓
POST /runs/{id}/upload_allocations/
  ↓
POST /runs/{id}/finalize_allocations/
  ↓
POST /runs/{id}/fund_payroll/
  ↓
GET /runs/{id}/funded_once_handle/
  ↓
POST /runs/{id}/activate_payroll/
  ↓
GET /runs/{id}/
~~~

---

## Employee Claim Flow

~~~text
GET /employees/{address}/claimables/
  ↓
GET /claims/{id}/
  ↓
POST /claims/{id}/submit_request_claim/
  ↓
POST /claims/{id}/sync_pending/
  ↓
POST /claims/{id}/submit_finalize_claim/
~~~

Retry path:

~~~text
POST /claims/{id}/submit_cancel_claim/
  ↓
POST /claims/{id}/submit_request_claim/
~~~

---

## Withdrawal Flow

~~~text
GET /swaprouter/withdraws/{id}/
  ↓
POST /swaprouter/withdraws/{id}/submit_request/
  ↓
POST /swaprouter/withdraws/{id}/sync_pending/
  ↓
POST /swaprouter/withdraws/{id}/submit_finalize/
~~~

---

# 10. Endpoints Proven by Real Confidential Input Test

The Wave 3 real confidential-input test validates these endpoints:

| Endpoint | Proven |
|---|---|
| `GET /templates/` | ✅ |
| `POST /templates/` | ✅ |
| `POST /templates/{id}/activate/` | ✅ |
| `POST /templates/{id}/create_next_run/` | ✅ |
| `POST /runs/{id}/set_ciphertexts/` | ✅ |
| `GET /runs/{id}/missing_ciphertexts/` | ✅ |
| `POST /runs/{id}/create_payroll/` | ✅ |
| `POST /runs/{id}/upload_allocations/` | ✅ |
| `POST /runs/{id}/finalize_allocations/` | ✅ |
| `POST /runs/{id}/fund_payroll/` | ✅ |
| `GET /runs/{id}/funded_once_handle/` | ✅ |
| `POST /runs/{id}/activate_payroll/` | ✅ |
| `GET /runs/{id}/` | ✅ |

See:

~~~text
docs/TESTS.md
~~~

---

# 11. Why This API Matters

A confidential payroll product needs more than contract calls.

It needs backend APIs for:

- setup
- scheduling
- encryption payload handling
- transaction orchestration
- claim discovery
- claim finalization
- withdrawal handling
- state recovery
- background processing

This API surface is the application layer that makes the confidential payroll protocol usable.

Wave 2 proved the contracts.

Wave 3 proves the backend API flow that drives them.