# Fantasy Baseball Dashboard

A Streamlit dashboard displaying z-score rankings for two fantasy baseball leagues
(WMM and LFL) backed by a MySQL database, with daily automated projection scraping
and roster syncing.

---

## Deploy on Ubuntu Server (fresh machine)

This section covers everything needed to get the automated pipeline running on a
bare Ubuntu machine. The Streamlit dashboard can run on the same server or
separately — the pipeline (scraper + DB loader) is the primary concern here.

### 1. System prerequisites

```bash
# Core tools
sudo apt update && sudo apt upgrade -y
sudo apt install -y git python3 python3-pip python3-venv

# MySQL client libraries (required by mysql-connector-python)
sudo apt install -y libmysqlclient-dev default-libmysqlclient-dev

# Google Chrome (required by the Playwright-based Razzball scraper)
# Option A: Chrome stable (recommended)
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" \
    | sudo tee /etc/apt/sources.list.d/google-chrome.list
sudo apt update && sudo apt install -y google-chrome-stable

# Option B: Chromium (if Chrome stable is unavailable)
# sudo apt install -y chromium-browser
```

> The database itself does not need to run on this server. The loader scripts
> connect to whichever MySQL host is set in `.env`.

### 2. Clone the repository

```bash
git clone <your-repo-url> ~/projects/fantasy-baseball-dashboard
cd ~/projects/fantasy-baseball-dashboard
```

### 3. Python virtual environment

The scraper dependencies (Playwright, requests, BeautifulSoup) are isolated in
`projections/.venv`. The cron jobs use this venv's interpreter directly, so
you do not need to activate it manually for automation.

```bash
python3 -m venv projections/.venv
projections/.venv/bin/pip install --upgrade pip

# Core dependencies
projections/.venv/bin/pip install \
    python-dotenv \
    mysql-connector-python \
    pandas \
    requests \
    beautifulsoup4 \
    playwright \
    yahoo-oauth \
    yfinance

# Install Chromium binaries managed by Playwright
projections/.venv/bin/playwright install chromium
```

If you also want to run the Streamlit dashboard on this server, create a
separate venv for it:

```bash
python3 -m venv streamlit-env
source streamlit-env/bin/activate
pip install --upgrade pip
pip install python-dotenv mysql-connector-python pandas streamlit
deactivate
```

### 4. Create the `.env` file

The `.env` file is not in the repo and must be created manually. Place it at the
project root (`~/projects/fantasy-baseball-dashboard/.env`):

```
DB_HOST=your_db_host
DB_PORT=3306
DB_NAME=fantasy_baseball_db
DB_USER=your_db_user
DB_PASSWORD=your_db_password

YAHOO_CLIENT_ID=your_yahoo_client_id
YAHOO_CLIENT_SECRET=your_yahoo_client_secret
YAHOO_WMM_LEAGUE_NAME=Walter Matthau
YAHOO_LFL_LEAGUE_NAME=Lion's Field
```

`YAHOO_WMM_LEAGUE_NAME` and `YAHOO_LFL_LEAGUE_NAME` are partial, case-insensitive
matches against your Yahoo Fantasy league names — the defaults above should work
as-is.

### 5. Authorize Yahoo OAuth (one-time, interactive)

The Yahoo roster sync uses OAuth 2.0. The first run requires a browser to
approve access; all subsequent runs reuse the saved token automatically.

```bash
cd ~/projects/fantasy-baseball-dashboard
projections/.venv/bin/python3 players/sync_rosters.py --dry-run
```

On first run:
1. A URL is printed — open it in a browser and approve access.
2. Yahoo displays a verification code — paste it back into the terminal.
3. Tokens are saved to `.yahoo_token.json` (gitignored) and reused on all
   future runs, including cron.

### 6. Create log files

The cron jobs append to files in `/var/log/`. Create them and grant write
access to the user that will own the cron jobs (typically your login user):

```bash
sudo touch /var/log/sync_rosters.log /var/log/fetch_projections.log /var/log/load_projections.log
sudo chown $USER /var/log/sync_rosters.log /var/log/fetch_projections.log /var/log/load_projections.log
```

### 7. Set up cron jobs

Run `crontab -e` and add the three entries below. Replace `/home/cbyam` with
your actual home directory if different.

```cron
# Fantasy baseball pipeline — runs nightly in sequence
# Midnight: sync Yahoo rosters → players/*.csv
0 0 * * * cd /home/cbyam/projects/fantasy-baseball-dashboard && /home/cbyam/projects/fantasy-baseball-dashboard/projections/.venv/bin/python3 players/sync_rosters.py >> /var/log/sync_rosters.log 2>&1

# 1 AM: scrape Razzball projections → projections/*.csv
0 1 * * * cd /home/cbyam/projects/fantasy-baseball-dashboard && /home/cbyam/projects/fantasy-baseball-dashboard/projections/.venv/bin/python3 projections/fetch_projections.py >> /var/log/fetch_projections.log 2>&1

# 2 AM: load projections into MySQL
0 2 * * * cd /home/cbyam/projects/fantasy-baseball-dashboard && /home/cbyam/projects/fantasy-baseball-dashboard/projections/.venv/bin/python3 projections/load_projections.py >> /var/log/load_projections.log 2>&1
```

Execution order: `sync_rosters.py` (midnight) -> `fetch_projections.py` (1 AM)
-> `load_projections.py` (2 AM). Each job is independent; a one-hour gap
between them is sufficient headroom.

### 8. Verify the pipeline runs end-to-end

Test each script manually before relying on cron:

```bash
cd ~/projects/fantasy-baseball-dashboard

# Roster sync (dry run first)
projections/.venv/bin/python3 players/sync_rosters.py --dry-run
projections/.venv/bin/python3 players/sync_rosters.py

# Projection scraper (dry run first)
projections/.venv/bin/python3 projections/fetch_projections.py --dry-run
projections/.venv/bin/python3 projections/fetch_projections.py

# DB loader
projections/.venv/bin/python3 projections/load_projections.py
```

Check logs after the first cron run:

```bash
tail -50 /var/log/sync_rosters.log
tail -50 /var/log/fetch_projections.log
tail -50 /var/log/load_projections.log
```

---

## Running the Streamlit dashboard

If the dashboard runs on this server, start it with the streamlit venv:

```bash
cd ~/projects/fantasy-baseball-dashboard
source streamlit-env/bin/activate
python3 -m streamlit run app.py
```

To keep it running as a background service, use a `systemd` unit or `tmux`/`screen`.

---

## Running scripts individually

### Sync rosters from Yahoo Fantasy API

```bash
python3 players/sync_rosters.py --dry-run   # preview names without writing files
python3 players/sync_rosters.py             # write the four players/*.csv files
```

### Fetch projections from Razzball

```bash
python3 projections/fetch_projections.py --dry-run   # preview row/column counts without writing files
python3 projections/fetch_projections.py             # scrape and write both CSVs
python3 projections/fetch_projections.py --hitters-only
python3 projections/fetch_projections.py --pitchers-only
```

### Load projections into MySQL

```bash
python3 projections/load_projections.py
python3 projections/load_projections.py --hitters-only
python3 projections/load_projections.py --pitchers-only
```

---

## Pulling repo updates on the server

When you push changes from another machine, pull them on the server before the
next cron run:

```bash
cd ~/projects/fantasy-baseball-dashboard
git pull
```

If new Python dependencies were added, reinstall into the venv:

```bash
projections/.venv/bin/pip install -r requirements.txt   # if a requirements file is added
# or install the new package explicitly:
projections/.venv/bin/pip install <new-package>
```

---

## Database schema

SQL DDL for the projection tables and z-score views is in `db/`. The views
recompute z-scores automatically on every query — no manual refresh needed
after loading new projections.
