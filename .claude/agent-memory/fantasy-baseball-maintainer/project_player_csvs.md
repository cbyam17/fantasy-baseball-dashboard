---
name: project-player-csvs
description: Format and filenames of players/ CSVs that app.py reads; how sync_rosters.py writes them
metadata:
  type: project
---

## Player CSV files — key facts

**Actual filenames** (what app.py reads — do not rename):
- `players/hitters_wmm.csv`
- `players/hitters_lfl.csv`
- `players/pitchers_wmm.csv`
- `players/pitchers_lfl.csv`

Note: the task spec in one place says `wmm_hitters.csv` style, but the actual files
and app.py both use `hitters_wmm.csv` style. Always match the actual files.

**Format:** Single column `NAME`, no index, UTF-8 plain text.
Example:
```
NAME
Ronald Acuna Jr.
CJ Abrams
Mookie Betts
```

**app.py consumption:** `pd.read_csv("players/hitters_wmm.csv")["NAME"].dropna().tolist()`
Used as `WHERE NAME IN (...)` filter in SQL queries. Name must match the DB value exactly.

**sync_rosters.py:** Writes these four files from Yahoo API `name.full` field.
Position split: `position_type == "B"` → hitters, `position_type == "P"` → pitchers.

**Why:** These CSVs are the sole roster-filtering mechanism for both leagues in the dashboard.
**How to apply:** Any script writing these files must use exactly this column name, no index,
and UTF-8. Do not add extra columns.
