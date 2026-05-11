# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A Streamlit fantasy baseball dashboard backed by a MySQL database. It displays z-score rankings for two fantasy leagues — **WMM (Walter Matthau Memorial)** and **LFL (Lion's Field Legends)** — for both hitters and pitchers, plus a player comparison tool with a custom composite score builder.

## Setup

```bash
python3 -m venv streamlit-env
source streamlit-env/bin/activate
pip install python-dotenv mysql-connector-python pandas streamlit
```

Create a `.env` file with:
```
DB_HOST=...
DB_PORT=...
DB_NAME=fantasy_baseball_db
DB_USER=...
DB_PASSWORD=...
```

## Running the app

```bash
python3 -m streamlit run app.py
```

## Loading projections (seasonal task)

Place updated CSV files in `projections/` (named `hitter_projections.csv` and `pitcher_projections.csv`), then run:

```bash
python3 projections/load_hitter_projections.py
python3 projections/load_pitcher_projections.py
```

Each script truncates and reloads the corresponding MySQL table. The z-score views recompute automatically on the next query.

## Architecture

**Data flow:** CSV exports from a projections source → loader scripts → MySQL tables → MySQL views (z-score calculation) → Streamlit app queries views → displayed in browser.

**`app.py`** — the entire Streamlit app in one file. It:
1. Connects to MySQL and queries `hitter_zscore_view` and `pitcher_zscore_view`
2. Filters rosters by league (WMM/LFL) using name lists from `players/*.csv`
3. Renders four league-specific tables with position filters
4. Renders two player comparison sections with a custom composite z-score builder

**`db/`** — SQL DDL for the two projection tables and two z-score views. The views compute per-stat z-scores using window functions; `ZSCORE_K` for hitters and `ZSCORE_ERA`/`ZSCORE_WHIP`/`ZSCORE_L` for pitchers are **inverted** (lower raw value = higher z-score). Composite `ZSCORE_WMM` and `ZSCORE_LFL` differ by which stats each league counts.

**`players/`** — CSVs listing each league's roster by position (hitters/pitchers × WMM/LFL). Only a `NAME` column is used.

**`projections/`** — CSV source files and loader scripts. Column mapping in the loaders translates Yahoo! projection export headers to DB column names.

## League stat differences

| | WMM hitters | LFL hitters |
|---|---|---|
| Batting average | No | Yes |
| OPS | Yes | Yes |
| Hits | Yes | No |
| Strikeouts (inv.) | Yes | No |

| | WMM pitchers | LFL pitchers |
|---|---|---|
| Losses (inv.) | Yes | No |
| Saves | No | Yes |
| Saves+Holds | Yes | No |
