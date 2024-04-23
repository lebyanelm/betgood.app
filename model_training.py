import pickle
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import accuracy_score
from sklearn.metrics import precision_score
from sklearn.preprocessing import MinMaxScaler
from sklearn.decomposition import PCA



"""Loading datasets"""
data_points = pd.read_csv("./datasets/train_data.csv").dropna().drop_duplicates().reset_index(drop=True)
data_points = data_points.loc[data_points.outcome != -1.0]
outcomes = data_points.pop("outcome").values.reshape((-1))
print(outcomes.shape)

"""Combine the weather data to one feature"""
data = data_points.values


"""Train set"""
TRAIN_SAMPLE_SIZE = int(len(data_points) * 0.8)
X = data[:TRAIN_SAMPLE_SIZE]
Y = outcomes[:TRAIN_SAMPLE_SIZE]


"""Split out the target classes"""
data = data_points.values


"""Test set"""
X_test = data[TRAIN_SAMPLE_SIZE-1:-1]
Y_test = outcomes[TRAIN_SAMPLE_SIZE-1:-1]
rf_classifier = RandomForestClassifier(
  n_estimators=(2),
  min_samples_leaf=(5),
  min_samples_split=(50),
  random_state=(1),
  bootstrap=(True),
  criterion=("gini"))


"""Normalize the data"""
scaler = MinMaxScaler()
X_normalized = scaler.fit_transform(X)
rf_classifier.fit(X, Y)


""""Perfom an accuracy test"""
def perfomance_metric(X_test, Y_test):
  Y_preds = rf_classifier.predict(X_test)
  accuracy = accuracy_score(Y_test, Y_preds)
  precision = precision_score(Y_test, Y_preds, average="weighted")
  combined_actual_to_preds = pd.DataFrame(dict(actual=Y_test, prediction=Y_preds))
  return round(precision, ndigits=2), round(accuracy, ndigits=2), pd.crosstab(index=combined_actual_to_preds["actual"], columns=combined_actual_to_preds["prediction"])


"""Saves the model to be used later."""
def save_model(name, model):
  with open(f'./models/{name}.pkl', 'wb') as f:
      pickle.dump(model, f)


"""Loads a previously saved model for use."""
def load_model(name):
  loaded_model = None
  with open(f'./models/{name}.pkl', 'rb') as f:
    loaded_model = pickle.load(f)
  return loaded_model


"Print out the outcomes"
precision, accuracy, crosstab = perfomance_metric(X_test, Y_test)
print(f'Precision: {precision * 100}%')
print(f'Accuracy: {accuracy * 100}%')
print("\n")
print(crosstab)

# Save a model
save_model("soccor_w-l_rf_estimator", rf_classifier)