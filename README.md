# Nucleus Playwright automation

Python Playwright automation for the Nucleus DEV application.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
cp .env.example .env
```

Set `NUCLEUS_TEST_PHONE` and `NUCLEUS_TEST_OTP` in `.env` or the process environment. Do not commit `.env` or `auth/.auth.json`.

## Run

```bash
pytest -m smoke
pytest
```

The framework saves authenticated storage state under `auth/.auth.json` only when authentication is needed. Reports are written to `reports/`.

See [docs/application-map.md](docs/application-map.md), [docs/test-strategy.md](docs/test-strategy.md), and [docs/automation-status.md](docs/automation-status.md).
See [docs/business-workflows.md](docs/business-workflows.md) for Phase 2 workflow coverage and safe limitations.
