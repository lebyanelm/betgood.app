import traceback
import bs4
import requests
import json
import datetime
import pandas as pd

LEAGUES = [{"name": "Premier League", "url": "https://www.oddsportal.com/football/england/premier-league"}]

"""Reports unexpected errors via email."""
def report_unexpected_error(error):
    print(error)


"""Loads team labels dataset used in training of the models"""
def get_model_labels(labels_sheet_name):
    try:
        SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTkHUiFAH-Ygbw5HG4-lpCEPHU-sACLCpt4P13-xBbDYYKuW_iy7i-dMu59Ldcn6FoliRAqEfFTxQps/pub?output=xlsx"
        return pd.read_excel(SHEET_URL, sheet_name=[labels_sheet_name])[labels_sheet_name].values
    except:
        raise Exception(f"Failed to load {labels_sheet_name} labels.")

LABELS = dict(
    teams = get_model_labels(labels_sheet_name="team_labels")
)


def get_soccer_fixtures():
    all_matches = dict(leagues=list(), fixtures=dict())

    try:
        for league in LEAGUES:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36'}
            response = requests.get(league["url"], headers=headers)

            if response.status_code == 200:
                soup = bs4.BeautifulSoup(response.text, 'html.parser')
                main_container = soup.find('div', class_="flex flex-col px-3 text-sm max-mm:px-0")
                data = json.loads(main_container.find("next-matches").attrs[":comp-data"])
                odds_response = requests.get(f'https://www.oddsportal.com{data["oddsRequest"]["url"]}', headers=headers)
                events = data["d"]["rows"]

                league_matches = []

                if odds_response.status_code == 200:
                    odds = odds_response.json()

                    for row in events:
                        event_id = row["encodeEventId"]
                        match_odds = odds["d"]["oddsData"][event_id]["odds"]

                        league_matches.append(dict(
                            id = row["id"],
                            event_id = event_id,
                            home_logo = f'https://www.oddsportal.com{row["home-participant-images"][0]}',
                            home_name = row["home-name"],
                            away_name = row["away-name"],
                            away_logo = f'https://www.oddsportal.com{row["away-participant-images"][0]}',
                            match_result = row["postmatchResult"],
                            partial_result = row["partialresult"],
                            date_timestamp = row["date-start-timestamp"],
                            home_odds = match_odds[0]["avgOdds"],
                            draw_odds = match_odds[1]["avgOdds"],
                            away_odds = match_odds[2]["avgOdds"]
                        ))

                    # Check if any of the matches have already played
                    for index, _ in enumerate(league_matches):
                        """Convert the datetime timestamp to extract its features"""
                        league_matches[index]["date"] = datetime.datetime.fromtimestamp(league_matches[index]["date_timestamp"])
                        league_matches[index]["day"] = league_matches[index]["date"].weekday()
                        league_matches[index]["hour"] = league_matches[index]["date"].hour
                        del league_matches[index]["date"]
                        del league_matches[index]["date_timestamp"]

                        if league_matches[index]["match_result"] == "":
                           league_matches[index]["completed"] = True # Save the match for future uses on fitting new models. 
                        else:
                           league_matches[index]["completed"] = False # Save the match for future uses on fitting new models. 
                    
                    all_matches["leagues"].append(league["name"])
                    all_matches["fixtures"][league["name"]] = league_matches
                else:
                    print("Error loading odds.")
            else:
                print('Failed to retrieve webpage:', response.status_code)
        return all_matches
    except:
        report_unexpected_error(traceback.format_exc())

        """Return empty results."""
        return all_matches


"""Reads from the training data labels and returns ID for each team assigned label"""
def get_label_id(type, target_label):
  label = None
  for team_label in LABELS[type]:
    if team_label[0] == target_label:
      label = team_label[1]
  return label


"""Given a model, performs a model and returns (prediction, probability)"""
def get_soccer_match_prediction(predictors: list, model):
  prediction = model.predict([predictors])[0]
  return predictors[5] if prediction == 1 else predictors[6], model.predict_proba([predictors])[0][0]
  