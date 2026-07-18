# User Payout Management System 

A Low-Level Design implementation of an affiliate payout system, built as
an SDE Intern assignment. Handles advance payouts, reconciliation,
withdrawal cooldowns, and failed-payout recovery using an append-only
ledger for auditable balance tracking.

## Tech Stack

- Python 3.12 
- FASTAPI (API Layer)
- SQLAlchemy (ORM)
- SQLite (storage as it requires no setup and is swappable to Postgres via one env var)
- Pytest (testing)

## Setup 

```bash
git clone
cd payout-system

python -m venv venv
venv\Scripts\Activate

pip install -r requirements.txt
```

## Running the API 

```bash
uvicorn app.main:app --reload
```

The API will be live at `http://127.0.0.1.8000`.
Interactive API docs (Swagger UI) is available at `http://127.0.0.1.8000/docs` (every endpoint can be tested directly from here)

The database schema is self intializing `payout_system.db` (SQLite) it is automatically created on first run without separate migration step

## Running Tests

```bash
pytest tests/ -v
```

19 tests covering all the rules, idempotency guarantees and edge cases.

## API Reference 

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/sales` | Create a new (pending) sale |
| `GET` | `/sales/{sale_id}` | Fetch a sale |
| `POST` | `/admin/advance-payout/run` | Run the advance payout batch job (idempotent) |
| `POST` | `/admin/sales/{sale_id}/reconcile` | Reconcile a sale to `approved`/`rejected` |
| `POST` | `/admin/payouts/{payout_id}/status` | Mark a payout `cancelled`/`rejected`/`failed`, triggering balance reversal |
| `GET` | `/users/{user_id}/balance` | Get a user's current withdrawable balance |
| `GET` | `/users/{user_id}/ledger` | Full audit trail of a user's ledger entries |
| `POST` | `/withdrawals` | Request a withdrawal (enforces balance check + 24h cooldown) |

## Example 

```bash
# 1. Create a sale (needs an existing user_id and brand_id)
POST /sales
{ "user_id": "...", "brand_id": "...", "earning": 40 }

# 2. Run the advance payout job -> pays 10% (Rs.4) on all eligible pending sales
POST /admin/advance-payout/run

# 3. Check balance -> 4.00
GET /users/{user_id}/balance

# 4. Reconcile the sale as approved -> releases remaining Rs.36
POST /admin/sales/{sale_id}/reconcile
{ "status": "approved" }

# 5. Check balance -> 40.00
GET /users/{user_id}/balance

# 6. Withdraw
POST /withdrawals
{ "user_id": "...", "amount": 20 }

# 7. A second withdrawal within 24h correctly returns 429 Too Many Requests
```
