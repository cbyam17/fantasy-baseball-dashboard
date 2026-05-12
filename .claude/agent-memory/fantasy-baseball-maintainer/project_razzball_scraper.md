---
name: project-razzball-scraper
description: Razzball.com projection scraper — URL structure, Cloudflare bypass, table behavior, column mapping
metadata:
  type: project
---

## Razzball.com projection scraper — key facts

### URLs
- Hitters: `https://razzball.com/restofseason-hitterprojections/`
- Pitchers: `https://razzball.com/restofseason-pitcherprojections/`
- Table ID: `neorazzstatstable` on both pages

### JavaScript rendering required
The `<table id="neorazzstatstable">` element is present in the raw HTML response but has **zero rows** —
data is loaded via DataTables/JavaScript. A headless browser (Playwright) is required.

### Cloudflare bypass
Plain headless Chromium is blocked by Cloudflare. Must use:
- `--disable-blink-features=AutomationControlled` Chrome flag
- A realistic User-Agent header (Chrome 131 on Linux)
- `add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")`
- System Chrome binary at `/usr/bin/google-chrome` (Playwright bundled browsers not installed; see [[project-venv]])
- Realistic Accept / Accept-Language / Accept-Encoding headers in browser context

### Table behavior (as of 2026-05-11)
- All rows are rendered at once — no DataTables pagination, no "Show N entries" select control
- Hitters: 909 rows, 28 columns — matches `HITTER_COLS` exactly
- Pitchers: 829 rows, 30 columns — matches `PITCHER_COLS` exactly
- `wait_until='domcontentloaded'` is sufficient; no need to wait for `networkidle`
- After navigation, `wait_for_selector('#neorazzstatstable', timeout=30_000)` reliably confirms the table loaded

### Column mapping
Razzball column headers match the existing CSV format **exactly** — no translation needed:
- Hitter headers: `['#', 'Name', 'Team', 'ESPN', 'Y!', '$', 'G', 'PA', 'AB', 'R', 'HR', 'RBI', 'SB', 'CS', 'H', '1B', '2B', '3B', 'TB', 'SO', 'BB', 'HBP', 'AVG', 'OBP', 'SLG', 'OPS', 'Own%', 'RazzID']`
- Pitcher headers: `['#', 'Name', 'Team', 'ESPN', 'Y!', '$', 'G', 'GS', 'QS', 'TBF', 'IP', 'W', 'L', 'SV', 'HLD', 'H', 'ER', 'K', 'BB', 'HBP', 'HR', 'ERA', 'SIERA', 'WHIP', 'GB%', 'LD%', 'FB%', 'BABIP', 'Own%', 'RazzID']`

### Script location
`projections/fetch_projections.py` — run from project root with:
```
projections/.venv/bin/python3 projections/fetch_projections.py
```
Supports `--dry-run`, `--hitters-only`, `--pitchers-only`.

### Output files
Written with `utf-8-sig` encoding (UTF-8 BOM) to match original manually-exported CSV format.
Pandas reads them correctly via default `pd.read_csv()` (strips BOM automatically).

### Scheduling (daily at 6 AM)
```
0 6 * * * cd /path/to/fantasy-baseball-dashboard && projections/.venv/bin/python3 projections/fetch_projections.py >> projections/fetch.log 2>&1
```

**Why:** Built to replace manual CSV downloads from Razzball.com (Feature 1 of automation initiative).
**How to apply:** If the scraper breaks (Cloudflare block, table structure change, row count drop), check:
1. Is the table ID still `neorazzstatstable`?
2. Does the Cloudflare bypass still work (try the stealth context settings)?
3. Did row counts drop below MIN_HITTER_ROWS=200 / MIN_PITCHER_ROWS=100?
