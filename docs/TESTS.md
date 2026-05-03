# Backend Test Suite

Real confidential-input backend integration test for Wave 3.

← Back to README

---

## Test Status

The Wave 3 backend was tested with a real confidential-input integration flow.

This test replaces fake encrypted payroll payloads with real CoFHE SDK-generated encrypted inputs and validates the employer-side payroll lifecycle through the existing Django API, viem worker, and deployed CoFHE contracts.

The test confirms that the backend can coordinate:

- USDC → cUSDC deposit through SwapRouter
- payroll template creation
- payroll run creation
- real salary encryption with CoFHE SDK
- encrypted salary storage through `set_ciphertexts`
- `createPayroll`
- `uploadAllocations`
- `finalizeAllocations`
- `fundPayroll`
- fundedOnce handle retrieval
- real `decryptForTx` proof generation
- `activatePayroll`
- backend run state progression
- transaction receipt polling

---

## Test Execution Context

The integration test was executed locally against the backend, viem worker, CoFHE helper, and Base Sepolia RPC.

This public document records the test coverage, expected results, and what each test proves.

---

## Required Services

The test requires:

~~~text
Django API running
Viem worker running
Celery worker running
Node.js installed
CoFHE helper installed
Base Sepolia RPC available
Employer wallet funded with ETH for gas
Employer wallet funded with USDC for deposit
~~~

Required backend components:

~~~text
Django REST API
apps/cofhe endpoints
apps/cofhe payroll run state model
viem worker
CoFHE SDK helper
SwapRouter contract
ConfidentialToken contract
PayrollVault contract
Base Sepolia RPC
~~~

Required environment values:

~~~text
BASE_URL
VIEM_URL
API_KEY
CHAIN_ID
RPC_URL
BACKEND_PRIVATE_KEY
EMPLOYER_ADDRESS
CONFIDENTIALTOKEN
PAYROLLVAULT
SWAPROUTER
USDC
ALICE_ADDRESS
BOB_ADDRESS
ALICE_SALARY
BOB_SALARY
FUND_AMOUNT
DEPOSIT_AMOUNT
~~~

---

# Real Confidential Input Test

## Summary

~~~text
Zalary CoFHE — Real Confidential Input Test
~~~

This is the main Wave 3 backend integration test.

It validates that the backend can move from payroll setup to payroll activation using real encrypted CoFHE inputs instead of placeholder data.

The test covers the employer-side flow:

~~~text
USDC deposit
  → template creation
  → run creation
  → real encrypted salaries
  → ciphertext storage
  → createPayroll
  → uploadAllocations
  → finalizeAllocations
  → encrypted funding
  → fundPayroll
  → fundedOnce proof
  → activatePayroll
~~~

---

# Test Sections

## 0. Pre-flight Checks

These tests validate that the local integration environment is ready before the payroll flow begins.

### ✅ Private key configured

Verifies that the backend private key exists and is formatted correctly.

What it checks:

~~~text
BACKEND_PRIVATE_KEY is set
BACKEND_PRIVATE_KEY starts with 0x
BACKEND_PRIVATE_KEY is 66 characters including 0x
~~~

Why it matters:

The viem worker needs a valid signer to broadcast contract transactions.

---

### ✅ Django and viem worker are up

Verifies that both backend services are running.

What it checks:

~~~text
GET /templates/
GET /health on viem worker
~~~

Expected result:

~~~text
Django returns 200
Viem worker returns ok=true
~~~

Why it matters:

The test requires both the Django API and worker execution layer.

---

### ✅ Node helper installed and derivation matches employer

Verifies that the CoFHE helper is available and that the configured private key derives the expected employer address.

What it checks:

~~~text
Node.js is available
CoFHE helper file exists
package.json exists
node_modules exists
derived account == EMPLOYER_ADDRESS
~~~

Why it matters:

The same signer used for encryption/proofs must match the employer identity expected by the backend and contracts.

---

### ✅ ETH balance sufficient for gas

Checks that the employer wallet has enough ETH on Base Sepolia to pay gas.

Expected condition:

~~~text
ETH balance >= 0.01 ETH
~~~

Why it matters:

Contract transactions such as `approve`, `deposit`, `createPayroll`, `uploadAllocations`, `fundPayroll`, and `activatePayroll` require gas.

---

### ✅ USDC balance sufficient for deposit

Checks that the employer wallet has enough USDC to deposit into SwapRouter.

Expected condition:

~~~text
USDC balance >= DEPOSIT_AMOUNT
~~~

Why it matters:

The employer needs USDC to mint confidential cUSDC before funding payroll.

---

## 1. SwapRouter — Deposit USDC to cUSDC

This section validates the public-to-confidential token entry point.

### ✅ Approve USDC for SwapRouter

Checks the current USDC allowance and submits `approve` if needed.

What it tests:

~~~text
ERC20.allowance(employer, SwapRouter)
ERC20.approve(SwapRouter, amount)
transaction receipt polling
~~~

Expected result:

~~~text
Approval is skipped if allowance is enough
Approval tx is submitted and mined if allowance is not enough
~~~

Why it matters:

SwapRouter needs USDC allowance before it can deposit USDC and mint cUSDC.

---

### ✅ Deposit USDC into SwapRouter when needed

Checks whether the employer already has a confidential cUSDC handle. If not, it deposits USDC through SwapRouter.

What it tests:

~~~text
ConfidentialToken.balanceOf(employer)
SwapRouter.deposit(amount)
transaction receipt polling
~~~

Expected result:

~~~text
Deposit is skipped if cUSDC handle already exists
Deposit tx is submitted and mined if needed
~~~

Why it matters:

Payroll funding happens using confidential token balances, so the employer must have cUSDC available.

---

### ✅ Verify employer cUSDC handle is non-zero

Reads the employer’s confidential token balance handle after deposit.

What it tests:

~~~text
ConfidentialToken.balanceOf(employer)
non-zero encrypted balance handle
~~~

Expected result:

~~~text
cUSDC handle is non-zero
~~~

Why it matters:

The system does not reveal the balance amount publicly, but it must confirm that the encrypted balance handle exists.

---

## 2. Backend Setup — Template and Run

This section validates that the backend can create the payroll objects needed before touching PayrollVault.

### ✅ Create payroll template

Creates a payroll template through the Django API.

Endpoint tested:

~~~text
POST /templates/
~~~

Payload includes:

~~~text
chain
token_address
employer_address
title
schedule
employees
employee wallet addresses
salary amounts
~~~

Expected result:

~~~text
HTTP 201
template_id returned
~~~

Why it matters:

The backend must store employer payroll configuration before creating an on-chain payroll.

---

### ✅ Activate template

Activates the newly created payroll template.

Endpoint tested:

~~~text
POST /templates/{template_id}/activate/
~~~

Expected result:

~~~text
HTTP 200
template becomes active
~~~

Why it matters:

Only active templates should be eligible to generate payroll runs.

---

### ✅ Create payroll run

Creates a payroll run from the activated template.

Endpoint tested:

~~~text
POST /templates/{template_id}/create_next_run/
~~~

Expected result:

~~~text
HTTP 200
run_id returned
initial run status returned
~~~

Why it matters:

A run represents the actual payroll cycle that will be mapped to PayrollVault.

---

## 3. Real CoFHE Inputs — Encrypt Salaries and Store Them

This is one of the most important Wave 3 test sections.

It proves that the backend flow can use real encrypted salary inputs, not fake payloads.

### ✅ Generate real CoFHE encrypted salaries

Uses the CoFHE helper to encrypt employee salary amounts.

What it tests:

~~~text
encrypt-u64(ALICE_SALARY)
encrypt-u64(BOB_SALARY)
real CoFHE SDK-generated encrypted inputs
~~~

Expected result:

~~~text
encrypted salary payload for Alice
encrypted salary payload for Bob
~~~

Why it matters:

Wave 3 must prove that payroll allocation upload can work with real confidential inputs.

---

### ✅ Store real encrypted salaries via set_ciphertexts

Stores the encrypted salary payloads on the backend allocation rows.

Endpoint tested:

~~~text
POST /runs/{run_id}/set_ciphertexts/
~~~

Payload includes:

~~~text
employee_address
encrypted_amount
~~~

Expected result:

~~~text
HTTP 200
updated = 2
~~~

Why it matters:

The backend must connect each employee allocation to its encrypted salary payload before uploading to PayrollVault.

---

### ✅ Verify run has no missing ciphertexts

Checks that all employees in the run have encrypted salary payloads attached.

Endpoint tested:

~~~text
GET /runs/{run_id}/missing_ciphertexts/
~~~

Expected result:

~~~text
No missing ciphertexts
~~~

Why it matters:

Payroll allocation upload should not proceed if any employee salary ciphertext is missing.

---

## 4. PayrollVault — createPayroll()

This section validates that the backend can create the on-chain payroll record through the worker.

### ✅ Broadcast and confirm createPayroll()

Reads `nextPayrollId`, submits the backend create payroll action, waits for the transaction, and confirms backend state.

Endpoint tested:

~~~text
POST /runs/{run_id}/create_payroll/
~~~

Contract read:

~~~text
PayrollVault.nextPayrollId()
~~~

Expected result:

~~~text
tx_hash returned
createPayroll transaction mined
run status becomes created
onchain_payroll_id is stored
~~~

Why it matters:

This proves the backend can bridge from a database payroll run to an on-chain PayrollVault payroll.

---

### ✅ Verify nextPayrollId incremented on-chain

Reads `nextPayrollId` again and verifies it increased by one.

Contract read:

~~~text
PayrollVault.nextPayrollId()
~~~

Expected result:

~~~text
nextPayrollId after = nextPayrollId before + 1
~~~

Why it matters:

This confirms that the contract state changed, not just the backend state.

---

## 5. PayrollVault — uploadAllocations() with Real Confidential Inputs

This section validates that encrypted employee salary allocations can move from backend state to PayrollVault.

### ✅ Broadcast uploadAllocations() with real encrypted salaries

Uploads Alice and Bob’s real encrypted salary payloads through the backend.

Endpoint tested:

~~~text
POST /runs/{run_id}/upload_allocations/
~~~

Payload includes:

~~~text
employee_addresses
encrypted_amounts
idempotency_key
private_key runtime signer input
~~~

Expected result:

~~~text
tx_hash returned
uploadAllocations transaction mined
run status becomes alloc_uploaded
~~~

Why it matters:

This is the core proof that the Wave 3 backend can coordinate encrypted salary allocation upload.

---

## 6. PayrollVault — finalizeAllocations()

This section validates that the backend can finalize uploaded allocations.

### ✅ Broadcast finalizeAllocations()

Finalizes allocation upload for the payroll run.

Endpoint tested:

~~~text
POST /runs/{run_id}/finalize_allocations/
~~~

Expected result:

~~~text
tx_hash returned
finalizeAllocations transaction mined
run status becomes alloc_finalized
~~~

Why it matters:

Payroll should not be funded or activated until allocation upload is finalized.

---

## 7. PayrollVault — fundPayroll() with Real Confidential Input

This section validates that payroll funding can use a real encrypted funding amount.

### ✅ Generate real encrypted funding input

Encrypts the payroll funding amount using the CoFHE SDK helper.

What it tests:

~~~text
encrypt-u64(FUND_AMOUNT)
~~~

Expected result:

~~~text
real encrypted funding payload
~~~

Why it matters:

Funding should use a confidential input, not a fake value.

---

### ✅ Broadcast fundPayroll() with real encrypted amount

Submits the encrypted funding payload through the backend.

Endpoint tested:

~~~text
POST /runs/{run_id}/fund_payroll/
~~~

Expected result:

~~~text
tx_hash returned
fundPayroll transaction mined
run status becomes funded
~~~

Why it matters:

This proves the backend can coordinate confidential payroll funding.

---

## 8. Activation Proof — fundedOnce Handle and activatePayroll()

This section validates the proof-backed activation path.

### ✅ Read fundedOnce handle from backend

Gets the encrypted fundedOnce handle needed for activation.

Endpoint tested:

~~~text
GET /runs/{run_id}/funded_once_handle/
~~~

Expected result:

~~~text
funded_once_handle returned
~~~

Why it matters:

Activation depends on proving that funding succeeded without exposing private balance logic.

---

### ✅ Decrypt fundedOnce handle using real CoFHE SDK

Uses CoFHE `decryptForTx` flow to decrypt the fundedOnce handle for transaction verification.

What it tests:

~~~text
decrypt-tx(funded_once_handle)
~~~

Expected result:

~~~text
decryptedValue returned
signature returned
funded_plaintext parsed as boolean
~~~

Why it matters:

The activation path depends on a real proof-backed result, not a mocked boolean.

---

### ✅ Broadcast activatePayroll() with real Threshold proof

Submits the funded proof to activate payroll.

Endpoint tested:

~~~text
POST /runs/{run_id}/activate_payroll/
~~~

Payload includes:

~~~text
funded_plaintext
funded_sig
~~~

Expected result:

~~~text
tx_hash returned
activatePayroll transaction mined
run status becomes active
~~~

Why it matters:

This completes the employer-side payroll lifecycle from template setup to active payroll.

---

## 9. Final State Summary

The test prints a final summary containing:

~~~text
Template ID
Run ID
On-chain payroll ID
Create tx
Upload tx
Finalize tx
Fund tx
Activate tx
~~~

It also summarizes the covered flow:

~~~text
real SDK encryption for salaries
real uploadAllocations transaction
real fundPayroll transaction
real fundedOnce decrypt proof
real activatePayroll transaction
~~~

---

# Backend API Endpoints Tested

| Area | Endpoint | Purpose |
|---|---|---|
| Templates | `GET /templates/` | Django readiness check |
| Templates | `POST /templates/` | Create payroll template |
| Templates | `POST /templates/{id}/activate/` | Activate template |
| Templates | `POST /templates/{id}/create_next_run/` | Create payroll run |
| Runs | `POST /runs/{id}/set_ciphertexts/` | Store encrypted salaries |
| Runs | `GET /runs/{id}/missing_ciphertexts/` | Confirm no missing encrypted salaries |
| Runs | `POST /runs/{id}/create_payroll/` | Broadcast createPayroll |
| Runs | `POST /runs/{id}/upload_allocations/` | Upload encrypted salary allocations |
| Runs | `POST /runs/{id}/finalize_allocations/` | Finalize allocation upload |
| Runs | `POST /runs/{id}/fund_payroll/` | Fund payroll with encrypted amount |
| Runs | `GET /runs/{id}/funded_once_handle/` | Read fundedOnce handle |
| Runs | `POST /runs/{id}/activate_payroll/` | Activate payroll with proof |
| Runs | `GET /runs/{id}/` | Poll backend run state |

---

# Worker and Contract Operations Tested

| Layer | Operation | Purpose |
|---|---|---|
| Viem worker | `GET /health` | Confirms worker is running |
| ERC20 | `allowance` | Checks USDC approval |
| ERC20 | `approve` | Approves SwapRouter |
| SwapRouter | `deposit` | Converts USDC to cUSDC |
| ConfidentialToken | `balanceOf` | Reads encrypted cUSDC handle |
| PayrollVault | `nextPayrollId` | Confirms payroll creation state |
| PayrollVault | `createPayroll` | Creates payroll on-chain |
| PayrollVault | `uploadAllocations` | Uploads encrypted salaries |
| PayrollVault | `finalizeAllocations` | Finalizes uploaded allocations |
| PayrollVault | `fundPayroll` | Funds payroll with encrypted amount |
| PayrollVault | `activatePayroll` | Activates payroll with funded proof |

---

# What This Test Proves

This test proves that Wave 3 is not just a backend folder structure.

It validates a real backend-to-chain confidential payroll path:

~~~text
Django API
  → viem worker
  → CoFHE SDK encrypted salary inputs
  → PayrollVault transactions
  → transaction receipt polling
  → backend run state updates
  → fundedOnce proof
  → payroll activation
~~~

The test proves the backend can coordinate:

| Capability | Proven |
|---|---|
| API readiness | ✅ |
| Worker readiness | ✅ |
| Real CoFHE salary encryption | ✅ |
| Backend ciphertext storage | ✅ |
| On-chain payroll creation | ✅ |
| Encrypted allocation upload | ✅ |
| Allocation finalization | ✅ |
| Encrypted payroll funding | ✅ |
| Transaction receipt polling | ✅ |
| fundedOnce handle read | ✅ |
| Real `decryptForTx` proof | ✅ |
| Payroll activation | ✅ |
| Backend state progression | ✅ |

---

# Current Coverage

## Covered in the Wave 3 Real Confidential Input Test

| Flow | Status |
|---|---|
| Employer environment pre-flight | ✅ Covered |
| USDC approval | ✅ Covered |
| USDC → cUSDC deposit | ✅ Covered |
| Template creation | ✅ Covered |
| Template activation | ✅ Covered |
| Payroll run creation | ✅ Covered |
| Real salary encryption | ✅ Covered |
| Ciphertext storage | ✅ Covered |
| Missing ciphertext check | ✅ Covered |
| createPayroll | ✅ Covered |
| nextPayrollId verification | ✅ Covered |
| uploadAllocations | ✅ Covered |
| finalizeAllocations | ✅ Covered |
| Encrypted funding input | ✅ Covered |
| fundPayroll | ✅ Covered |
| fundedOnce handle read | ✅ Covered |
| decryptForTx proof | ✅ Covered |
| activatePayroll | ✅ Covered |

---

## Completed Additional Backend Test Coverage

| Flow | Status |
|---|---|
| Employee private-key claim test | ✅ Completed |
| Employee claim finalization test | ✅ Completed |
| Claim cancellation/retry test | ✅ Completed |
| SwapRouter private withdrawal finalization test | ✅ Completed |
| Multi-run recurring payroll scheduler test | ✅ Completed |
| Transaction replacement/reorg handling test | ✅ Completed |
| Email reminder delivery test | ✅ Completed |
| Large employee batch upload test | ✅ Completed |

---

# Why This Matters

A confidential payroll protocol is only useful if the backend can coordinate the full lifecycle around it.

This test confirms that the backend can:

1. create payroll state,
2. accept real encrypted salary inputs,
3. move those inputs into the contract flow,
4. fund the payroll confidentially,
5. read the activation handle,
6. generate a real transaction proof,
7. activate the payroll,
8. and track backend state along the way.

That is the core of Wave 3.

Wave 2 proved the protocol.

Wave 3 proves that the backend can drive the protocol.