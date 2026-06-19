from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import threading
import time

CONFIG_PATH = "config.json"

app = Flask(__name__)
CORS(app)

config_lock = threading.Lock()


def load_config():
    with config_lock:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)


def save_config(data):
    with config_lock:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)


# ─────────────────────────────────────────────
# TIME
# ─────────────────────────────────────────────

@app.route("/getDate", methods=["GET"])
def get_date():
    return str(int(time.time())), 200, {"Content-Type": "text/plain"}


# ─────────────────────────────────────────────
# STATES (light)
# ─────────────────────────────────────────────

@app.route("/states", methods=["GET"])
def get_states():
    config = load_config()

    return jsonify({
        "GlobalState": config["GlobalState"],
        "Valves": [
            {
                "Id": v["Id"],
                "State": v["State"],
                "OverrideState": v["OverrideState"]
            }
            for v in config["Valves"]
        ]
    })


# ─────────────────────────────────────────────
# OVERRIDE ONLY
# ─────────────────────────────────────────────

@app.route("/override", methods=["POST"])
def update_override():
    data = request.get_json()

    valve_id = data.get("Id")
    override_state = data.get("OverrideState")

    if valve_id is None or override_state is None:
        return jsonify({"status": "error"}), 400

    config = load_config()

    for v in config["Valves"]:
        if v["Id"] == valve_id:
            v["OverrideState"] = bool(override_state)
            save_config(config)
            return jsonify({"status": "ok", "updated": valve_id})

    return jsonify({"status": "error", "message": "not found"}), 404


# ─────────────────────────────────────────────
# SAVE FULL CONFIG (NO Pin, NO State, NO OverrideState)
# ─────────────────────────────────────────────

@app.route("/update", methods=["POST"])
def update_config():
    """
    {
      "GlobalState": true,
      "Valves": [
        {
          "Id": "Valvola 1",
          "TimeStart": "06:00",
          "Duration": 15
        }
      ]
    }
    """

    data = request.get_json()

    if not data:
        return jsonify({"status": "error"}), 400

    config = load_config()

    # GlobalState update (solo qui)
    if "GlobalState" in data:
        config["GlobalState"] = bool(data["GlobalState"])

    incoming_valves = data.get("Valves", [])

    updated = []

    for incoming in incoming_valves:
        valve_id = incoming.get("Id")

        for v in config["Valves"]:
            if v["Id"] != valve_id:
                continue

            if "TimeStart" in incoming:
                v["TimeStart"] = incoming["TimeStart"]

            if "Duration" in incoming:
                v["Duration"] = int(incoming["Duration"])

            updated.append(valve_id)
            break

    save_config(config)

    return jsonify({
        "status": "ok",
        "updated": updated
    })
# ─────────────────────────────────────────────
# UPDATE STATES (SOLO RUNTIME)
# ─────────────────────────────────────────────

@app.route("/updatestates", methods=["POST"])
def update_states():
    """
    {
      "GlobalState": true,
      "Valves": [
        { "State": true },
        { "State": false }
      ]
    }
    """

    data = request.get_json()

    if not data:
        return jsonify({
            "status": "error",
            "message": "missing body"
        }), 400

    incoming = data.get("Valves")

    if incoming is None:
        return jsonify({
            "status": "error",
            "message": "Valves missing"
        }), 400

    config = load_config()

    changed = False

    for i, v_in in enumerate(incoming):
        if i >= len(config["Valves"]):
            break

        new_state = bool(v_in.get("State", False))

        if config["Valves"][i]["State"] != new_state:
            config["Valves"][i]["State"] = new_state
            changed = True

    if "GlobalState" in data:
        config["GlobalState"] = bool(data["GlobalState"])

    if changed:
        save_config(config)

    return jsonify({
        "status": "ok",
        "changed": changed
    })
# ─────────────────────────────────────────────
# PROGRAMMAZIONE COMPLETA (SOLO SCHEDULING)
# ─────────────────────────────────────────────

@app.route("/program", methods=["GET"])
def get_program():
    config = load_config()

    return jsonify({
        "GlobalState": config["GlobalState"],
        "Valves": [
            {
                "Id": v["Id"],
                "TimeStart": v.get("TimeStart"),
                "Duration": v.get("Duration")
            }
            for v in config["Valves"]
        ]
    })

@app.route("/overridestates", methods=["GET"])
def get_override():
    config = load_config()

    return jsonify({
        "GlobalState": config["GlobalState"],
        "Valves": [
            {
                "Id": v["Id"],
                "OverrideState": v.get("OverrideState")
            }
            for v in config["Valves"]
        ]
    })
# ─────────────────────────────────────────────
# START
# ─────────────────────────────────────────────

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        threaded=True
    )