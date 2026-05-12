---
name: project-yahoo-api
description: Yahoo Fantasy API OAuth details, league discovery pattern, and roster response structure used by sync_rosters.py
metadata:
  type: project
---

## Yahoo Fantasy API — key facts

**Auth:** OAuth 2.0 with Bearer token. Client ID and secret live in `.env` as
`YAHOO_CLIENT_ID` / `YAHOO_CLIENT_SECRET`. Tokens cached in `.yahoo_token.json`
(gitignored). Redirect URI is `oob` (out-of-band verifier code flow). Token URL:
`https://api.login.yahoo.com/oauth2/get_token`. Scope: `fspt-r`.

**League discovery endpoint:**
`GET /fantasy/v2/users;use_login=1/games;game_keys=mlb/leagues?format=json`
Response path: `fantasy_content.users["0"].user[1].games["0"].game[1].leagues["0"].league`
(list of dicts). Match by `name` field (case-insensitive substring against
`YAHOO_WMM_LEAGUE_NAME` / `YAHOO_LFL_LEAGUE_NAME` from `.env`).

**Team discovery endpoint:**
`GET /fantasy/v2/league/{league_id}/teams?format=json`
Response path: `fantasy_content.league[1].teams["0"].team[0]` (list of dicts).
Find the user's team via `is_owned_by_current_login == 1`.

**Roster endpoint:**
`GET /fantasy/v2/team/{team_key}/roster?format=json`
Response path: `fantasy_content.team[1].roster["0"].players`
Numeric string keys "0"..."N", plus `"count"` for total.
Each player: `player[0]` is a list of dicts — extract `name.full` and `position_type`.

**Position discrimination:**
`position_type == "B"` → batter/hitter
`position_type == "P"` → pitcher (SP or RP)
This is cleaner than parsing `display_position` or `eligible_positions`.

**Sample data:** `/home/cbyam/postman/lfl-roster-sample.json` — LFL roster response.
The team in the sample is `469.l.71989.t.5` (Woodfields Drive Wombats), managed by "Chris".

**Postman collection:** `/home/cbyam/postman/yahoo-fantasy-api.postman_collection.json`
Contains endpoints for: leagues, WMM/LFL teams, WMM/LFL rosters, WMM free agents.
Variables `wmm_league_id`, `lfl_league_id`, `wmm_team_id`, `lfl_team_id` were empty in the file — the script auto-discovers them at runtime.

**Why:** Replacing manual CSV maintenance (Feature 3).
**How to apply:** When debugging API calls or extending to new endpoints, reference
the response structure above. The `position_type` field is the canonical splitter for pitcher vs hitter.
