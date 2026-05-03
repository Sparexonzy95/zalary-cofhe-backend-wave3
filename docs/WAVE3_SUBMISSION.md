# Wave 3 Submission

Zalary CoFHE Backend — Fhenix Buildathon Wave 3

← Back to README

---

## Submission Summary

Zalary is a confidential payroll system built for teams that want on-chain salary settlement without exposing compensation publicly.

Wave 2 proved the confidential payroll smart contract protocol.

Wave 3 adds the backend integration layer that coordinates the full payroll lifecycle around that protocol.

This submission focuses on the backend system that makes confidential payroll usable beyond direct contract calls.

---

## One-Line Summary

Zalary Wave 3 delivers the backend orchestration layer for confidential payroll on Fhenix CoFHE.

---

## What Was Built

Wave 3 introduces the backend foundation for:

- employer onboarding
- employee onboarding
- payroll templates
- payroll runs
- encrypted salary allocation handling
- PayrollVault transaction coordination
- funding and activation state
- claim discovery
- claim request/finalization
- SwapRouter withdrawal flow
- background scheduling
- transaction tracking
- viem worker integration
- real confidential-input backend testing

---

## Why Wave 3 Matters

Wave 2 proved that confidential payroll can exist at the contract level.

But payroll is not just a contract problem.

A real payroll product needs:

- templates
- schedules
- employee records
- salary allocation state
- claim state
- withdrawal state
- transaction status
- reminders
- onboarding
- error handling
- retry paths

Wave 3 adds this backend orchestration layer.

---

## Wave 2 to Wave 3 Progress

| Area | Wave 2 | Wave 3 |
|---|---|---|
| Main focus | Confidential payroll contracts | Backend integration flow |
| Core system | Smart contracts | Django/DRF backend |
| User structure | Contract actors | Employer/employee onboarding |
| Payroll setup | Contract calls | Payroll templates and runs |
| Salary allocation | Encrypted contract inputs | Backend-tracked encrypted allocation flow |
| Execution | Direct contract interaction | API → worker → contract |
| Scheduling | Future roadmap | Backend scheduler structure |
| Claims | Contract-level claim flow | Backend claim discovery and state |
| Withdrawals | SwapRouter contract flow | Backend withdrawal lifecycle |
| Transaction state | Chain-level | Backend + chain tracking |
| Testing | Contract tests | Real confidential-input backend integration test |

---

## Backend Architecture Delivered

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

## Repository Contents

| Area | Location |
|---|---|
| Django project config | `config/` |
| Chain configuration | `apps/chains/` |
| CoFHE payroll backend app | `apps/cofhe/` |
| Onboarding module | `apps/onboarding/` |
| Viem worker interface | `workers/viem/` |
| API documentation | `docs/API_OVERVIEW.md` |
| Backend flow documentation | `docs/BACKEND_FLOW.md` |
| Test documentation | `docs/TESTS.md` |
| Security documentation | `docs/SECURITY_NOTES.md` |
| Architecture documentation | `docs/ARCHITECTURE.md` |
| Data model documentation | `docs/DATA_MODEL.md` |
| Integration flow documentation | `docs/INTEGRATION_FLOW.md` |
| Setup documentation | `docs/SETUP.md` |

---

## Backend Flow Delivered

### Employer Flow

```text
Employer onboarding
  → payroll template creation
  → template activation
  → payroll run creation
  → encrypted salary setup
  → createPayroll
  → uploadAllocations
  → finalizeAllocations
  → fundPayroll
  → fundedOnce proof
  → activatePayroll
```

### Employee Flow

```text
Employee onboarding
  → claimable payroll discovery
  → claim request
  → claim sync
  → claim finalization
  → withdrawal request
  → withdrawal sync
  → withdrawal finalization
```

### Transaction Flow

```text
API request
  → backend validation
  → worker call
  → contract transaction
  → tx hash stored
  → receipt/finality sync
  → backend lifecycle update
```

---

## API Surface Delivered

The backend API surface includes:

- templates
- payroll runs
- encrypted ciphertext setup
- funding quote/context
- payroll creation
- allocation upload
- allocation finalization
- payroll funding
- fundedOnce handle retrieval
- payroll activation
- employee claimables
- claims
- withdrawals

Full API documentation:

```text
docs/API_OVERVIEW.md
```

---

## Test Proof

Wave 3 includes confidential-input backend integration testing.

The test validates:

- Django API readiness
- viem worker readiness
- real CoFHE salary encryption
- backend ciphertext storage
- on-chain payroll creation
- encrypted allocation upload
- allocation finalization
- encrypted payroll funding
- fundedOnce handle read
- real `decryptForTx` proof
- payroll activation
- backend state progression

Full test documentation:

```text
docs/TESTS.md
```

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

## Security Posture

The public repository excludes:

- `.env`
- local databases
- private keys
- local CoFHE key material
- SMTP credentials
- production deployment credentials
- virtual environments
- `node_modules`
- local Celery schedule files

Full security notes:

```text
docs/SECURITY_NOTES.md
```

---

## Product-Market Fit

Zalary targets teams that want stablecoin payroll without public salary exposure.

The strongest early users are:

- crypto-native companies
- DAOs
- Web3 startups
- contributor networks
- grant programs
- remote teams paying in stablecoins

The core market pain is simple:

> Teams want the speed of stablecoin payroll, but cannot expose salaries publicly.

Zalary’s confidential payroll architecture solves that.

---

## Competitive Position

| Category | Limitation | Zalary Advantage |
|---|---|---|
| Traditional payroll | Slow and centralized | Faster on-chain settlement direction |
| Public crypto payments | Salary data is public | FHE-encrypted salary logic |
| DAO payout tools | Contributor comp is visible | Private contributor payroll |
| Manual stablecoin payouts | Operationally messy | Template/run/claim workflow |
| Contract-only systems | No product workflow | Backend orchestration layer |

---

## Why This Submission Is Strong

This Wave 3 submission is strong because it shows movement from protocol to product infrastructure.

Zalary now has:

- a backend architecture
- a data model
- an API surface
- onboarding structure
- worker integration
- payroll lifecycle design
- claim lifecycle design
- withdrawal lifecycle design
- background job direction
- transaction state tracking
- real confidential-input test coverage

This is the infrastructure required to make confidential payroll usable.

---

## Why This Wins

Zalary is not just another payment tool.

It addresses a real payroll problem:

> Public blockchains expose salaries. Payroll needs confidentiality.

Wave 2 proved that the protocol can enforce confidential payroll logic.

Wave 3 proves that a backend can coordinate the product workflow around it.

That is the difference between a smart contract demo and a payroll system.

---

## Final Statement

Zalary is building confidential payroll infrastructure for on-chain organizations.

Wave 1 proved the idea.

Wave 2 proved the protocol.

Wave 3 proves the backend integration flow.

The next step is production-grade UX, and mainnet readiness.