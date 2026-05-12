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
- place csv files in projections directory (hitter-projections.csv and pitcher-projections.csv)
- python3 projections/load_hitter_projections.py
- python3 projections/load_pitcher_projections.py

Run the app:
- python3 -m streamlit run app.py