# Security Notes

This document explains how the public Wave 3 backend repository is prepared for buildathon review without exposing runtime secrets, private key material, local databases, or production infrastructure details.

← Back to README

---

## Security Principle

The core source-control rule for Zalary is simple:

> Runtime secrets and private key material must never be committed.

The backend is designed to coordinate confidential payroll workflows, but the repository must not contain anything that can compromise wallets, deployments, private infrastructure, or local development keys.

---

## What Is Safe to Commit

The public repository may include:

| File / Folder | Why It Is Safe |
|---|---|
| `README.md` | Public project explanation and Wave 3 submission overview |
| `docs/` | Architecture, API, test, and security documentation |
| `.env.example` | Example environment variable names without real values |
| `.gitignore` | Prevents accidental commit of secrets and local files |
| `LICENSE` | Public source-availability/legal notice |
| `manage.py` | Standard Django project entrypoint |
| `config/` | Public Django project configuration structure |
| `apps/chains/` | Chain configuration model/structure |
| `apps/onboarding/` | Public onboarding module structure |
| `apps/cofhe/models.py` | Data model structure for payroll, claims, withdrawals, transactions |
| `apps/cofhe/serializers.py` | Serializer structure |
| `apps/cofhe/urls.py` | Public API route structure |
| `workers/viem/` | Public worker interface structure |

---

## What Must Never Be Committed

The following files and materials must stay out of the public repository:

| Item | Risk |
|---|---|
| `.env` | May contain API keys, private keys, RPC secrets, SMTP passwords, database URLs |
| `.env.local` | Local runtime secrets |
| `.env.production` | Production credentials and infrastructure secrets |
| `db.sqlite3` | Local database state, test records, addresses, run data |
| `*.sqlite3` | Any local database file |
| `.cofhe-home/` | Local CoFHE SDK key/cache material |
| `.cofhesdk/` | CoFHE SDK local storage |
| `cofhesdk-keys.json` | CoFHE key material |
| wallet private keys | Can compromise funds and contract execution authority |
| RPC provider secret URLs | Can expose paid/private RPC credentials |
| SMTP passwords | Can compromise email delivery accounts |
| production deployment configs | Can reveal server access/deployment structure |
| `node_modules/` | Large dependency folder, unnecessary in source control |
| `.venv/`, `venv/`, `env/` | Local Python virtual environments |
| `celerybeat-schedule*` | Local Celery scheduler state |
| `__pycache__/` | Generated Python cache files |
| generated local logs | May expose runtime errors, addresses, credentials, or environment paths |
| combined source dumps | May accidentally include private files or sensitive implementation details |

---

## Public Environment File

The repository includes:

```text
.env.example