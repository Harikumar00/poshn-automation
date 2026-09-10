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

## MongoDB validation discovery

MongoDB checks are isolated under the `mongo` marker and use only metadata
operations (`ping`, `list_collection_names`, and collection `options()`).
Configure a dedicated read-only account locally in `.env`:

```bash
MONGODB_URI=<READ_ONLY_MONGODB_URI>
MONGODB_DATABASE=<DATABASE_NAME>
```

Run the first-phase discovery with:

```bash
pytest -m mongo tests/mongo -q
```

The sanitized reports are written to `reports/mongodb_validation_discovery.md`
and `reports/mongodb_validation_discovery.json`. No documents are queried or
modified, and `.env` is ignored by Git.

The framework saves authenticated storage state under `auth/.auth.json` only when authentication is needed. Reports are written to `reports/`.

## GitHub Actions

The CI workflow is defined in `.github/workflows/ci.yml`. It always runs Python
quality checks and runs the Playwright/MongoDB tests when the corresponding
GitHub Actions secrets are configured:

- `NUCLEUS_BASE_URL`
- `NUCLEUS_TEST_PHONE`
- `NUCLEUS_TEST_OTP`
- `MONGODB_URI`
- `MONGODB_DATABASE`

The MongoDB job uses the read-only account and performs metadata/structure
inspection only. No deployment job is included because this repository does
not define a service deployment target.

The `cd` job builds the test-runner [Dockerfile](../Dockerfile) and publishes
versioned and `latest` images to GitHub Container Registry after the `main`
branch tests pass. MongoDB and application credentials are supplied only when
the image is run; they are never included in the image.

See [docs/application-map.md](docs/application-map.md), [docs/test-strategy.md](docs/test-strategy.md), and [docs/automation-status.md](docs/automation-status.md).
See [docs/business-workflows.md](docs/business-workflows.md) for Phase 2 workflow coverage and safe limitations.
