# Backend Architecture

Zalary Wave 3 introduces the backend architecture required to coordinate confidential payroll workflows around the Wave 2 CoFHE smart contract protocol.

← Back to README

---

## Architecture Summary

Zalary is designed as a backend-orchestrated confidential payroll system.

The backend sits between the client/API consumer and the deployed CoFHE contracts.

It coordinates:

- employer onboarding
- employee onboarding
- payroll template setup
- payroll run creation
- encrypted allocation handling
- contract transaction execution
- funding and activation state
- employee claim discovery
- claim request/finalization
- withdrawal lifecycle
- background jobs
- transaction tracking

---

## High-Level Architecture

```text
Client / API Consumer
        │
        ▼
Django REST API
        │
        ▼
Backend Data Model
        │
        ▼
Celery + Redis
        │
        ▼
Viem Worker Interface
        │
        ▼
CoFHE Contracts
        │
        ▼
Base Sepolia
```

---

## Core Layers

| Layer | Responsibility |
|---|---|
| Client / API Consumer | Prepares user actions, wallet flows, encrypted inputs, and API requests |
| Django REST API | Receives payroll, claim, withdrawal, and onboarding requests |
| Backend Data Model | Stores payroll templates, runs, allocations, claims, withdrawals, and transaction state |
| Celery + Redis | Handles background scheduling, reminders, and transaction sync |
| Viem Worker Interface | Bridges backend actions to contract calls |
| CoFHE Contracts | ConfidentialToken, PayrollVault, and SwapRouter |
| Base Sepolia | Testnet execution environment |

---

# 1. Client / API Consumer Layer

The client/API consumer is responsible for initiating user actions and preparing data before sending it to the backend.

This layer may include:

- wallet connection
- employer actions
- employee actions
- encrypted salary input preparation
- proof/decrypt flow coordination
- API requests to the backend

The backend does not assume all payroll actions happen in one browser session.

That is why it stores persistent backend state for payroll runs, claims, withdrawals, and transactions.

---

# 2. Django REST API Layer

The Django REST API is the main application interface.

It exposes endpoints for:

- payroll templates
- payroll runs
- encrypted allocation setup
- funding context
- payroll activation
- employee claimables
- claim lifecycle
- SwapRouter withdrawals
- onboarding
- chain configuration

The API turns user/client actions into backend state transitions.

Example:

```text
POST /templates/
        │
        ▼
Create PayrollTemplate
        │
        ▼
Create employee allocation records
```

Another example:

```text
POST /runs/{id}/create_payroll/
        │
        ▼
Validate run state
        │
        ▼
Call worker interface
        │
        ▼
Store tx hash
        │
        ▼
Update run lifecycle
```

---

# 3. Backend Data Model Layer

The data model is the persistent state layer.

It allows the backend to remember:

- which employer owns a payroll template
- which employees belong to a run
- whether encrypted salary payloads were attached
- whether the payroll was created on-chain
- whether allocations were uploaded
- whether payroll was funded
- whether payroll was activated
- whether an employee requested a claim
- whether a claim is pending/finalized/cancelled
- whether a withdrawal is pending/finalized
- whether a chain transaction succeeded or failed

This is what makes the system resilient.

Payroll cannot depend only on temporary frontend state.

---

## Major Model Groups

| Model Group | Purpose |
|---|---|
| Chain configuration | Network and contract address configuration |
| Payroll templates | Reusable employer payroll setup |
| Payroll runs | Executable payroll cycles |
| Run allocations | Employee salary allocation records |
| Claims | Employee salary claim state |
| Withdrawals | SwapRouter withdrawal state |
| Transactions | Chain transaction tracking |
| Onboarding | Employer and employee setup |

---

# 4. Chain Configuration Layer

The chain configuration layer stores network-specific data.

It can include:

- chain ID
- chain name
- RPC URL
- USDC address
- ConfidentialToken address
- PayrollVault address
- SwapRouter address
- confirmation requirements
- active/inactive status

## Why it matters

A payroll backend should not scatter contract addresses across unrelated files.

A structured chain configuration makes the backend easier to manage and safer to update.

---

# 5. Payroll Template Layer

Payroll templates define reusable payroll structures.

A template can represent:

- one-time payroll
- instant payroll
- recurring payroll
- scheduled payroll
- employer group payroll

Templates include:

- employer wallet
- token address
- payroll title
- schedule
- employees
- allocation metadata
- next run timestamp
- status

## Template Purpose

A template is not the actual on-chain payroll.

It is the backend planning object that can generate payroll runs.

---

# 6. Payroll Run Layer

A payroll run is one payroll execution cycle.

It is the backend object that eventually maps to an on-chain PayrollVault payroll.

A run tracks:

- template relationship
- employer address
- token address
- run time
- claim deadline
- employee count
- required total
- on-chain payroll ID
- create transaction
- upload transaction
- finalize transaction
- fund transaction
- activation transaction
- lifecycle status
- last error

## Why it matters

Every payroll cycle needs its own lifecycle state.

A recurring template can produce many runs.

Each run may have different:

- deadlines
- transaction hashes
- employee claim status
- funding status
- activation state
- errors

---

# 7. Encrypted Allocation Layer

The encrypted allocation layer connects employee payroll records to encrypted salary payloads.

The backend must know:

- which employee belongs to the run
- whether the employee has an encrypted salary input
- whether that encrypted input was uploaded
- whether the allocation was included in the on-chain payroll flow

This layer is important because confidential payroll cannot safely continue if employee salary ciphertexts are missing.

---

# 8. Claim Layer

The claim layer coordinates employee salary claims.

A claim record can track:

- payroll run
- employee wallet
- request transaction
- pending claim state
- pending handles
- finalization transaction
- cancellation transaction
- claim status
- withdrawal relationship
- last error

## Why it matters

Employee claims are not always one-step actions.

The backend makes claims resumable and trackable.

---

# 9. Withdrawal Layer

The withdrawal layer coordinates SwapRouter withdrawal flows.

A withdrawal record can track:

- user wallet
- withdrawal key
- request transaction
- pending amount handle
- pending ok handle
- pending request ID
- proof/finalization payload
- finalization transaction
- status
- last error

## Why it matters

Employees may need to move from confidential salary balance back to public USDC.

The backend tracks the full withdrawal lifecycle instead of leaving it as a manual contract interaction.

---

# 10. Transaction Tracking Layer

Blockchain transactions are asynchronous.

The backend tracks:

- transaction intent
- transaction hash
- pending status
- confirmation status
- finality status
- failure/revert state
- related object type
- related object ID

## Transaction Lifecycle

```text
created
  → submitted
  → pending
  → confirmed
  → finalized
```

Failure paths:

```text
submitted
  → failed
  → reverted
  → replaced
```

## Why it matters

Payroll is high-trust infrastructure.

The backend must know whether each transaction actually succeeded.

---

# 11. Celery + Redis Background Layer

The backend uses a background job layer for tasks that should not depend on one request.

Background tasks include:

- scheduler tick
- payroll run generation
- deadline reminders
- pending claim reminders
- chain transaction synchronization
- status updates

## Scheduler Flow

```text
Celery beat
  → scheduler_tick
  → find active templates due for run
  → create PayrollRun
  → advance next_run_at
```

## Transaction Sync Flow

```text
Celery worker
  → find pending transactions
  → poll receipt/finality
  → update transaction status
  → update payroll/claim/withdraw state
```

---

# 12. Viem Worker Interface

The viem worker is the backend-to-contract execution bridge.

The worker interface covers:

- `createPayroll`
- `uploadAllocations`
- `finalizeAllocations`
- `fundPayroll`
- `activatePayroll`
- `requestClaim`
- `finalizeClaim`
- `cancelClaim`
- `requestWithdraw`
- `finalizeWithdraw`

## Why it matters

The backend manages application state.

The worker manages contract execution.

This separation keeps payroll orchestration cleaner.

---

# 13. CoFHE Contract Layer

The contract layer is the Wave 2 protocol foundation.

It includes:

- ConfidentialToken
- PayrollVault
- SwapRouter

The backend coordinates calls to these contracts without exposing salary values publicly.

---

# 14. End-to-End Architecture Flow

```text
Employer creates payroll template
        │
        ▼
Backend stores template + employees
        │
        ▼
Scheduler/manual action creates payroll run
        │
        ▼
Client/API consumer prepares encrypted salary inputs
        │
        ▼
Backend stores encrypted allocation payloads
        │
        ▼
Backend calls viem worker
        │
        ▼
Worker broadcasts PayrollVault transactions
        │
        ▼
Backend tracks tx state
        │
        ▼
Payroll becomes active
        │
        ▼
Employee discovers claimable payroll
        │
        ▼
Employee requests/finalizes claim
        │
        ▼
Employee withdraws through SwapRouter if needed
```

---

# 15. Architecture Outcome

Wave 3 proves that Zalary has moved from protocol-only infrastructure to a backend-orchestrated payroll system.

The architecture supports:

- real payroll state
- user onboarding
- encrypted salary workflows
- contract coordination
- background processing
- transaction tracking
- claim and withdrawal lifecycle management

This is the backend foundation required for confidential payroll as a product.