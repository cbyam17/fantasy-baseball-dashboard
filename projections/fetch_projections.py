"""
fetch_projections.py — Scrape rest-of-season player projections from Razzball.com.

Fetches hitter and pitcher projection tables from:
  https://razzball.com/restofseason-hitterprojections/
  https://razzball.com/restofseason-pitcherprojections/

Each page renders its data via DataTables/JavaScript, so Playwright with a
system Chrome binary is used to execute the page JS before scraping.

Output files (written relative to the project root):
  projections/hitter_projections.csv
  projections/pitcher_projections.csv

Both files are written with a UTF-8 BOM (utf-8-sig encoding) to match the
format of the original manually-exported CSVs, which load_projections.py
already reads correctly via pandas' default BOM handling.

Usage:
    python3 projections/fetch_projections.py
    python3 projections/fetch_projections.py --dry-run   # print counts, skip writes
    python3 projections/fetch_projections.py --hitters-only
    python3 projections/fetch_projections.py --pitchers-only

Scheduling (daily at 6 AM):
    0 6 * * * cd /path/to/fantasy-baseball-dashboard && \
        projections/.venv/bin/python3 projections/fetch_projections.py >> projections/fetch.log 2>&1
"""

import argparse
import logging
import sys
import time
from io import StringIO
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Paths — script is in projections/, project root is one level up
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent

HITTER_OUT = PROJECT_ROOT / "projections" / "hitter_projections.csv"
PITCHER_OUT = PROJECT_ROOT / "projections" / "pitcher_projections.csv"

# ---------------------------------------------------------------------------
# Logging — match sync_rosters.py style
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Razzball source config
# ---------------------------------------------------------------------------

HITTER_URL = "https://razzball.com/restofseason-hitterprojections/"
PITCHER_URL = "https://razzball.com/restofseason-pitcherprojections/"
TABLE_ID = "neorazzstatstable"

# Minimum row counts; warn if fetch returns fewer
MIN_HITTER_ROWS = 200
MIN_PITCHER_ROWS = 100

# Expected columns — must match load_projections.py HITTER_MAPPING keys
HITTER_REQUIRED_COLS = {"#", "Name", "Team", "Y!", "R", "H", "HR", "RBI", "SB", "SO", "AVG", "OPS"}
PITCHER_REQUIRED_COLS = {"#", "Name", "Team", "Y!", "QS", "W", "L", "SV", "HLD", "ERA", "WHIP", "K"}

# Desired output column order — matches original CSV format
HITTER_COLS = ["#", "Name", "Team", "ESPN", "Y!", "$", "G", "PA", "AB",
               "R", "HR", "RBI", "SB", "CS", "H", "1B", "2B", "3B", "TB",
               "SO", "BB", "HBP", "AVG", "OBP", "SLG", "OPS", "Own%", "RazzID"]
PITCHER_COLS = ["#", "Name", "Team", "ESPN", "Y!", "$", "G", "GS", "QS",
                "TBF", "IP", "W", "L", "SV", "HLD", "H", "ER", "K", "BB",
                "HBP", "HR", "ERA", "SIERA", "WHIP", "GB%", "LD%", "FB%",
                "BABIP", "Own%", "RazzID"]

# ---------------------------------------------------------------------------
# Playwright browser helpers
# ---------------------------------------------------------------------------

# System Chrome binary — Playwright's bundled browsers require a separate
# `playwright install` step; using the system binary avoids that dependency.
CHROME_BINARY = "/usr/bin/google-chrome"

CHROME_ARGS = [
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-blink-features=AutomationControlled",
    "--window-size=1920,1080",
]

BROWSER_CONTEXT_KWARGS = dict(
    user_agent=(
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    ),
    viewport={"width": 1920, "height": 1080},
    locale="en-US",
    timezone_id="America/New_York",
    extra_http_headers={
        "Accept": (
            "text/html,application/xhtml+xml,application/xml;"
            "q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    },
)

# Injected before page JS runs — hides the webdriver flag that Cloudflare checks
STEALTH_SCRIPT = (
    "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
)


def _launch_browser(playwright):
    """Return a (browser, context) tuple ready for scraping."""
    browser = playwright.chromium.launch(
        headless=True,
        executable_path=CHROME_BINARY,
        args=CHROME_ARGS,
    )
    context = browser.new_context(**BROWSER_CONTEXT_KWARGS)
    context.add_init_script(STEALTH_SCRIPT)
    return browser, context


# ---------------------------------------------------------------------------
# Core scraping logic
# ---------------------------------------------------------------------------

def _scrape_table(page, url: str, label: str) -> pd.DataFrame:
    """
    Navigate to *url*, wait for the DataTables table to load, and return
    all rows as a DataFrame. Raises RuntimeError on failure.
    """
    log.info("Fetching %s projections from %s", label, url)
    try:
        page.goto(url, timeout=60_000, wait_until="domcontentloaded")
    except Exception as exc:
        raise RuntimeError(f"Navigation to {url} failed: {exc}") from exc

    # Wait for the table element to be present in the DOM
    try:
        page.wait_for_selector(f"#{TABLE_ID}", timeout=30_000)
    except Exception as exc:
        # Attempt to surface the page title for diagnosis
        try:
            title = page.title()
        except Exception:
            title = "<unknown>"
        raise RuntimeError(
            f"Table #{TABLE_ID} not found on {url} after 30s. "
            f"Page title: '{title}'. Possible Cloudflare block or URL change."
        ) from exc

    # Read headers from thead
    headers = page.eval_on_selector_all(
        f"#{TABLE_ID} thead th",
        "els => els.map(e => e.innerText.trim())",
    )
    if not headers:
        raise RuntimeError(f"No header columns found in #{TABLE_ID} at {url}")

    log.info("%s: found %d columns: %s", label, len(headers), headers)

    # Read all tbody rows as a 2D list of strings
    # DataTables renders all rows into the DOM on this site (no pagination)
    rows = page.eval_on_selector_all(
        f"#{TABLE_ID} tbody tr",
        "rows => rows.map(r => Array.from(r.querySelectorAll('td')).map(td => td.innerText.trim()))",
    )

    if not rows:
        raise RuntimeError(
            f"Table #{TABLE_ID} at {url} has no data rows. "
            "DataTables may not have finished rendering — try increasing wait time."
        )

    log.info("%s: scraped %d rows", label, len(rows))

    # Build DataFrame — skip rows whose column count doesn't match headers
    # (e.g. colspan rows used for DataTables grouping)
    clean_rows = [r for r in rows if len(r) == len(headers)]
    if len(clean_rows) < len(rows):
        log.warning(
            "%s: dropped %d malformed rows (expected %d cols each)",
            label, len(rows) - len(clean_rows), len(headers),
        )

    df = pd.DataFrame(clean_rows, columns=headers)
    return df


def _validate(df: pd.DataFrame, required_cols: set, min_rows: int, label: str) -> None:
    """Warn if required columns are missing or row count is suspiciously low."""
    missing = required_cols - set(df.columns)
    if missing:
        log.warning(
            "%s: missing expected columns: %s  "
            "(load_projections.py will fail if these are needed)",
            label, sorted(missing),
        )
    if len(df) < min_rows:
        log.warning(
            "%s: only %d rows scraped — expected at least %d. "
            "Check the Razzball URL and table structure.",
            label, len(df), min_rows,
        )


def _reorder_columns(df: pd.DataFrame, desired_cols: list, label: str) -> pd.DataFrame:
    """
    Return df with columns in *desired_cols* order. Columns present in
    desired_cols but absent from df are added as NaN. Extra columns not in
    desired_cols are dropped.
    """
    for col in desired_cols:
        if col not in df.columns:
            log.debug("%s: adding missing column '%s' as NaN", label, col)
            df[col] = float("nan")
    # Keep only the desired columns, in order
    return df[desired_cols]


def _write_csv(df: pd.DataFrame, path: Path, label: str, dry_run: bool) -> None:
    """Write *df* to *path* as a UTF-8 BOM CSV (matches original export format)."""
    if dry_run:
        log.info(
            "[DRY RUN] %s: would write %d rows × %d cols to %s",
            label, len(df), len(df.columns), path,
        )
        log.info("[DRY RUN] %s columns: %s", label, list(df.columns))
        return

    df.to_csv(path, index=False, encoding="utf-8-sig")
    log.info("%s: wrote %d rows to %s", label, len(df), path)


# ---------------------------------------------------------------------------
# Public fetch functions
# ---------------------------------------------------------------------------

def fetch_hitters(dry_run: bool = False) -> pd.DataFrame:
    """
    Scrape the Razzball hitter projection table and write
    projections/hitter_projections.csv. Returns the DataFrame.
    """
    from playwright.sync_api import sync_playwright  # local import — optional dep

    with sync_playwright() as pw:
        browser, context = _launch_browser(pw)
        try:
            page = context.new_page()
            df = _scrape_table(page, HITTER_URL, "hitters")
        finally:
            browser.close()

    _validate(df, HITTER_REQUIRED_COLS, MIN_HITTER_ROWS, "hitters")
    df = _reorder_columns(df, HITTER_COLS, "hitters")
    _write_csv(df, HITTER_OUT, "hitters", dry_run)
    return df


def fetch_pitchers(dry_run: bool = False) -> pd.DataFrame:
    """
    Scrape the Razzball pitcher projection table and write
    projections/pitcher_projections.csv. Returns the DataFrame.
    """
    from playwright.sync_api import sync_playwright  # local import — optional dep

    with sync_playwright() as pw:
        browser, context = _launch_browser(pw)
        try:
            page = context.new_page()
            df = _scrape_table(page, PITCHER_URL, "pitchers")
        finally:
            browser.close()

    _validate(df, PITCHER_REQUIRED_COLS, MIN_PITCHER_ROWS, "pitchers")
    df = _reorder_columns(df, PITCHER_COLS, "pitchers")
    _write_csv(df, PITCHER_OUT, "pitchers", dry_run)
    return df


def fetch_both(dry_run: bool = False) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Scrape both hitter and pitcher tables in a single browser session.
    More efficient than calling fetch_hitters() + fetch_pitchers() separately.
    Returns (hitters_df, pitchers_df).
    """
    from playwright.sync_api import sync_playwright  # local import — optional dep

    with sync_playwright() as pw:
        browser, context = _launch_browser(pw)
        try:
            page = context.new_page()

            hitter_df = _scrape_table(page, HITTER_URL, "hitters")

            # Brief pause between requests — respectful scraping
            time.sleep(2)

            pitcher_df = _scrape_table(page, PITCHER_URL, "pitchers")
        finally:
            browser.close()

    _validate(hitter_df, HITTER_REQUIRED_COLS, MIN_HITTER_ROWS, "hitters")
    hitter_df = _reorder_columns(hitter_df, HITTER_COLS, "hitters")
    _write_csv(hitter_df, HITTER_OUT, "hitters", dry_run)

    _validate(pitcher_df, PITCHER_REQUIRED_COLS, MIN_PITCHER_ROWS, "pitchers")
    pitcher_df = _reorder_columns(pitcher_df, PITCHER_COLS, "pitchers")
    _write_csv(pitcher_df, PITCHER_OUT, "pitchers", dry_run)

    return hitter_df, pitcher_df


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Scrape rest-of-season player projections from Razzball.com "
            "and write them to projections/hitter_projections.csv and "
            "projections/pitcher_projections.csv."
        )
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--hitters-only",
        action="store_true",
        help="Fetch and write only the hitter projection CSV.",
    )
    group.add_argument(
        "--pitchers-only",
        action="store_true",
        help="Fetch and write only the pitcher projection CSV.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print row counts and column names without writing any files.",
    )
    return parser


def main() -> None:
    args = _build_parser().parse_args()
    log.info(
        "Starting projection fetch (dry_run=%s, hitters_only=%s, pitchers_only=%s)",
        args.dry_run,
        getattr(args, "hitters_only", False),
        getattr(args, "pitchers_only", False),
    )

    try:
        if args.hitters_only:
            fetch_hitters(dry_run=args.dry_run)
        elif args.pitchers_only:
            fetch_pitchers(dry_run=args.dry_run)
        else:
            fetch_both(dry_run=args.dry_run)
    except RuntimeError as exc:
        log.error("Fetch failed: %s", exc)
        sys.exit(1)
    except Exception as exc:
        log.error("Unexpected error: %s", exc, exc_info=True)
        sys.exit(1)

    log.info("Projection fetch complete.")


if __name__ == "__main__":
    main()
