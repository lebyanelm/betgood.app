"""
_________________________________
SERVER_NAME
Server description goes here
__________________________________
"""
import pickle
import helpers
from flask import Flask
from flask_cors import CORS, cross_origin
from pymongo import MongoClient
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
    static_folder="./assets/",
    static_url_path="/server_name/assets/")
CORS(server_instance, resources={r"*": {"origins": "*"}})

"""
__________________________________
DATABASE CONNECTION
__________________________________
"""
client = None
if environ.get("MONGO_CONNECTION"):
    client = MongoClient(environ.get("MONGODB_CONNECTION"), tlsInsecure=True)


"""
__________________________________
LOAD THE MODELS
__________________________________
"""
soccer_estimator = None
with open("./models/soccer-estimator.pkl", 'rb') as f:
    soccer_estimator = pickle.load(f)


"""
__________________________________
SERVER INSTANCE ROUTES
__________________________________
"""
# Returns status of the server
@server_instance.route("/template/status", methods=["GET"])
@cross_origin()
def status():
    return Response(cd=200, msg="Running.").to_json()


# Gets fixtures and makes predictions
@server_instance.route("/predictions/soccer", methods=["GET"])
@cross_origin()
def get_soccer_predictions():
    fixtures = helpers.get_soccer_fixtures()
    all_predictions = dict(fixtures=list())

    for league_name in fixtures["leagues"]:
        league_matches = fixtures["fixtures"][league_name]
        
        league_predictions = list()
        for index, upcoming_match in enumerate(fixtures["fixtures"][league_name]):
            """Get the label IDs"""
            fixtures["fixtures"][league_name][index]["home_id"] = helpers.get_label_id(type="teams", 
                                                                                        target_label=fixtures["fixtures"][league_name][index]["home_name"])
            fixtures["fixtures"][league_name][index]["away_id"] = helpers.get_label_id(type="teams", 
                                                                                        target_label=fixtures["fixtures"][league_name][index]["away_name"])

            """Get the estimator"""
            prediction_result = helpers.get_soccer_match_prediction(predictors=[
                                    fixtures["fixtures"][league_name][index]["day"],
                                    fixtures["fixtures"][league_name][index]["hour"],
                                    fixtures["fixtures"][league_name][index]["home_odds"],
                                    fixtures["fixtures"][league_name][index]["draw_odds"],
                                    fixtures["fixtures"][league_name][index]["away_odds"],
                                    fixtures["fixtures"][league_name][index]["home_id"],
                                    fixtures["fixtures"][league_name][index]["away_id"],
                                ], model=soccer_estimator)
            
            """Decode the estimator"""
            if prediction_result[0] == fixtures["fixtures"][league_name][index]["home_id"]:
                fixtures["fixtures"][league_name][index]["home_result"] = "W"
                fixtures["fixtures"][league_name][index]["away_result"] = "L"
                fixtures["fixtures"][league_name][index]["home_result_color"] = "4db33d"
                fixtures["fixtures"][league_name][index]["away_result_color"] = "777777"

                fixtures["fixtures"][league_name][index]["home_pred"] = round(prediction_result[1] * 100, 2)
                fixtures["fixtures"][league_name][index]["draw_pred"] = 0
                fixtures["fixtures"][league_name][index]["away_pred"] = round((1-prediction_result[1]) * 100, 2)
            
            else:
                fixtures["fixtures"][league_name][index]["home_result"] = "L"
                fixtures["fixtures"][league_name][index]["away_result"] = "W"
                fixtures["fixtures"][league_name][index]["home_result_color"] = "777777"
                fixtures["fixtures"][league_name][index]["away_result_color"] = "4db33d"

                fixtures["fixtures"][league_name][index]["home_pred"] = round((1-prediction_result[1]) * 100, 2)
                fixtures["fixtures"][league_name][index]["draw_pred"] = 0
                fixtures["fixtures"][league_name][index]["away_pred"] = round(prediction_result[1] * 100, 2)
                
            fixtures["fixtures"][league_name][index]["home_name"] = fixtures["fixtures"][league_name][index]["home_name"].upper()
            fixtures["fixtures"][league_name][index]["away_name"] = fixtures["fixtures"][league_name][index]["away_name"].upper()

    """Prepare the fixtures to be sent to an email."""
    email_data = dict(fixtures=list())
    for league_name in fixtures["leagues"]:
        email_data["fixtures"].append(dict(is_name=True, name=league_name))
        for match in fixtures["fixtures"][league_name]:
            email_data["fixtures"].append(match)

    return Response(cd=200, d=email_data).to_json()