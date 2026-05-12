Instructions (Ubuntu)

Install python:
- sudo apt install python3

Set up and activate virtual env:
- python3 -m venv streamlit-env
- source streamlit-env/bin/activate
- pip install --upgrade pip
- pip install python-dotenv
- pip install mysql-connector-python
- pip install pandas
- pip install streamlit
- pip install requests

Create .env file:
- DB_HOST=host
- DB_PORT=port
- DB_NAME=db
- DB_USER=user
- DB_PASSWORD=password
- YAHOO_CLIENT_ID=your_yahoo_client_id
- YAHOO_CLIENT_SECRET=your_yahoo_client_secret
- YAHOO_WMM_LEAGUE_NAME=Walter Matthau
- YAHOO_LFL_LEAGUE_NAME=Lion's Field

The YAHOO_CLIENT_ID and YAHOO_CLIENT_SECRET come from the Yahoo developer app registered
for this project. YAHOO_WMM_LEAGUE_NAME and YAHOO_LFL_LEAGUE_NAME are partial, case-insensitive
matches against your Yahoo Fantasy league names — the defaults above should work as-is.

Sync rosters from Yahoo Fantasy API:
- python3 players/sync_rosters.py --dry-run   # preview names without writing files
- python3 players/sync_rosters.py             # write the four players/*.csv files

On the first run you will be prompted to authorize access:
1. A URL is printed — open it in a browser and approve access
2. Yahoo displays a verification code — paste it back into the terminal
3. Tokens are saved to .yahoo_token.json (gitignored) and reused automatically on all future runs

Load projections:
- place csv files in projections directory (hitter_projections.csv and pitcher_projections.csv)
- python3 projections/load_projections.py

Run the app:
- python3 -m streamlit run app.py

Automate daily roster sync and projection load (cron):

First, ensure the log files exist and are writable by the cron user:
- sudo touch /var/log/sync_rosters.log /var/log/load_projections.log
- sudo chown $USER /var/log/sync_rosters.log /var/log/load_projections.log

Then add the following entries via `crontab -e`:

0 0 * * * cd /home/cbyam/projects/fantasy-baseball-dashboard && /home/cbyam/projects/fantasy-baseball-dashboard/projections/.venv/bin/python3 players/sync_rosters.py >> /var/log/sync_rosters.log 2>&1
0 1 * * * cd /home/cbyam/projects/fantasy-baseball-dashboard && /home/cbyam/projects/fantasy-baseball-dashboard/projections/.venv/bin/python3 projections/load_projections.py >> /var/log/load_projections.log 2>&1

sync_rosters.py runs at midnight; load_projections.py runs one hour later.
Note: the Yahoo OAuth token must already be authorized before cron runs (see sync rosters section above).