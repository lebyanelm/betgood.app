"""
_________________________________
SERVER_NAME
Server description goes here
__________________________________
"""
import os
import pandas as pd
import datetime
import requests
import helpers.all
from flask import Flask, render_template
from flask_cors import CORS, cross_origin
from os import environ
from dotenv import load_dotenv
from classes.response import Response


"""
__________________________________
DEVELOPMENTAL ENVIRONMENT VARIABLES
__________________________________
"""
if environ.get("environment") != "production":
	load_dotenv()


"""
__________________________________
SERVER INSTANCE SETUP
__________________________________
"""
server_instance = Flask(__name__,
    static_folder="./static/",
    static_url_path="/static/")
CORS(server_instance, resources={r"*": {"origins": "*"}})


"""
__________________________________
PAGE VIEW ROUTES
__________________________________
"""
"""Returns status of the server"""
@server_instance.route("/template/status", methods=["GET"])
@cross_origin()
def status():
    return Response(cd=200, msg="Running.").to_json()


@server_instance.route("/", methods=["GET"])
@cross_origin()
def index():
    return render_template("index.html", name="BeGood")


@server_instance.route("/soccer_matches", methods=["GET"])
@cross_origin()
def index_soccer_matches():
    return render_template("soccer_matches.html", name="BeGood")


@server_instance.route("/soccer_matches/match/<match_id>", methods=["GET"])
@cross_origin()
def index_soccer_match(match_id):
    return render_template("match.html", name="BeGood")


"""
__________________________________
BACKEND API ROUTES
__________________________________
"""
# Gets fixtures and makes predictions
@server_instance.route("/predictions/soccer", methods=["GET"])
@cross_origin()
def predictions():
    fixtures = helpers.all.inferences.get_soccer_fixtures()
    results = list()

    for fixture in fixtures:
        if fixture["odds"]["homeWin"] != None:
            features = [fixture["competition"]["id"],
                fixture["homeTeam"]["id"],
                fixture["awayTeam"]["id"],
                fixture["odds"]["homeWin"],
                fixture["odds"]["draw"],
                fixture["exp_weather_condition"]["temperature_2m"],
                fixture["exp_weather_condition"]["relative_humidity_2m"],
                fixture["exp_weather_condition"]["precipitation"],
                fixture["exp_weather_condition"]["cloud_cover"],
                fixture["exp_weather_condition"]["wind_speed_100m"],
                fixture["exp_weather_condition"]["elevation"]]
            # outcome = soccer_estimator.predict([features])

            fixture["day"] = fixture["utcDate"].strftime("%d, %m %Y - %H:%M")
            # fixture["time"] = fixture["utcDate"].time()
            del fixture["utcDate"]
            # fixture["expected_outcome"] = outcome[0]
            results.append(fixture)
    datetime.datetime.now().time
    return Response(cd=200, d=results).to_json()


@server_instance.route("/predictions/financial/<symbol_pair>", methods=["GET"])
@cross_origin()
def get_crypto_symbol_prediction(symbol_pair, interval=60):
    """
    Runs a prediction on the crypto market and returns the direction of the symbol with the data.
    """
    candle_response = requests.get(f"https://www.bitstamp.net/api/v2/ohlc/{symbol_pair}/?step={interval}&limit=30")
    if candle_response.status_code == 200:
        candle_data = financial_indicators.append_technical_indicators(pd.DataFrame.from_dict(candle_response.json()["data"]["ohlc"]))
        current_candle = candle_data.iloc[-1].values.reshape(-5)
        print(current_candle)

        prediction = helpers.all.make_prediction(os.environ["AAPL_MODEL"], list(), values=current_candle)[0]
        print(prediction)

        return Response(cd=200, d=dict(direction="up" if prediction == 1 else "down")).to_json()
    else:
        return Response(cd=candle_response.status_code, rs=f"Something went wrong. {candle_response.text}").to_json()