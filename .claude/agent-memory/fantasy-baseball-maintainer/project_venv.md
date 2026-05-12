---
name: project-venv
description: Python environment setup — projections/.venv is fully built with all deps including Playwright Chromium binaries
metadata:
  type: project
---

## Python environment — current state (as of 2026-05-12)

`projections/.venv` is the sole venv for automation scripts. It was created fresh on 2026-05-12
on the Ubuntu homelab server at `/srv/docker-data/python/app`.

**What's installed in projections/.venv (Python 3.12.3):**
- python-dotenv
- mysql-connector-python
- pandas
- requests
- beautifulsoup4
- playwright (v1.59.0) — with Playwright-managed Chromium binaries downloaded via `playwright install chromium`
- yahoo-oauth
- yfinance

**Playwright Chromium binaries** are installed at `/home/cbyam/.cache/ms-playwright/chromium-1217`
(Chrome for Testing 147.0.7727.15). The scripts use Playwright's own bundled Chromium, not system Chrome.
System Chrome is NOT installed on this server.

**streamlit-env** does not exist; the Streamlit dashboard venv has not been created on this server.
The README describes how to create it if needed.

**.env file** is present at `/srv/docker-data/python/app/.env` with all 9 required keys:
DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD, YAHOO_CLIENT_ID, YAHOO_CLIENT_SECRET,
YAHOO_WMM_LEAGUE_NAME, YAHOO_LFL_LEAGUE_NAME. Properly gitignored.

**load_projections.py** has been verified to run end-to-end: reads both CSVs and loads to MySQL.

**Why:** Full environment setup was done on 2026-05-12 following README step 3 exactly.
**How to apply:** All three automation scripts should be invoked with
`/srv/docker-data/python/app/projections/.venv/bin/python3`. For cron, use that full path.
