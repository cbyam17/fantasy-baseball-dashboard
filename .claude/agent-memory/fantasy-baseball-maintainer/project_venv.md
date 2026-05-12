---
name: project-venv
description: Python environment setup for the project; the README-described streamlit-env doesn't exist
metadata:
  type: project
---

## Python environment — key facts

The README says to create `streamlit-env` in the project root, but that venv does not exist.
The only venv present is `projections/.venv` (Python 3.14), which has `pandas`, `requests`,
`beautifulsoup4`, and `playwright` (v1.59.0) but NOT `python-dotenv` or `mysql-connector-python`.

The intended environment (from README + CLAUDE.md) is:
```
python3 -m venv streamlit-env
source streamlit-env/bin/activate
pip install python-dotenv mysql-connector-python pandas streamlit
```

`python-dotenv` is not installed system-wide or in the projections venv.
Scripts that use `from dotenv import load_dotenv` must be run inside a venv that has it installed.

**Playwright note:** The projections venv has playwright installed but its *bundled browsers* are NOT
installed (playwright install was not run). However, system Chrome at `/usr/bin/google-chrome` works
as a substitute by passing `executable_path='/usr/bin/google-chrome'` to `playwright.chromium.launch()`.

**Why:** Encountered when verifying sync_rosters.py dependencies and building fetch_projections.py.
**How to apply:** When a user says a script fails on import, first ask if they're in the right venv.
For Playwright specifically, always pass the system Chrome executable_path.
