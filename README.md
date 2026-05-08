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

Create .env file:
- DB_HOST=host
- DB_PORT=port
- DB_NAME=db
- DB_USER=user
- DB_PASSWORD=password

Load projections:
- place csv files in projections directory (hitter-projections.csv and pitcher-projections.csv)
- python3 projections/load_hitter_projections.py
- python3 projections/load_pitcher_projections.py

Generate dashboards:
- python3 -m streamlit run dashboards/hitters_dashboard.py
- python3 -m streamlit run dashboards/pitchers_dashboard.py
- python3 -m streamlit run dashboards/player_comp_dashboard.py