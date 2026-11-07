# smartcare
SmartCare healthcare appointment scheduling system — COMP 425

## How to run the tests

From the repository root, use Python 3.12:

```sh
cd backend
python3 -m venv .venv-qa
source .venv-qa/bin/activate
python -m pip install -r requirements-qa.txt
python -m pytest -q
```

The API tests use a temporary in-memory SQLite database. The appointment tests
cover booking, cancellation and reopening a slot, rejecting a repeat booking,
and rejecting a slot whose start time has already passed.

Run `python -m ruff check .` and `python -m mypy` from `backend` for the
configured checks. Ruff covers the validation module and tests, and mypy covers
the validation module.
