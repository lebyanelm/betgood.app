import os
import traceback
import bs4
import requests
import datetime
import pandas as pd


"""Reports unexpected errors via email."""
def report_unexpected_error(error):
    print(error)


"""Loads team labels dataset used in training of the models"""
# def get_model_labels(labels_sheet_name):
#     try:
#         SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTkHUiFAH-Ygbw5HG4-lpCEPHU-sACLCpt4P13-xBbDYYKuW_iy7i-dMu59Ldcn6FoliRAqEfFTxQps/pub?output=xlsx"
#         return pd.read_excel(SHEET_URL, sheet_name=[labels_sheet_name])[labels_sheet_name].values
#     except:
#         raise Exception(f"Failed to load {labels_sheet_name} labels.")

# LABELS = dict(
#     teams = get_model_labels(labels_sheet_name="team_labels")
# )

def get_matches(url):
  response = requests.get(url,
                    headers={'X-Unfold-Lineups': "true",
                             'X-Unfold-Goals': "true",
                             'X-Auth-Token': os.environ.get("FOOTBALL_DATA_API_KEY")})
  if response.status_code == 200:
    print(response.json())
    return response.json()["matches"]
  else:
    return []

def get_fixtures_venues():
    FIXTURES_ENDPOINT = "https://za.soccerway.com"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36'}
    supersport_fixtures = requests.get(FIXTURES_ENDPOINT, headers=headers)

    fixture_venues = dict()
    if supersport_fixtures.status_code == 200:
        soup = bs4.BeautifulSoup(supersport_fixtures.text, 'html.parser')
        match_groups = soup.select(".teams")
        for matches in match_groups:
            href = matches.select('a')[0]["href"]
            match_venue_url = f'{FIXTURES_ENDPOINT}{href}venue'
            match_request = requests.get(match_venue_url, headers=headers)
            soup = bs4.BeautifulSoup(match_request.text, 'html.parser')
            venue_name = soup.select(".block_venue_info-wrapper")[0].select_one(".header-label-2").text.strip()
            team_names = '-'.join(soup.select_one("title").text.split(' - ')[0].split(' vs. ')).lower()
            fixture_venues[team_names] = venue_name
    return fixture_venues


def get_soccer_fixtures():
    all_matches = list()
    match_venues = get_fixtures_venues()
    print(match_venues)

    try:
        today = datetime.datetime.now()
        FOOTBALL_DATA_HEADER = {'X-Unfold-Lineups': "true",
                                                'X-Unfold-Goals': "true",
                                                'X-Auth-Token': os.environ.get("FOOTBALL_DATA_API_KEY")}

        fixtures_request = requests.get(f"https://api.football-data.org/v4/matches?competitions=ED,PL,CLI,PD,BL1,SA,ELC,FL1,PPL,CL&date=TOMORROW",
                                        headers=FOOTBALL_DATA_HEADER)
        
        if fixtures_request.status_code == 200:
            fixtures = fixtures_request.json()
            for fixture in fixtures["matches"]:
                """Focus more on matches that have good odds about 1.5."""
                match_request = requests.get(f"https://api.football-data.org/v4/matches/{fixture['id']}",
                                            headers=FOOTBALL_DATA_HEADER)
                if match_request.status_code == 200:
                    match = match_request.json()
                    match_key = f'{match["homeTeam"]["shortName"]}-{match["awayTeam"]["shortName"]}'.lower()
                    if match_venues.get(match_key):
                       venue = match_venues.get(match_key)
                       match["venue"] = venue
                       match["utcDate"] = datetime.datetime.fromisoformat(match["utcDate"].replace('Z', '+00:00'))
                       start_hour = match["utcDate"].hour
                       lat, lng, place_id = get_stadium_coordinates(venue)
                       exp_weather_condition = get_stadium_future_weather(lat, lng, match["utcDate"].timestamp(), start_hour)
                       match["exp_weather_condition"] = exp_weather_condition
                       match["venue"] = place_id
                       all_matches.append(match)
                else:
                    report_unexpected_error(match_request.json())
                    continue

            return all_matches
        else:
           report_unexpected_error(fixtures_request.json())
           return []
    except:
        report_unexpected_error(traceback.format_exc())

        """Return empty results."""
        return []


def get_stadium_coordinates(stadium_name):
  COORDINATES_ENDPOINT = f"https://geocode-api.arcgis.com/arcgis/rest/services/World/GeocodeServer/findAddressCandidates?=&f=json&token=AAPK4ccecd97951a4c1da6418e3fba9e2c58t5qYY8i5kRqFQkT8iKyh_VhKWIQnTVSrH7Cxw-w69tnHkqj91rbvOTyZlMkhQNBV&address={stadium_name}"
  coordinates_response = requests.get(COORDINATES_ENDPOINT)
  if coordinates_response.status_code == 200:
    locations_found = coordinates_response.json()["candidates"]
    if len(locations_found) == 0: return None, None, None

    best_location = None
    highest_score = 0
    for location_found in locations_found:
      if location_found["score"] > highest_score:
        best_location = location_found
        highest_score = location_found["score"]

    if best_location:
      lat = best_location["location"]["y"]
      lng = best_location["location"]["x"]
      place_id = abs(lat + lng) # use the unique lat/lng coords as the stadium ID
      return lat, lng, place_id
    

def get_stadium_future_weather(lat, lng, timestamp, start_time):
    if lat != None and lng != None and timestamp:
        weather_response = requests.get(f"https://api.weatherapi.com/v1/forecast.json?key=e7a39d8a1019410889f121558212610&q={lat},{lng}&&unixdt={timestamp}")
        stadium_elevation = get_place_elevation(lat, lng)
        if stadium_elevation is not None:
            if weather_response.status_code == 200:
                forcast_hours = weather_response.json()["forecast"]["forecastday"][0]["hour"]
                target_conditions = ["temp_f", "wind_mph", "precip_mm", "humidity", "cloud"]
                avg_conditions = dict()
                for target_condition in target_conditions:
                    avg_conditions[target_condition] = round((forcast_hours[start_time][target_condition] + forcast_hours[start_time + 1][target_condition] + forcast_hours[start_time + 2][target_condition]) / 3, 2)
                return dict(elev_m=stadium_elevation,
                            temperature_2m=avg_conditions["temp_f"],
                            humidity_2m=avg_conditions["humidity"],
                            precipitation=avg_conditions["precip_mm"],
                            cloud_cover=avg_conditions["cloud"],
                            wind_speed_100m=avg_conditions["wind_mph"])
            else:
                print(weather_response.text)
                return None
        else:
           return None
    else:
        return dict(elevation=None,
                    temperature_2m=None,
                    humidity_2m=None,
                    precipitation=None,
                    cloud_cover=None,
                    wind_speed_100m=None)


"""Gets the elevation of a place given the coordinates"""
def get_place_elevation(lat, lng):
    elevation = requests.get(f"https://api.open-elevation.com/api/v1/lookup?locations={lat},{lng}")
    if elevation.status_code == 200:
        return elevation.json()["results"][0]["elevation"]
    else:
        return None
    

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
  