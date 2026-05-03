# Backend Flow

Wave 3 turns Zalary from a confidential payroll protocol into a backend-orchestrated payroll system.

Wave 2 proved that the smart contracts can hold confidential payroll funds, upload encrypted employee allocations, allow employees to claim salary privately, and support withdrawal through SwapRouter.

Wave 3 adds the backend flow around that protocol.

The backend coordinates the operational work that a real payroll product needs:

- employer onboarding
- employee onboarding
- payroll template setup
- payroll scheduling
- payroll run creation
- encrypted allocation handling
- contract transaction coordination
- funding state
- activation state
- employee claim discovery
- employee claim finalization
- withdrawal lifecycle
- background reminders
- transaction status tracking

---

## High-Level System Flow

~~~text
Client / API Consumer
        │
        ▼
Django REST API
        │
        ▼
Backend Database State
        │
        ▼
Celery + Redis Background Layer
        │
        ▼
Viem Worker Interface
        │
        ▼
CoFHE Contracts
        │
        ▼
Base Sepolia
~~~

The backend is the coordination layer.

It does not replace the contracts. It makes the contracts usable by tracking who is doing what, when payroll should run, what state a payroll is in, and whether each contract transaction has succeeded.

---

## Main Backend Domains

Zalary’s backend flow is organized around six major domains.

| Domain | Purpose |
|---|---|
| Chain configuration | Stores active network and contract configuration |
| Onboarding | Connects employer/employee identity to wallet and email flow |
| Payroll templates | Stores reusable payroll setup |
| Payroll runs | Tracks each executable payroll cycle |
| Claims | Tracks employee claim lifecycle |
| Withdrawals | Tracks SwapRouter withdrawal lifecycle |
| Transactions | Tracks contract transaction status and finality |

---

# 1. Chain Configuration Flow

The chain configuration flow gives the backend a reliable source of truth for network and contract settings.

The backend stores:

- chain ID
- chain name
- RPC URL
- USDC address
- ConfidentialToken address
- PayrollVault address
- SwapRouter address
- confirmation requirements
- active/inactive status

## Why this matters

Payroll actions should not depend on hardcoded contract addresses inside individual services.

The backend needs a structured chain record so that contract interaction can be coordinated consistently across:

- payroll creation
- allocation upload
- funding
- activation
- claims
- withdrawals
- transaction polling

## Flow

~~~text
Environment variables
        │
        ▼
Seed/update chain command
        │
        ▼
Chain database record
        │
        ▼
Payroll / claim / withdraw services
        │
        ▼
Viem worker contract calls
~~~

## Result

The backend becomes network-aware.

If the contract addresses or RPC configuration change, the backend can be updated from configuration instead of rewriting business logic.

---

# 2. Employer Onboarding Flow

Employer onboarding gives the backend context about who is creating payroll.

Payroll should not be treated as anonymous contract interaction. The backend needs to know which employer is connected, which wallet is being used, and whether the employer has completed setup.

## Employer onboarding responsibilities

The onboarding layer is designed to support:

- employer wallet capture
- employer email capture
- company/profile metadata
- wallet verification flow
- email verification flow
- role-aware access
- onboarding session/token handling

## Employer flow

~~~text
Employer opens app/client
        │
        ▼
Employer connects wallet
        │
        ▼
Backend issues/validates onboarding flow
        │
        ▼
Employer submits profile/email data
        │
        ▼
Backend stores onboarding record
        │
        ▼
Employer can access payroll template creation
~~~

## Backend outcome

After onboarding, the backend can associate payroll templates and payroll runs with the employer’s wallet and identity context.

This enables:

- employer-specific dashboards
- employer-specific payroll templates
- employer-specific runs
- safer payroll action authorization
- future audit/admin workflows

---

# 3. Employee Onboarding Flow

Employee onboarding gives the backend context about who can claim payroll.

An employee should be able to connect a wallet and discover claimable salary without seeing every payroll in the system.

## Employee onboarding responsibilities

The onboarding layer is designed to support:

- employee wallet capture
- employee email capture
- wallet verification
- role-aware access
- employee-specific claim discovery

## Employee flow

~~~text
Employee opens app/client
        │
        ▼
Employee connects wallet
        │
        ▼
Backend validates employee onboarding state
        │
        ▼
Employee profile is associated with wallet/email
        │
        ▼
Employee can query claimable payroll
~~~

## Backend outcome

After onboarding, the backend can return claimable payroll records for the employee address.

This enables a clean employee experience:

~~~text
Connect wallet
        │
        ▼
View claimable payroll
        │
        ▼
Request claim
        │
        ▼
Finalize claim
        │
        ▼
Withdraw if needed
~~~

---

# 4. Payroll Template Flow

A payroll template is the reusable payroll setup created by an employer.

It is the planning layer before an actual payroll run exists.

## Template data

A payroll template can include:

- chain
- token address
- employer address
- title
- description
- schedule type
- schedule start time
- recurrence configuration
- employee list
- employee wallet addresses
- salary allocation data
- status
- next run timestamp

## Why templates matter

Employers should not rebuild payroll from scratch every time.

Templates allow the backend to support:

- one-time payroll
- recurring payroll
- scheduled payroll runs
- repeat payroll structures
- employee allocation reuse
- future payroll automation

## Flow

~~~text
Employer creates template
        │
        ▼
Backend validates template payload
        │
        ▼
Backend stores payroll template
        │
        ▼
Backend stores employee allocation rows
        │
        ▼
Template remains draft or becomes active
~~~

## Template lifecycle

| Status | Meaning |
|---|---|
| Draft | Template exists but is not active |
| Active | Template can generate payroll runs |
| Paused | Template is temporarily stopped |
| Completed | Template is no longer generating runs |

## Template activation

Before a template can generate a payroll run, it must be activated.

~~~text
Template created
        │
        ▼
Employer activates template
        │
        ▼
Backend marks template active
        │
        ▼
Scheduler/manual action can create a run
~~~

---

# 5. Payroll Run Creation Flow

A payroll run is one executable payroll cycle created from a template.

If a template is the plan, a payroll run is the actual payroll instance.

## Run data

A payroll run can track:

- template
- chain
- token address
- employer address
- run time
- claim deadline
- employee count
- required total amount
- on-chain payroll ID
- status
- create transaction hash
- upload transaction hash
- finalize transaction hash
- fund transaction hash
- activation transaction hash
- last error

## Flow

~~~text
Active template
        │
        ▼
Manual create-next-run or scheduler tick
        │
        ▼
Backend creates PayrollRun
        │
        ▼
Backend copies employee allocations into run allocations
        │
        ▼
Run waits for encrypted salary payloads
~~~

## Why this matters

The backend needs a separate run record because each payroll cycle may have different:

- deadlines
- transaction hashes
- claim state
- activation state
- employee claim progress
- withdrawal progress
- errors

A recurring payroll template can generate many payroll runs over time.

---

# 6. Encrypted Allocation Flow

Encrypted allocations connect employee salary data to a payroll run.

In Zalary, salary values should not be uploaded as public plaintext contract data.

The client/API consumer prepares CoFHE-compatible encrypted salary inputs. The backend stores those encrypted payload references and coordinates upload to PayrollVault.

## Flow

~~~text
Payroll run created
        │
        ▼
Client prepares encrypted salary inputs
        │
        ▼
Backend receives encrypted allocation payloads
        │
        ▼
Backend attaches ciphertexts to employee run allocations
        │
        ▼
Backend checks for missing ciphertexts
        │
        ▼
Run becomes ready for allocation upload
~~~

## Important checks

Before upload, the backend should verify:

- every employee has a wallet address
- every employee has an encrypted amount payload
- the run exists
- the run is in the correct state
- the allocation list matches the run
- duplicate or missing employee allocation states are avoided

## Why this matters

Payroll allocation upload should not begin if even one employee is missing encrypted salary data.

A partial encrypted allocation upload could create a broken payroll run.

---

# 7. Create Payroll On-Chain Flow

After the backend has a run, it creates a matching payroll on PayrollVault.

This bridges backend state to on-chain state.

## Flow

~~~text
PayrollRun exists in backend
        │
        ▼
Backend sends createPayroll request
        │
        ▼
Viem worker broadcasts PayrollVault.createPayroll
        │
        ▼
Contract returns transaction hash
        │
        ▼
Backend stores create tx hash
        │
        ▼
Backend waits for receipt/finality
        │
        ▼
Backend stores on-chain payroll ID
        │
        ▼
Run status becomes created
~~~

## What must be tracked

The backend should track:

- transaction hash
- on-chain payroll ID
- transaction status
- finality status
- error/revert reason if available
- backend run status

## Why this matters

The backend run and the on-chain payroll must be linked.

Without that link, later actions like allocation upload, funding, activation, and claims cannot be reliably coordinated.

---

# 8. Upload Allocations Flow

Once the payroll exists on-chain and encrypted salary inputs are ready, the backend coordinates allocation upload.

## Flow

~~~text
Run status: created
        │
        ▼
Encrypted employee allocations ready
        │
        ▼
Backend sends uploadAllocations request
        │
        ▼
Viem worker broadcasts PayrollVault.uploadAllocations
        │
        ▼
Backend stores upload tx hash
        │
        ▼
Backend waits for receipt/finality
        │
        ▼
Run allocations marked uploaded
        │
        ▼
Run status becomes alloc_uploaded
~~~

## Why this matters

This is the point where confidential salary allocation data moves into the contract flow.

The backend must ensure upload happens safely and idempotently.

## Idempotency

Allocation upload should be protected against duplicate submission.

A real payroll backend must avoid:

- uploading the same allocation batch twice
- double-counting employees
- losing transaction status after page refresh
- marking upload complete before transaction finality

---

# 9. Finalize Allocations Flow

Allocation upload and allocation finalization are separate.

Finalization confirms that the payroll allocation set is complete and ready for funding.

## Flow

~~~text
Run status: alloc_uploaded
        │
        ▼
Backend sends finalizeAllocations request
        │
        ▼
Viem worker broadcasts PayrollVault.finalizeAllocations
        │
        ▼
Backend stores finalize tx hash
        │
        ▼
Backend waits for receipt/finality
        │
        ▼
Run status becomes alloc_finalized
~~~

## Why this matters

Payroll should not be funded or activated while allocation data is incomplete.

Finalization gives the backend a clean state boundary:

~~~text
Before finalization:
  allocations can still be incomplete

After finalization:
  payroll is ready for funding
~~~

---

# 10. Funding Flow

Funding moves confidential payroll value into the payroll escrow path.

The employer funds payroll using a CoFHE-compatible encrypted amount.

## Flow

~~~text
Run status: alloc_finalized
        │
        ▼
Client/API consumer prepares encrypted funding input
        │
        ▼
Backend sends fundPayroll request
        │
        ▼
Viem worker broadcasts PayrollVault.fundPayroll
        │
        ▼
Backend stores fund tx hash
        │
        ▼
Backend waits for receipt/finality
        │
        ▼
Run status becomes funded
~~~

## What the backend tracks

- encrypted funding payload reference
- funding transaction hash
- transaction status
- run status
- last error if funding fails

## Why this matters

Funding is one of the most sensitive steps.

The backend must not assume that a transaction hash means the payroll is ready. It needs receipt/finality tracking and lifecycle state updates.

---

# 11. Activation Flow

Activation makes payroll claimable.

In the confidential payroll protocol, funding success is represented through a private/fhe-aware proof path.

The backend coordinates the handle/proof flow required to activate payroll.

## Flow

~~~text
Run status: funded
        │
        ▼
Backend reads fundedOnce handle
        │
        ▼
Client/API consumer performs proof/decrypt-for-tx flow
        │
        ▼
Backend receives funded plaintext + signature payload
        │
        ▼
Backend sends activatePayroll request
        │
        ▼
Viem worker broadcasts PayrollVault.activatePayroll
        │
        ▼
Backend stores activation tx hash
        │
        ▼
Backend waits for receipt/finality
        │
        ▼
Run status becomes active
~~~

## Why this matters

Activation is the boundary between employer setup and employee access.

Before activation:

~~~text
Payroll exists, but employees should not claim.
~~~

After activation:

~~~text
Employees can discover and claim salary.
~~~

---

# 12. Employee Claim Discovery Flow

Once payroll is active, employees need to discover claimable payroll.

The backend exposes claimable payroll based on employee wallet address.

## Flow

~~~text
Employee connects wallet
        │
        ▼
Client requests claimables for employee address
        │
        ▼
Backend searches active runs and employee allocations
        │
        ▼
Backend returns claimable payroll records
~~~

## Claimable logic can consider

- employee wallet address
- active payroll runs
- allocation exists
- claim deadline
- claim status
- already claimed state
- pending claim state
- cancellation/retry state

## Why this matters

Employees should not have to know payroll IDs manually.

A real payroll product should show:

~~~text
You have salary available to claim
~~~

instead of forcing the employee to interact directly with a contract.

---

# 13. Claim Request Flow

Claim request starts the employee claim process.

## Flow

~~~text
Employee chooses claimable payroll
        │
        ▼
Client sends claim request
        │
        ▼
Backend creates/updates ClaimRecord
        │
        ▼
Backend sends requestClaim to worker
        │
        ▼
Viem worker broadcasts PayrollVault.requestClaim
        │
        ▼
Backend stores request tx hash
        │
        ▼
Backend tracks pending claim state
~~~

## Claim record tracks

- employee address
- payroll run
- request transaction hash
- pending request ID
- pending handles
- claim status
- last error

## Why this matters

Claims can involve pending state.

The backend must remember that a claim is in progress even if the user refreshes the page or leaves the app.

---

# 14. Claim Sync Flow

The backend needs to sync the pending claim state after request.

## Flow

~~~text
Claim request submitted
        │
        ▼
Backend reads pending claim state
        │
        ▼
Backend stores handles/request IDs
        │
        ▼
Client can continue finalization flow
~~~

## Why this matters

A claim is not always a single-step action.

There may be a request phase, proof/decrypt phase, and finalization/cancellation phase.

The backend makes the process resumable.

---

# 15. Claim Finalization Flow

Finalization completes a successful claim.

## Flow

~~~text
Pending claim exists
        │
        ▼
Client/API consumer prepares proof-backed result
        │
        ▼
Backend receives finalization payload
        │
        ▼
Backend sends finalizeClaim to worker
        │
        ▼
Viem worker broadcasts PayrollVault.finalizeClaim
        │
        ▼
Backend stores finalize tx hash
        │
        ▼
Backend marks claim completed after receipt/finality
~~~

## Why this matters

The backend must distinguish:

- claim requested
- claim pending
- claim finalized
- claim cancelled
- claim failed
- claim retryable

This is important for employee experience and payroll correctness.

---

# 16. Claim Cancellation / Retry Flow

Some claim attempts may fail or need cancellation.

The backend supports the concept of cancellation/retry state.

## Flow

~~~text
Pending claim exists
        │
        ▼
Claim cannot finalize or user chooses retry path
        │
        ▼
Backend sends cancel claim request
        │
        ▼
Worker broadcasts cancelPendingClaim
        │
        ▼
Backend clears pending state
        │
        ▼
Employee can retry claim
~~~

## Why this matters

In confidential systems, operations can fail without exposing sensitive information.

A robust payroll backend must support retry paths so employees are not stuck.

---

# 17. Withdrawal Request Flow

After salary is claimed, the employee may want to withdraw confidential balance to public USDC.

SwapRouter handles withdrawal.

## Flow

~~~text
Employee has confidential balance
        │
        ▼
Employee requests withdrawal
        │
        ▼
Backend creates SwapRouterWithdraw record
        │
        ▼
Backend sends requestWithdraw to worker
        │
        ▼
Viem worker broadcasts SwapRouter.requestWithdraw
        │
        ▼
Backend stores request tx hash
        │
        ▼
Backend tracks pending withdrawal state
~~~

## Withdrawal record tracks

- user address
- withdrawal key
- request transaction hash
- pending amount handle
- pending ok handle
- pending request ID
- status
- last error

## Why this matters

Withdrawal is also a multi-step confidential flow.

The backend must track the pending withdrawal state until finalization.

---

# 18. Withdrawal Sync Flow

The backend syncs pending withdrawal data after request.

## Flow

~~~text
Withdrawal request submitted
        │
        ▼
Backend reads pending withdrawal state
        │
        ▼
Backend stores pending handles/request ID
        │
        ▼
Client/API consumer can continue finalization
~~~

## Why this matters

Without sync, the frontend/client would have to reconstruct state manually.

The backend makes withdrawal resumable.

---

# 19. Withdrawal Finalization Flow

Finalization completes a withdrawal.

## Flow

~~~text
Pending withdrawal exists
        │
        ▼
Client/API consumer prepares proof-backed result
        │
        ▼
Backend receives finalization payload
        │
        ▼
Backend sends finalizeWithdraw to worker
        │
        ▼
Viem worker broadcasts SwapRouter.finalizeWithdraw
        │
        ▼
Backend stores finalize tx hash
        │
        ▼
Backend marks withdrawal completed after receipt/finality
~~~

## Why this matters

This completes the salary lifecycle:

~~~text
Employer funds confidential payroll
        │
        ▼
Employee claims salary privately
        │
        ▼
Employee withdraws when needed
~~~

---

# 20. Transaction Tracking Flow

Every contract write creates asynchronous state.

The backend needs transaction tracking so payroll state remains reliable after refreshes, delays, failed transactions, or background processing.

## Transaction statuses

The backend can track states such as:

| Status | Meaning |
|---|---|
| Created | Transaction intent exists |
| Submitted | Transaction hash received |
| Pending | Waiting for mining/finality |
| Confirmed | Transaction mined |
| Finalized | Required confirmations reached |
| Failed | Transaction failed |
| Reverted | Contract reverted |
| Replaced | Transaction replaced/dropped |

## Flow

~~~text
Backend action begins
        │
        ▼
Transaction intent recorded
        │
        ▼
Worker broadcasts transaction
        │
        ▼
Transaction hash stored
        │
        ▼
Background sync polls receipt
        │
        ▼
Status updated
        │
        ▼
Related payroll/claim/withdraw status updated
~~~

## Why this matters

Payroll cannot depend on temporary UI state.

The backend must know the truth of every payroll action.

---

# 21. Celery / Redis Background Flow

Some payroll tasks should happen in the background.

## Background tasks

The backend is structured for:

- scheduler tick
- payroll run generation
- deadline reminders
- pending claim reminders
- transaction sync
- background state updates

## Scheduler tick flow

~~~text
Celery beat triggers scheduler_tick
        │
        ▼
Backend finds active templates due for a run
        │
        ▼
Backend creates payroll runs
        │
        ▼
Backend advances next_run_at
~~~

## Reminder flow

~~~text
Celery beat triggers reminder task
        │
        ▼
Backend finds relevant payroll/claim records
        │
        ▼
Backend sends reminder notification
        │
        ▼
Backend records reminder timestamp
~~~

## Transaction sync flow

~~~text
Celery worker checks pending transactions
        │
        ▼
Backend polls receipt/finality
        │
        ▼
Backend updates transaction state
        │
        ▼
Backend updates run/claim/withdraw lifecycle state
~~~

## Why this matters

Payroll workflows do not always happen in one request.

A real backend needs background workers to keep the system moving.

---

# 22. Error Handling Flow

Payroll actions can fail.

The backend needs to capture errors clearly and keep records recoverable.

## Possible errors

- invalid wallet address
- missing ciphertext
- duplicate allocation
- worker unavailable
- RPC timeout
- transaction reverted
- transaction dropped
- insufficient gas
- insufficient balance
- failed proof
- claim already pending
- withdrawal already pending
- expired claim deadline

## Error handling pattern

~~~text
Action begins
        │
        ▼
Backend validates input
        │
        ▼
Backend records attempted action
        │
        ▼
Worker/contract call attempted
        │
        ▼
If failure:
    store last_error
    keep object recoverable
    expose safe error to client
~~~

## Why this matters

Payroll is high trust.

If something fails, the employer or employee needs to know what happened and what can be retried.

---

# 23. State Machine Summary

## Payroll run states

A payroll run can move through states similar to:

~~~text
draft / scheduled
        │
        ▼
created
        │
        ▼
alloc_uploaded
        │
        ▼
alloc_finalized
        │
        ▼
funded
        │
        ▼
active
        │
        ▼
closed
~~~

## Claim states

A claim can move through states similar to:

~~~text
available
        │
        ▼
requested
        │
        ▼
pending
        │
        ├──► finalized
        │
        └──► cancelled / retryable
~~~

## Withdrawal states

A withdrawal can move through states similar to:

~~~text
created
        │
        ▼
requested
        │
        ▼
pending
        │
        ├──► finalized
        │
        └──► cancelled / failed
~~~

## Transaction states

A transaction can move through states similar to:

~~~text
created
        │
        ▼
submitted
        │
        ▼
pending
        │
        ▼
confirmed
        │
        ▼
finalized
~~~

Failure paths:

~~~text
submitted
        │
        ├──► failed
        ├──► reverted
        └──► replaced
~~~

---

# 24. End-to-End Flow Summary

The complete backend-supported payroll flow is:

~~~text
Employer onboarding
        │
        ▼
Payroll template creation
        │
        ▼
Template activation
        │
        ▼
Payroll run creation
        │
        ▼
Encrypted salary preparation
        │
        ▼
Ciphertext storage
        │
        ▼
On-chain payroll creation
        │
        ▼
Encrypted allocation upload
        │
        ▼
Allocation finalization
        │
        ▼
Encrypted payroll funding
        │
        ▼
fundedOnce proof path
        │
        ▼
Payroll activation
        │
        ▼
Employee claim discovery
        │
        ▼
Claim request
        │
        ▼
Claim sync
        │
        ▼
Claim finalization or retry
        │
        ▼
Withdrawal request
        │
        ▼
Withdrawal sync
        │
        ▼
Withdrawal finalization
~~~

---

# 25. What This Proves for Wave 3

Wave 3 proves that Zalary is no longer only a contract protocol.

It now has the backend design needed to coordinate:

- employer setup
- employee setup
- payroll templates
- payroll schedules
- payroll runs
- encrypted allocation movement
- contract transaction execution
- transaction state tracking
- claim lifecycle
- withdrawal lifecycle
- background jobs

This is the infrastructure layer required for a real confidential payroll product.

Wave 2 proved the protocol.

Wave 3 proves the backend flow that drives the protocol.

---

# 26. Why This Matters

Confidential payroll cannot be solved by contracts alone.

A real payroll product needs:

- private salary logic
- reliable scheduling
- resumable claims
- recoverable withdrawals
- background workers
- transaction tracking
- user onboarding
- stateful payroll records

The backend flow is what connects those requirements into one system.

That is why Wave 3 matters.