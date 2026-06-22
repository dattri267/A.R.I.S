from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import pandas as pd
import os

app = Flask(__name__)
CORS(app)

# -------------------------
# LOAD DATA
# -------------------------
# Create sample data if data.csv doesn't exist
if not os.path.exists("data.csv"):
    sample_data = {
        "Zone": ["Zone A - Anand Vihar", "Zone B - Rohini", "Zone C - Dwarka", "Zone D - Noida Sector 62", "Zone E - Gurugram"],
        "AQI": [380, 245, 175, 310, 290],
        "Traffic": [85, 60, 40, 70, 75],
        "Construction": [70, 45, 30, 80, 55],
        "Industry": [60, 50, 25, 65, 70],
        "Wind": [8, 12, 18, 6, 10],
        "Lat": [28.6469, 28.7041, 28.5921, 28.6270, 28.4595],
        "Lon": [77.3164, 77.1025, 77.0458, 77.3665, 77.0266]
    }
    df = pd.DataFrame(sample_data)
    df.to_csv("data.csv", index=False)
else:
    df = pd.read_csv("data.csv")

# Add lat/lon defaults if not present
if "Lat" not in df.columns:
    df["Lat"] = 28.6139
if "Lon" not in df.columns:
    df["Lon"] = 77.2090


@app.route("/", methods=["GET"])
def landing():
    """Serve the landing page."""
    return render_template("landing.html")


@app.route("/dashboard", methods=["GET"])
def dashboard():
    """Serve the main project dashboard (A.R.I.S War Room)."""
    return render_template("dashboard.html")


@app.route("/api/zones", methods=["GET"])
def get_zones():
    """Return list of available zones."""
    zones = df["Zone"].tolist()
    return jsonify({"zones": zones})


@app.route("/api/zone/<path:zone_name>", methods=["GET"])
def get_zone_data(zone_name):
    """Return full data for a specific zone."""
    row = df[df["Zone"] == zone_name]
    if row.empty:
        return jsonify({"error": "Zone not found"}), 404

    row = row.iloc[0]
    aqi = int(row["AQI"])
    traffic = int(row["Traffic"])
    construction = int(row["Construction"])
    industry = int(row["Industry"])
    wind = float(row["Wind"])
    lat = float(row.get("Lat", 28.6139))
    lon = float(row.get("Lon", 77.2090))

    # Risk level
    if aqi > 300:
        risk = "Severe"
        risk_color = "#93000a"
    elif aqi > 200:
        risk = "High"
        risk_color = "#ca8100"
    else:
        risk = "Moderate"
        risk_color = "#00a572"

    # AI Attribution Engine
    traffic_score = traffic * 0.4
    construction_score = construction * 0.3
    industry_score = industry * 0.3
    total = traffic_score + construction_score + industry_score

    traffic_percent = int((traffic_score / total) * 100)
    construction_percent = int((construction_score / total) * 100)
    industry_percent = int((industry_score / total) * 100)

    causes = []
    if traffic_percent > 30:
        causes.append("Traffic")
    if construction_percent > 25:
        causes.append("Construction")
    if industry_percent > 25:
        causes.append("Industry")

    # Forecasting
    future_6 = aqi + 20
    future_12 = aqi + 40

    # Confidence
    confidence = min(95, int((traffic_percent + construction_percent + industry_percent) / 1.2))

    return jsonify({
        "zone": zone_name,
        "aqi": aqi,
        "traffic": traffic,
        "construction": construction,
        "industry": industry,
        "wind": wind,
        "lat": lat,
        "lon": lon,
        "risk": risk,
        "risk_color": risk_color,
        "traffic_percent": traffic_percent,
        "construction_percent": construction_percent,
        "industry_percent": industry_percent,
        "causes": causes,
        "future_6h": future_6,
        "future_12h": future_12,
        "confidence": confidence
    })


@app.route("/api/zone/<path:zone_name>/plan", methods=["GET"])
def get_intervention_plan(zone_name):
    """Generate AI intervention plan for a zone."""
    row = df[df["Zone"] == zone_name]
    if row.empty:
        return jsonify({"error": "Zone not found"}), 404

    row = row.iloc[0]
    traffic = int(row["Traffic"])
    construction = int(row["Construction"])
    industry = int(row["Industry"])

    traffic_score = traffic * 0.4
    construction_score = construction * 0.3
    industry_score = industry * 0.3
    total = traffic_score + construction_score + industry_score

    traffic_percent = int((traffic_score / total) * 100)
    construction_percent = int((construction_score / total) * 100)
    industry_percent = int((industry_score / total) * 100)

    causes = []
    if traffic_percent > 30:
        causes.append("Traffic")
    if construction_percent > 25:
        causes.append("Construction")
    if industry_percent > 25:
        causes.append("Industry")

    all_actions = []
    if "Traffic" in causes:
        all_actions.append({"action": "Divert Traffic", "impact": "High Impact", "cost": "Low Cost", "reduction": 20})
    if "Construction" in causes:
        all_actions.append({"action": "Halt Construction", "impact": "Very High Impact", "cost": "High Resistance", "reduction": 25})
    if "Industry" in causes:
        all_actions.append({"action": "Inspect Industry", "impact": "Medium Impact", "cost": "Moderate Cost", "reduction": 15})

    selected_actions = all_actions[:2]
    skipped_actions = all_actions[2:]

    return jsonify({
        "causes": causes,
        "selected_actions": selected_actions,
        "skipped_actions": skipped_actions
    })


@app.route("/api/zone/<path:zone_name>/simulate", methods=["POST"])
def simulate_impact(zone_name):
    """Simulate AQI reduction based on selected actions."""
    row = df[df["Zone"] == zone_name]
    if row.empty:
        return jsonify({"error": "Zone not found"}), 404

    data = request.get_json()
    actions = data.get("actions", [])
    aqi = int(row.iloc[0]["AQI"])

    reduction = 0
    for action in actions:
        if action == "Divert Traffic":
            reduction += 20
        elif action == "Halt Construction":
            reduction += 25
        elif action == "Inspect Industry":
            reduction += 15

    new_aqi = max(aqi - reduction, 50)
    saturation = int((aqi / 500) * 100)

    return jsonify({
        "original_aqi": aqi,
        "new_aqi": new_aqi,
        "reduction": reduction,
        "saturation": saturation
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)
