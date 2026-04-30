Install python:
- brew install python

Install dependencies:
- pip3 install python-dotenv
- pip3 install mysql-connector-python
- pip3 install pandas
- pip3 install streamlit

Create .env file:
- DB_HOST=host
- DB_PORT=port
- DB_NAME=db
- DB_USER=user
- DB_PASSWORD=password

Load projections:
- place csv files in projections directory (hitter-projections.csv and pitcher-projections.csv)
- python3 projections/load-hitter-projections.py
- python3 projections/load-pitcher-projections.py

Generate dashboards:
- python3 -m streamlit run dashboards/hitters_dashboard.py
- python3 -m streamlit run dashboards/pitchers_dashboard.py
- python3 -m streamlit run dashboards/trade_dashboard.py
- python3 -m streamlit run dashboards/playground_dashboard.py