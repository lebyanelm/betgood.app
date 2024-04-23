import datetime
import requests
import time
import numpy as np
import traceback
import pandas as pd

API_KEY="333bc1de5be842fd954d756e0d67a177"

is_reached_end = False
count = 0
today = datetime.datetime(year=2023, month=11, day=4)
endpoints = list()
data = list()
loaded_requests = 0
total_count = 0
TOTAL_DATA_REQUIRED = 2000

def get_matches(url):
  response = requests.get(url,
                    headers={'X-Unfold-Lineups': "true",
                             'X-Unfold-Goals': "true",
                             'X-Auth-Token': API_KEY})
  if response.status_code == 200:
    return response.json()["matches"]
  else:
    return []

def get_match(id):
  response = requests.get(f'https://api.football-data.org/v4/matches/{id}',
                    headers={'X-Unfold-Lineups': "true",
                             'X-Unfold-Goals': "true",
                             'X-Auth-Token': API_KEY})
  if response.status_code == 200:
    return response.json()
  else:
    return None

while is_reached_end == False:
  try:
    timedelta = datetime.timedelta(days=10)
    past_ten_days = today - timedelta
    endpoint = f"https://api.football-data.org/v4/matches?dateTo={today.strftime('%Y-%m-%d')}&dateFrom={past_ten_days.strftime('%Y-%m-%d')}"

    if loaded_requests == 10:
        print(f'Requests: {loaded_requests}, sleeping.')
        time.sleep(60)
        print(f'Reset, continue.')
        loaded_requests = 0

    matches = get_matches(endpoint)
    loaded_requests += 1

    if matches:
        for match_ in matches:
            if loaded_requests == 10:
                print(f'Requests: {loaded_requests}, sleeping.')
                time.sleep(60)
                print(f'Reset, continue.')
                loaded_requests = 0

            match_ = get_match(match_["id"])
            loaded_requests += 1

            if match_ is not None:
                data.append([
                    match_["id"],
                    match_["utcDate"], # date
                    match_["status"], # status
                    match_["competition"]["name"], # league_name
                    match_["competition"]["id"], # league_id
                    match_["competition"]["type"], # league_type
                    match_["stage"], # stage
                    match_["homeTeam"]["shortName"], # home_name
                    match_["homeTeam"]["id"], # home_id
                    match_["awayTeam"]["shortName"], # away_name
                    match_["awayTeam"]["id"], # away_id
                    match_["venue"], # venue
                    match_["score"]["halfTime"]["home"], # score_home_ht
                    match_["score"]["halfTime"]["away"], # score_away_ht
                    match_["score"]["fullTime"]["home"], # score_home_ft
                    match_["score"]["fullTime"]["away"], # score_away_ft
                    match_["odds"]["homeWin"], # home_odds
                    match_["odds"]["draw"], # draw_odds
                    match_["odds"]["awayWin"], # away_odds
                    -1, # precipitation
                    -1, # temperature
                    -1, # wind_speed
                    -1  # wind_direction
                ])
                total_count += 1
                print(f'Total count: {total_count}')

            if (total_count == TOTAL_DATA_REQUIRED):
                break

    is_reached_end = total_count == TOTAL_DATA_REQUIRED
    today = past_ten_days
  except:
    print(traceback.format_exc())
    # Await the next 60 seconds to be allowed to request more data
    time.sleep(60)
    continue

df = pd.DataFrame(data, columns=["id", "date", "status", "league_name", "league_id", "league_type", "stage", "home_team", "home_team_id", "away_team", "away_team_id", "venue", "score_home_ht", "score_away_ht", "score_home_ft", "score_away_ft", "home_odds", "draw_odds", "away_odds", "precipitation", "temperature", "wind_speed", "wind_direction"])
df.to_csv("data_2.csv", index=False)

# AAPK4ccecd97951a4c1da6418e3fba9e2c58t5qYY8i5kRqFQkT8iKyh_VhKWIQnTVSrH7Cxw-w69tnHkqj91rbvOTyZlMkhQNBV