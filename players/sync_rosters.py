"""
sync_rosters.py — Sync fantasy baseball rosters from Yahoo Fantasy API.

Fetches the current roster for the user's team in both WMM and LFL leagues
and writes four CSV files:
    players/hitters_wmm.csv
    players/hitters_lfl.csv
    players/pitchers_wmm.csv
    players/pitchers_lfl.csv

Each file has a single NAME column (no index), matching the format that
app.py expects.

Auth uses OAuth 2.0. On first run an authorization URL will be printed;
visit it, approve access, and paste the redirect URL back. The resulting
tokens are saved to the file named by YAHOO_TOKEN_FILE in .env (default:
.yahoo_token.json) and refreshed automatically on subsequent runs.

Required .env variables:
    YAHOO_CLIENT_ID       — from your Yahoo developer app
    YAHOO_CLIENT_SECRET   — from your Yahoo developer app
    YAHOO_WMM_LEAGUE_NAME — partial or full name of WMM league (case-insensitive)
    YAHOO_LFL_LEAGUE_NAME — partial or full name of LFL league (case-insensitive)

Optional .env variables:
    YAHOO_TOKEN_FILE      — path to token cache file (default: .yahoo_token.json)

Usage:
    python3 players/sync_rosters.py
    python3 players/sync_rosters.py --dry-run   # print names, skip writing CSVs
"""

import argparse
import json
import logging
import os
import sys
import time
import webbrowser
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode, urlparse, parse_qs

import pandas as pd
import requests
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

YAHOO_AUTH_URL = "https://api.login.yahoo.com/oauth2/request_auth"
YAHOO_TOKEN_URL = "https://api.login.yahoo.com/oauth2/get_token"
YAHOO_API_BASE = "https://fantasysports.yahooapis.com/fantasy/v2"
REDIRECT_URI = "oob"  # out-of-band: Yahoo prints the verifier code to the page
SCOPE = "fspt-r"

PITCHER_POSITION_TYPE = "P"
HITTER_POSITION_TYPE = "B"

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

def load_config() -> dict:
    """Load and validate required environment variables."""
    load_dotenv()

    required = ["YAHOO_CLIENT_ID", "YAHOO_CLIENT_SECRET",
                "YAHOO_WMM_LEAGUE_NAME", "YAHOO_LFL_LEAGUE_NAME"]
    missing = [k for k in required if not os.getenv(k)]
    if missing:
        log.error("Missing required .env variables: %s", ", ".join(missing))
        sys.exit(1)

    return {
        "client_id": os.environ["YAHOO_CLIENT_ID"],
        "client_secret": os.environ["YAHOO_CLIENT_SECRET"],
        "wmm_league_name": os.environ["YAHOO_WMM_LEAGUE_NAME"],
        "lfl_league_name": os.environ["YAHOO_LFL_LEAGUE_NAME"],
        "token_file": os.getenv("YAHOO_TOKEN_FILE", ".yahoo_token.json"),
    }

# ---------------------------------------------------------------------------
# OAuth 2.0 token management
# ---------------------------------------------------------------------------

def _token_is_expired(token_data: dict) -> bool:
    """Return True if the access token is expired or about to expire (60s buffer)."""
    expires_at = token_data.get("expires_at", 0)
    return time.time() >= (expires_at - 60)


def _save_token(token_file: str, token_data: dict) -> None:
    token_data["expires_at"] = time.time() + token_data.get("expires_in", 3600)
    with open(token_file, "w") as fh:
        json.dump(token_data, fh, indent=2)
    log.info("Token saved to %s", token_file)


def _fetch_token_with_code(client_id: str, client_secret: str, code: str) -> dict:
    """Exchange an authorization code for access + refresh tokens."""
    resp = requests.post(
        YAHOO_TOKEN_URL,
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": REDIRECT_URI,
            "code": code,
            "grant_type": "authorization_code",
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def _refresh_access_token(client_id: str, client_secret: str,
                          refresh_token: str) -> dict:
    """Use a refresh token to get a new access token."""
    resp = requests.post(
        YAHOO_TOKEN_URL,
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": REDIRECT_URI,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def get_access_token(config: dict) -> str:
    """
    Return a valid access token, refreshing or running the full OAuth flow
    as needed.
    """
    client_id = config["client_id"]
    client_secret = config["client_secret"]
    token_file = config["token_file"]

    # --- Try loading cached token ---
    if os.path.exists(token_file):
        with open(token_file) as fh:
            token_data = json.load(fh)

        if not _token_is_expired(token_data):
            log.info("Using cached access token (expires in ~%ds)",
                     int(token_data.get("expires_at", 0) - time.time()))
            return token_data["access_token"]

        # Token expired — try refresh
        refresh_token = token_data.get("refresh_token")
        if refresh_token:
            log.info("Access token expired; refreshing...")
            try:
                new_token = _refresh_access_token(client_id, client_secret,
                                                  refresh_token)
                _save_token(token_file, new_token)
                return new_token["access_token"]
            except requests.HTTPError as exc:
                log.warning("Token refresh failed (%s); re-authorizing...", exc)

    # --- Full authorization flow ---
    auth_params = urlencode({
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": SCOPE,
    })
    auth_url = f"{YAHOO_AUTH_URL}?{auth_params}"

    print("\n" + "=" * 70)
    print("Yahoo OAuth authorization required.")
    print("Open this URL in your browser:\n")
    print(f"  {auth_url}")
    print("\nAfter approving, Yahoo will show you a verification code.")
    print("=" * 70)

    code = input("Paste the verification code here: ").strip()
    if not code:
        log.error("No code provided; aborting.")
        sys.exit(1)

    token_data = _fetch_token_with_code(client_id, client_secret, code)
    _save_token(token_file, token_data)
    return token_data["access_token"]

# ---------------------------------------------------------------------------
# Yahoo Fantasy API helpers
# ---------------------------------------------------------------------------

def _api_get(url: str, access_token: str) -> dict:
    """GET a Yahoo Fantasy API URL and return the parsed JSON."""
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
    }
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()


def discover_league_ids(access_token: str, wmm_name: str,
                        lfl_name: str) -> tuple[str, str]:
    """
    Query the authenticated user's MLB leagues and return (wmm_league_id,
    lfl_league_id) by matching league names (case-insensitive substring).
    """
    url = (f"{YAHOO_API_BASE}/users;use_login=1"
           "/games;game_keys=mlb/leagues?format=json")
    data = _api_get(url, access_token)

    leagues = []
    try:
        games = data["fantasy_content"]["users"]["0"]["user"][1]["games"]
        game_count = games["count"]
        for i in range(game_count):
            game_obj = games.get(str(i), {})
            game = game_obj.get("game", [])
            # leagues are the second element in the game list
            if len(game) > 1 and isinstance(game[1], dict):
                league_block = game[1].get("leagues", {})
                league_count = league_block.get("count", 0)
                for j in range(league_count):
                    league = league_block.get(str(j), {}).get("league", [])
                    league_info = {item_key: item_val
                                   for item in league
                                   if isinstance(item, dict)
                                   for item_key, item_val in item.items()}
                    league_key = league_info.get("league_key", "")
                    league_name = league_info.get("name", "")
                    leagues.append((league_key, league_name))
    except (KeyError, IndexError, TypeError) as exc:
        log.error("Unexpected structure in leagues response: %s", exc)
        log.debug("Response: %s", json.dumps(data, indent=2))
        sys.exit(1)

    if not leagues:
        log.error("No leagues found. Verify the game_keys=mlb parameter and "
                  "that the account has active MLB leagues.")
        sys.exit(1)

    log.info("Found %d league(s): %s",
             len(leagues),
             [(key, name) for key, name in leagues])

    wmm_id = lfl_id = None
    for key, name in leagues:
        if wmm_name.lower() in name.lower():
            wmm_id = key
        if lfl_name.lower() in name.lower():
            lfl_id = key

    if not wmm_id:
        log.error("Could not find WMM league matching '%s' among: %s",
                  wmm_name, [n for _, n in leagues])
        sys.exit(1)
    if not lfl_id:
        log.error("Could not find LFL league matching '%s' among: %s",
                  lfl_name, [n for _, n in leagues])
        sys.exit(1)

    log.info("WMM league ID: %s", wmm_id)
    log.info("LFL league ID: %s", lfl_id)
    return wmm_id, lfl_id


def find_my_team_id(league_id: str, access_token: str) -> str:
    """
    Return the team_key for the currently authenticated user's team in a league.
    """
    url = f"{YAHOO_API_BASE}/league/{league_id}/teams?format=json"
    data = _api_get(url, access_token)

    try:
        teams = data["fantasy_content"]["league"][1]["teams"]
        team_count = teams["count"]
        for i in range(team_count):
            team_obj = teams.get(str(i), {}).get("team", [])
            # team[0] is a list of dicts with team metadata
            meta = {item_key: item_val
                    for item in team_obj[0]
                    if isinstance(item, dict)
                    for item_key, item_val in item.items()}
            if meta.get("is_owned_by_current_login"):
                team_key = meta.get("team_key", "")
                team_name = meta.get("name", "")
                log.info("My team in league %s: '%s' (%s)",
                         league_id, team_name, team_key)
                return team_key
    except (KeyError, IndexError, TypeError) as exc:
        log.error("Unexpected structure in teams response: %s", exc)
        log.debug("Response: %s", json.dumps(data, indent=2))
        sys.exit(1)

    log.error("No team owned by current login found in league %s", league_id)
    sys.exit(1)


def fetch_roster(team_key: str, access_token: str) -> list[dict]:
    """
    Return a list of player dicts with keys 'name' and 'position_type'
    for every player on the roster.
    """
    url = f"{YAHOO_API_BASE}/team/{team_key}/roster?format=json"
    data = _api_get(url, access_token)

    players = []
    try:
        players_block = (
            data["fantasy_content"]["team"][1]["roster"]["0"]["players"]
        )
        player_count = players_block["count"]
        for i in range(player_count):
            player_obj = players_block.get(str(i), {}).get("player", [])
            # player[0] is a list of dicts with player metadata
            info = {item_key: item_val
                    for item in player_obj[0]
                    if isinstance(item, dict)
                    for item_key, item_val in item.items()}
            full_name = info.get("name", {}).get("full", "")
            pos_type = info.get("position_type", "")
            if full_name and pos_type:
                players.append({"name": full_name, "position_type": pos_type})
            else:
                log.warning("Skipping player with missing name or position: %s",
                            info)
    except (KeyError, IndexError, TypeError) as exc:
        log.error("Unexpected structure in roster response: %s", exc)
        log.debug("Response: %s", json.dumps(data, indent=2))
        sys.exit(1)

    log.info("Fetched %d players from team %s", len(players), team_key)
    return players


# ---------------------------------------------------------------------------
# CSV writing
# ---------------------------------------------------------------------------

PLAYERS_DIR = Path(__file__).parent  # players/ directory

def split_roster(players: list[dict]) -> tuple[list[str], list[str]]:
    """Split a flat player list into (hitter_names, pitcher_names)."""
    hitters = [p["name"] for p in players
               if p["position_type"] == HITTER_POSITION_TYPE]
    pitchers = [p["name"] for p in players
                if p["position_type"] == PITCHER_POSITION_TYPE]
    return hitters, pitchers


def write_csv(names: list[str], filepath: Path, dry_run: bool) -> None:
    """Write a single-column NAME CSV to filepath."""
    df = pd.DataFrame({"NAME": names})
    if dry_run:
        log.info("[DRY RUN] Would write %d names to %s:\n%s",
                 len(names), filepath, df.to_string(index=False))
        return
    df.to_csv(filepath, index=False)
    log.info("Wrote %d names to %s", len(names), filepath)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sync Yahoo Fantasy baseball rosters to players/ CSVs."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print results without writing CSV files.",
    )
    args = parser.parse_args()

    config = load_config()
    log.info("Starting roster sync (dry_run=%s)", args.dry_run)

    # Authenticate
    access_token = get_access_token(config)

    # Discover league IDs for WMM and LFL
    wmm_league_id, lfl_league_id = discover_league_ids(
        access_token,
        config["wmm_league_name"],
        config["lfl_league_name"],
    )

    # Find this user's team in each league
    wmm_team_key = find_my_team_id(wmm_league_id, access_token)
    lfl_team_key = find_my_team_id(lfl_league_id, access_token)

    # Fetch rosters
    wmm_players = fetch_roster(wmm_team_key, access_token)
    lfl_players = fetch_roster(lfl_team_key, access_token)

    # Split by position type
    wmm_hitters, wmm_pitchers = split_roster(wmm_players)
    lfl_hitters, lfl_pitchers = split_roster(lfl_players)

    log.info("WMM: %d hitters, %d pitchers", len(wmm_hitters), len(wmm_pitchers))
    log.info("LFL: %d hitters, %d pitchers", len(lfl_hitters), len(lfl_pitchers))

    # Sanity check — warn if counts look unusually low
    for label, names in [("WMM hitters", wmm_hitters),
                          ("WMM pitchers", wmm_pitchers),
                          ("LFL hitters", lfl_hitters),
                          ("LFL pitchers", lfl_pitchers)]:
        if len(names) < 3:
            log.warning("Suspiciously few %s (%d) — double-check the output.",
                        label, len(names))

    # Write CSVs
    write_csv(wmm_hitters, PLAYERS_DIR / "hitters_wmm.csv", args.dry_run)
    write_csv(wmm_pitchers, PLAYERS_DIR / "pitchers_wmm.csv", args.dry_run)
    write_csv(lfl_hitters, PLAYERS_DIR / "hitters_lfl.csv", args.dry_run)
    write_csv(lfl_pitchers, PLAYERS_DIR / "pitchers_lfl.csv", args.dry_run)

    log.info("Roster sync complete.")


if __name__ == "__main__":
    main()
