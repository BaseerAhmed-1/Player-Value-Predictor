from flask import Flask, request, jsonify, render_template
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score

app = Flask(__name__)

FEATURES = ["age", "reactions", "composure", "ball_control", "dribbling", "Technical_Skill"]
RADAR_ATTRS = ["reactions", "composure", "ball_control", "dribbling"]

# ---------------- Load data & train model once at startup ----------------
df = pd.read_csv("PlayerStats.csv")
df = df.rename(columns={
    "value_euro": "value", "height_cm": "height", "weight_kgs": "weight",
    "nationality": "country", "name": "player"
})
df["Technical_Skill"] = df[["ball_control", "dribbling"]].mean(axis=1)

ml_df = df[FEATURES + ["value"]].dropna()
X, y = ml_df[FEATURES], ml_df["value"]

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

model = RandomForestRegressor(n_estimators=100, max_depth=20, random_state=42)
model.fit(X_train, y_train)
TEST_R2 = r2_score(y_test, model.predict(X_test))


def predict_value(age, reactions, composure, ball_control, dribbling):
    tech = (ball_control + dribbling) / 2
    row = pd.DataFrame([[age, reactions, composure, ball_control, dribbling, tech]], columns=FEATURES)
    return float(model.predict(scaler.transform(row))[0])


# ---------------- Routes ----------------
@app.route("/")
def index():
    return render_template("index.html", r2=round(TEST_R2, 3), count=len(ml_df))


@app.route("/api/predict", methods=["POST"])
def api_predict():
    d = request.json
    value = predict_value(d["age"], d["reactions"], d["composure"], d["ball_control"], d["dribbling"])
    return jsonify({"value": value})


@app.route("/api/whatif", methods=["POST"])
def api_whatif():
    d = request.json
    attr = d["attr"]
    base = d["base"]
    x_range = range(16, 46) if attr == "age" else range(1, 101)
    results = []
    for v in x_range:
        args = dict(base)
        args[attr] = v
        results.append({"x": v, "y": predict_value(**args)})
    return jsonify(results)


@app.route("/api/similar", methods=["POST"])
def api_similar():
    d = request.json
    lookup = df.dropna(subset=RADAR_ATTRS + ["player", "value"]).copy()
    target = np.array([d["reactions"], d["composure"], d["ball_control"], d["dribbling"]])
    lookup["distance"] = lookup[RADAR_ATTRS].apply(lambda row: np.linalg.norm(row.values - target), axis=1)
    closest = lookup.sort_values("distance").head(10)
    cols = [c for c in ["player", "country", "value"] + RADAR_ATTRS if c in closest.columns]
    return jsonify(closest[cols].to_dict(orient="records"))


@app.route("/api/leaderboard")
def api_leaderboard():
    top = df.dropna(subset=["value", "player"]).sort_values("value", ascending=False).head(10)
    return jsonify(top[["player", "value"]].to_dict(orient="records"))


@app.route("/api/age-trend")
def api_age_trend():
    trend = df.dropna(subset=["value", "age"]).groupby("age")["value"].median().reset_index()
    return jsonify(trend.to_dict(orient="records"))


if __name__ == "__main__":
    app.run(debug=True, port=5000)
