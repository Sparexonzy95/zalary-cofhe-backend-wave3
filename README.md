# Zalary, Confidential Payroll Backend

Payroll cannot move fully on-chain if salaries are exposed publicly.

Zalary fixes that with Fhenix CoFHE.

Wave 2 proved the confidential payroll protocol.  
Wave 3 adds the backend integration layer that coordinates payroll templates, encrypted allocations, claims, withdrawals, scheduling, and transaction state.

Submitted for **Fhenix Buildathon, Wave 3**.

---

## TL;DR

Zalary is confidential payroll infrastructure for teams that want stablecoin payroll without public salary exposure.

Employers can create payroll templates, generate payroll runs, coordinate encrypted salary allocations, fund payroll, activate payroll, and track backend/on-chain state.

Employees can discover claimable payroll, request salary claims, finalize claims, and withdraw through the SwapRouter flow.

Think **Stripe for payroll**, but salaries are never public.

---

## Wave 3 Deliverable

Wave 3 focuses on the backend integration flow.

This repository contains the public Wave 3 backend submission:

- Django / Django REST Framework backend structure
- chain configuration layer
- employer and employee onboarding module
- payroll template and payroll run model
- encrypted salary allocation flow
- claim and withdrawal lifecycle structure
- Celery/Redis background task interface
- viem worker interface
- API route surface
- real confidential-input backend test documentation
- security and setup documentation

Runtime secrets, local databases, private key material, local CoFHE key storage, deployment credentials, and private runtime modules are excluded from this public repository.

---

## Review in 3 Minutes

| What to Review | Where |
|---|---|
| Wave 3 submission summary | [`docs/WAVE3_SUBMISSION.md`](docs/WAVE3_SUBMISSION.md) |
| Backend architecture | [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) |
| Backend flow | [`docs/BACKEND_FLOW.md`](docs/BACKEND_FLOW.md) |
| API surface | [`docs/API_OVERVIEW.md`](docs/API_OVERVIEW.md) |
| Data model | [`docs/DATA_MODEL.md`](docs/DATA_MODEL.md) |
| Integration flow | [`docs/INTEGRATION_FLOW.md`](docs/INTEGRATION_FLOW.md) |
| Backend test summary | [`docs/TESTS.md`](docs/TESTS.md) |
| Setup instructions | [`docs/SETUP.md`](docs/SETUP.md) |
| Security notes | [`docs/SECURITY_NOTES.md`](docs/SECURITY_NOTES.md) |
| Django project configuration | [`config/`](config/) |
| Chain configuration layer | [`apps/chains/`](apps/chains/) |
| Payroll backend module | [`apps/cofhe/`](apps/cofhe/) |
| Onboarding module | [`apps/onboarding/`](apps/onboarding/) |
| Viem worker interface | [`workers/viem/`](workers/viem/) |
| Environment structure | [`.env.example`](.env.example) |

---

## The Problem

Payroll is one of the most sensitive financial workflows in the world.

Public blockchains are transparent by default. That makes them powerful for settlement, but dangerous for payroll.

If payroll runs directly on a public chain without confidentiality:

- employee salaries become visible
- company compensation structures leak
- DAO contributor payments become public
- payroll history can be tracked forever
- competitors can inspect treasury and workforce spending
- confidential compensation agreements become difficult to honor

Because of this, most crypto payroll still depends on off-chain systems, custodians, spreadsheets, banks, or centralized payroll platforms.

Zalary exists because payroll needs the speed and programmability of on-chain settlement without exposing salary data.

---

## What Wave 3 Proves

Wave 2 answered:

> Can confidential payroll work at the smart contract level?

Wave 3 answers:

> Can the protocol be coordinated by a backend that supports real employer and employee payroll workflows?

This submission proves the backend architecture for:

- employer onboarding
- employee onboarding
- payroll template creation
- payroll run generation
- encrypted salary allocation handling
- contract transaction coordination
- funding and activation state
- employee claim discovery
- claim request and finalization flow
- withdrawal lifecycle through SwapRouter
- background scheduling with Celery
- Redis-backed task coordination
- viem worker interface for contract execution
- backend transaction state tracking

Full backend flow:

[`docs/BACKEND_FLOW.md`](docs/BACKEND_FLOW.md)

---

## Why Backend Integration Matters

Smart contracts alone are not enough for payroll.

A real payroll product needs a backend that can coordinate:

- who the employer is
- who the employee is
- which payroll template is active
- when payroll should run
- which employees are included
- whether encrypted allocations were prepared
- whether payroll was funded
- whether payroll was activated
- whether an employee has a claimable salary
- whether a claim is pending or finalized
- whether a withdrawal was requested or completed
- whether a transaction finalized, failed, reverted, or needs retry

Wave 3 is about this orchestration layer.

The backend turns the confidential payroll contracts from Wave 2 into an application-ready payroll system.

---

## System Architecture

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

Detailed architecture:

[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)

---

## Wave 2 → Wave 3

| Wave | Focus | Output | Status |
|---|---|---|---|
| Wave 1 | Ideation and architecture | Product concept and confidential payroll direction | Completed |
| Wave 2 | Protocol layer | ConfidentialToken, PayrollVault, SwapRouter, tests, deployment | Completed |
| Wave 3 | Backend integration | Django/DRF backend, payroll state model, onboarding, worker interface, API surface, confidential-input testing | This submission |

Wave 2 proved that confidential payroll can work on-chain.

Wave 3 proves that the protocol can be coordinated by a backend that supports real payroll workflows.

---

## Backend Test Proof

Wave 3 includes confidential-input backend integration testing.

The test validates the employer-side payroll lifecycle using:

- Django REST API
- viem worker
- Base Sepolia RPC
- real CoFHE SDK-generated encrypted salary inputs
- PayrollVault contract flow
- SwapRouter deposit flow
- backend run state tracking
- transaction receipt polling
- fundedOnce proof flow
- payroll activation flow

The tested path:

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

Full test documentation:

[`docs/TESTS.md`](docs/TESTS.md)

---

## API Surface

The backend API is grouped around the payroll lifecycle:

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

[`docs/API_OVERVIEW.md`](docs/API_OVERVIEW.md)

---

## Data Model

The backend data model tracks the state needed to coordinate real payroll operations:

- chain configuration
- onboarding state
- payroll templates
- payroll runs
- employee run allocations
- claim records
- SwapRouter withdrawals
- transaction status

Full data model documentation:

[`docs/DATA_MODEL.md`](docs/DATA_MODEL.md)

---

## Why Zalary Wins

| Area | Traditional Payroll | Transparent On-chain Payroll | Zalary |
|---|---|---|---|
| Salary privacy | Private but centralized | Public forever | FHE-encrypted |
| Settlement speed | Slow banking rails | Fast | Fast |
| Custody | Platform/bank dependent | Non-custodial possible | Non-custodial design |
| Payroll scheduling | Yes | Usually manual | Backend scheduled |
| Employee claims | Platform controlled | Public | Confidential claim flow |
| Withdrawal flow | Bank/account based | Public transfer | SwapRouter flow |
| Transaction tracking | Internal ledger | Chain-only | Backend + chain status |
| Web3 readiness | Limited | Privacy problem | Built for confidential payroll |

Zalary combines the product expectations of payroll software with the settlement advantages of on-chain infrastructure.

---

## Who It Is For

Zalary is for teams that want to pay people on-chain without exposing compensation.

Primary users:

- crypto-native companies
- DAOs paying contributors
- Web3 startups paying contractors
- grant programs distributing contributor compensation
- on-chain organizations that need private stablecoin payroll
- future enterprises that want programmable payroll settlement

The first market is crypto-native teams because they already understand wallets, stablecoins, and on-chain settlement.

The long-term market is any organization that wants faster payroll infrastructure without salary exposure.

---

## Product-Market Fit

The product-market fit is clear:

> Teams already want to pay people in stablecoins, but they cannot expose compensation publicly.

Zalary fits where three needs overlap:

1. **Stablecoin payroll**  
   Teams want fast global settlement.

2. **Salary confidentiality**  
   Salary data must not be public.

3. **On-chain auditability**  
   Payroll should be programmable and verifiable without revealing amounts.

Without the backend, Zalary is a protocol.

With the backend, Zalary becomes payroll infrastructure.

---

## Repository Structure

```text
zalary-cofhe-backend-wave3/
├── apps/
│   ├── chains/
│   ├── cofhe/
│   └── onboarding/
├── config/
├── docs/
│   ├── API_OVERVIEW.md
│   ├── ARCHITECTURE.md
│   ├── BACKEND_FLOW.md
│   ├── DATA_MODEL.md
│   ├── INTEGRATION_FLOW.md
│   ├── SECURITY_NOTES.md
│   ├── SETUP.md
│   ├── TESTS.md
│   └── WAVE3_SUBMISSION.md
├── workers/
│   └── viem/
├── .env.example
├── .gitignore
├── LICENSE
├── manage.py
├── package.json
├── Requirements.txt
└── README.md
```

---

## Documentation

All technical depth lives in `/docs`.

| Document | What It Contains |
|---|---|
| [`docs/WAVE3_SUBMISSION.md`](docs/WAVE3_SUBMISSION.md) | Judge-facing Wave 3 summary |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Full backend architecture map and component responsibilities |
| [`docs/BACKEND_FLOW.md`](docs/BACKEND_FLOW.md) | Employer flow, employee flow, withdrawal flow, transaction flow |
| [`docs/API_OVERVIEW.md`](docs/API_OVERVIEW.md) | Public API route surface and endpoint responsibilities |
| [`docs/DATA_MODEL.md`](docs/DATA_MODEL.md) | Backend models and lifecycle states |
| [`docs/INTEGRATION_FLOW.md`](docs/INTEGRATION_FLOW.md) | Client → API → worker → contract coordination |
| [`docs/TESTS.md`](docs/TESTS.md) | Real confidential-input backend integration test summary |
| [`docs/SETUP.md`](docs/SETUP.md) | Local setup, Redis, Celery, worker instructions |
| [`docs/SECURITY_NOTES.md`](docs/SECURITY_NOTES.md) | Source control and runtime secret safety |

---

## Setup

Full setup guide:

[`docs/SETUP.md`](docs/SETUP.md)

Quick start:

```bash
cp .env.example .env
python -m venv .venv
.venv\Scripts\activate
pip install -r Requirements.txt
python manage.py migrate
python manage.py runserver
```

Start Celery:

```bash
celery -A config worker -l info
celery -A config beat -l info
```

Start viem worker:

```bash
cd workers/viem
npm install
npm run dev
```

---

## Security

The backend follows a clear source-control principle:

> Runtime secrets and private key material must never be committed.

Excluded from the public repository:

- `.env`
- local database files
- CoFHE local key material
- wallet/private keys
- SMTP credentials
- production deployment credentials
- local virtual environments
- `node_modules`
- local Celery schedule files

Full security notes:

[`docs/SECURITY_NOTES.md`](docs/SECURITY_NOTES.md)

---

## Roadmap

| Wave | Milestone | Status |
|---|---|---|
| Wave 1 | Ideation and architecture | Completed |
| Wave 2 | Confidential payroll protocol | Completed |
| Wave 3 | Backend integration flow | This submission |
| Wave 4 | Full client/backend production hardening | Planned |
| Wave 5 | Mainnet readiness and institutional onboarding | Planned |

---

## Why This Wins

Zalary has a clear wedge:

Payroll is a massive financial workflow, but it cannot safely move to public blockchains without confidentiality.

Wave 2 proved the confidential contract protocol.

Wave 3 proves the backend layer needed to coordinate real payroll operations.

This is not just a smart contract demo.

It is a confidential payroll system moving toward a complete product:

- private salary allocation
- employer payroll setup
- employee claim discovery
- confidential claim flow
- withdrawal flow
- backend scheduling
- worker-based contract execution
- transaction state tracking
- payroll lifecycle orchestration

Zalary is building the confidential payroll layer for on-chain organizations.

---

## License

All rights reserved. See [`LICENSE`](LICENSE).