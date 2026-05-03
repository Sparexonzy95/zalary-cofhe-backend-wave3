# Setup

This document explains the local setup for the Zalary Wave 3 backend public submission.

← Back to README

---

## Setup Overview

The backend is structured around:

- Python
- Django
- Django REST Framework
- Celery
- Redis
- Node.js
- viem worker
- Base Sepolia RPC
- CoFHE-compatible encrypted input flow

This public repository is prepared for review and technical evaluation.

Runtime secrets, private keys, local database files, local CoFHE key material, and production credentials are excluded.

---

## Requirements

Install the following:

| Tool | Purpose |
|---|---|
| Python 3.11+ | Backend runtime |
| pip | Python dependency installation |
| virtualenv / venv | Local Python environment |
| Redis | Celery broker/result backend |
| Node.js | viem worker and CoFHE helper runtime |
| npm | Worker dependency installation |
| Git | Source control |

---

## 1. Clone Repository

```bash
git clone <repo-url>
cd zalary-cofhe-backend-public
```

---

## 2. Create Environment File

Copy the example environment file:

```bash
cp .env.example .env
```

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Then update `.env` with local values.

Important:

```text
Never commit .env
```

---

## 3. Environment Variables

The backend expects variables similar to:

```env
DJANGO_SECRET_KEY=replace-with-secure-secret
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost

DB_ENGINE=
DB_NAME=zalary
DB_USER=zalary
DB_PASSWORD=
DB_HOST=localhost
DB_PORT=5432
SQLITE_PATH=db.sqlite3

REDIS_URL=redis://127.0.0.1:6379/0
CELERY_BROKER_URL=redis://127.0.0.1:6379/0
CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/0

API_KEY=dev-key
FRONTEND_BASE_URL=http://localhost:5173

BASE_SEPOLIA_CHAIN_ID=84532
BASE_SEPOLIA_RPC_URL=https://sepolia.base.org

USDC_ADDRESS=
CONFIDENTIALTOKEN_ADDRESS=
PAYROLLVAULT_ADDRESS=
SWAPROUTER_ADDRESS=

CONFIRMATIONS_REQUIRED=3
FINALITY_RECHECK_DEPTH=200
REPLACEMENT_SCAN_BLOCKS=200

VIEM_WORKER_URL=http://127.0.0.1:8787
VIEM_WORKER_TIMEOUT_SECONDS=45

DEFAULT_FROM_EMAIL=noreply@zalary.app
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=
EMAIL_PORT=587
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_TIMEOUT=20

ONBOARDING_TOKEN_MAX_AGE_SECONDS=604800
ONBOARDING_NONCE_TTL_SECONDS=600
ONBOARDING_EMAIL_CODE_TTL_SECONDS=900

TIME_ZONE=Africa/Lagos
LOG_LEVEL=INFO
```

---

## 4. Create Python Virtual Environment

```bash
python -m venv .venv
```

Activate it.

Windows PowerShell:

```powershell
.venv\Scripts\activate
```

macOS/Linux:

```bash
source .venv/bin/activate
```

---

## 5. Install Python Dependencies

```bash
pip install -r Requirements.txt
```

---

## 6. Run Database Migrations

```bash
python manage.py migrate
```

---

## 7. Start Django API

```bash
python manage.py runserver
```

Default local API:

```text
http://127.0.0.1:8000/api/v1
```

---

## 8. Start Redis

Celery requires Redis.

If Redis is installed locally:

```bash
redis-server
```

On Windows, use Redis through WSL, Docker, or another supported local setup.

Example Docker command:

```bash
docker run --name zalary-redis -p 6379:6379 redis:7
```

---

## 9. Start Celery Worker

In a separate terminal:

```bash
celery -A config worker -l info
```

---

## 10. Start Celery Beat

In another terminal:

```bash
celery -A config beat -l info
```

Celery beat is used for scheduled/background flows such as:

- scheduler tick
- payroll run generation
- reminders
- transaction sync

---

## 11. Install Worker Dependencies

From the repository root:

```bash
cd workers/viem
npm install
```

---

## 12. Start Viem Worker

From `workers/viem`:

```bash
npm run dev
```

Expected worker URL:

```text
http://127.0.0.1:8787
```

Health check:

```text
GET http://127.0.0.1:8787/health
```

---

## 13. Seed Chain Configuration

If the backend includes a chain seed command, run the relevant management command.

Example:

```bash
python manage.py seed_chain
```

The chain record should include:

- Base Sepolia chain ID
- RPC URL
- USDC address
- ConfidentialToken address
- PayrollVault address
- SwapRouter address
- confirmation settings

---

## 14. API Key Header

Backend API calls may require:

```http
X-API-Key: <API_KEY>
Content-Type: application/json
```

Example:

```http
X-API-Key: dev-key
Content-Type: application/json
```

---

## 15. Basic API Check

Check that Django is running:

```bash
curl http://127.0.0.1:8000/api/v1/templates/
```

With API key:

```bash
curl -H "X-API-Key: dev-key" http://127.0.0.1:8000/api/v1/templates/
```

---

## 16. Worker Health Check

```bash
curl http://127.0.0.1:8787/health
```

Expected response:

```json
{
  "ok": true
}
```

---

## 17. Local Development Flow

Recommended local terminal setup:

| Terminal | Command |
|---|---|
| 1 | `python manage.py runserver` |
| 2 | `redis-server` or Docker Redis |
| 3 | `celery -A config worker -l info` |
| 4 | `celery -A config beat -l info` |
| 5 | `cd workers/viem && npm run dev` |

---

## 18. Expected Payroll Flow

After setup, the backend is designed to support:

```text
POST /templates/
  → POST /templates/{id}/activate/
  → POST /templates/{id}/create_next_run/
  → POST /runs/{id}/set_ciphertexts/
  → GET /runs/{id}/missing_ciphertexts/
  → POST /runs/{id}/create_payroll/
  → POST /runs/{id}/upload_allocations/
  → POST /runs/{id}/finalize_allocations/
  → POST /runs/{id}/fund_payroll/
  → GET /runs/{id}/funded_once_handle/
  → POST /runs/{id}/activate_payroll/
```

---

## 19. Testing Notes

The Wave 3 backend integration test validates the employer-side confidential payroll flow.

See:

```text
docs/TESTS.md
```

The test covers:

- service readiness
- viem worker health
- real CoFHE encrypted salary input
- template creation
- run creation
- ciphertext storage
- createPayroll
- uploadAllocations
- finalizeAllocations
- fundPayroll
- fundedOnce proof
- activatePayroll

---

## 20. Security Reminder

Before pushing to GitHub, confirm that private files are not present:

```powershell
Get-ChildItem -Recurse -Force | Where-Object {
    $_.FullName -match "\.env$|cofhesdk-keys|\.cofhe-home|\.cofhesdk|db\.sqlite3|node_modules|\.venv|celerybeat-schedule|__pycache__"
} | Select-Object FullName
```

Expected output:

```text
No output
```

If the command returns anything sensitive, remove it before committing.

---

## 21. Files That Should Not Be Public

Do not commit:

- `.env`
- `db.sqlite3`
- `.cofhe-home/`
- `.cofhesdk/`
- `cofhesdk-keys.json`
- wallet private keys
- SMTP passwords
- production database URLs
- private RPC URLs
- `node_modules/`
- `.venv/`
- Celery schedule files
- local logs

---

## 22. Setup Outcome

After setup, the local system should have:

- Django API running
- Redis running
- Celery worker running
- Celery beat running
- viem worker running
- environment variables configured
- chain configuration seeded
- backend ready to coordinate payroll flows

This is the local foundation for testing the Wave 3 backend integration flow.