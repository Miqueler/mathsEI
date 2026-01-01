import ast
import json
import os
import re
import pandas as pd
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

file_counter = 1
while os.path.exists(f"annealing/result_log/results{file_counter}.txt"):
    file_counter += 1
CSV_PATH = f"annealing/progress_logs/annealing_progress{file_counter}.csv"
RESULTS_DIR = "annealing/result_log"
LIVE_LAYOUT_PATH = "annealing/progress_logs/current_best_layout.json"

def get_latest_results_path():
    if not os.path.isdir(RESULTS_DIR):
        return None
    latest_num = -1
    latest_path = None
    for name in os.listdir(RESULTS_DIR):
        match = re.fullmatch(r"results(\d+)\.txt", name)
        if not match:
            continue
        num = int(match.group(1))
        if num > latest_num:
            latest_num = num
            latest_path = os.path.join(RESULTS_DIR, name)
    return latest_path

def load_data(max_rows=5000):
    if not os.path.isfile(CSV_PATH):
        return None

    # Read CSV; handle header-only gracefully
    try:
        df = pd.read_csv(CSV_PATH)
    except Exception:
        return None

    if df.shape[0] == 0:
        return df

    # Keep last max_rows
    if df.shape[0] > max_rows:
        df = df.iloc[-max_rows:].copy()

    # Ensure expected columns exist
    expected = [
        "iteration",
        "elapsed_seconds",
        "temperature",
        "current_cost",
        "best_cost",
        "acceptance_ratio",
        "digraph_cost",
        "single_letter_cost",
    ]
    for col in expected:
        if col not in df.columns:
            df[col] = None

    # Compute rolling acceptance rate (window)
    df["acceptance_ratio"] = pd.to_numeric(df["acceptance_ratio"], errors="coerce").fillna(0.0)
    df["acceptance_rate_200"] = df["acceptance_ratio"].rolling(200, min_periods=1).mean()
    df["cost_gap"] = pd.to_numeric(df["current_cost"], errors="coerce") - pd.to_numeric(df["best_cost"], errors="coerce")
    df["digraph_cost"] = pd.to_numeric(df["digraph_cost"], errors="coerce")
    df["single_letter_cost"] = pd.to_numeric(df["single_letter_cost"], errors="coerce")
    digraph_weight = 1.0
    single_letter_weight = 0.1
    df["digraph_cost_weighted"] = df["digraph_cost"] * digraph_weight
    df["single_letter_cost_weighted"] = df["single_letter_cost"] * single_letter_weight

    return df

def load_keyboard_layout():
    if os.path.isfile(LIVE_LAYOUT_PATH):
        try:
            with open(LIVE_LAYOUT_PATH, "r") as f:
                payload = json.load(f)
            layout = payload.get("layout")
            if isinstance(layout, dict):
                return layout
        except Exception:
            pass

    results_path = get_latest_results_path()
    if not results_path or not os.path.isfile(results_path):
        return None
    try:
        with open(results_path, "r") as f:
            first_line = f.readline().strip()
    except Exception:
        return None
    if not first_line:
        return None
    try:
        layout = ast.literal_eval(first_line)
    except Exception:
        return None
    if not isinstance(layout, dict):
        return None
    return layout

@app.route("/")
def index():
    return render_template("index.html", csv_path=CSV_PATH)

@app.route("/api/data")
def api_data():
    max_rows = int(request.args.get("max_rows", "2000"))
    df = load_data(max_rows=max_rows)
    if df is None:
        return jsonify({"ok": False, "error": f"Log file not found or unreadable: {CSV_PATH}"}), 404
    if df.shape[0] == 0:
        return jsonify({"ok": True, "rows": []})

    temp_group = (
        df.groupby("temperature", dropna=True)
        .agg(last_best=("best_cost", "last"),
             last_iter=("iteration", "last"))
        .reset_index()
        .sort_values("last_iter")
    )
    temp_group["prev_best"] = temp_group["last_best"].shift(1)
    temp_group["improvement"] = (temp_group["prev_best"] - temp_group["last_best"]).fillna(0.0)

    # Convert to plain lists for Chart.js
    out = {
        "ok": True,
        "rows": {
            "iteration": df["iteration"].tolist(),
            "elapsed_seconds": df["elapsed_seconds"].tolist(),
            "temperature": df["temperature"].tolist(),
            "current_cost": df["current_cost"].tolist(),
            "best_cost": df["best_cost"].tolist(),
            "acceptance_ratio": df["acceptance_ratio"].tolist(),
            "acceptance_rate_200": df["acceptance_rate_200"].tolist(),
            "cost_gap": df["cost_gap"].tolist(),
            "digraph_cost": df["digraph_cost"].tolist(),
            "single_letter_cost": df["single_letter_cost"].tolist(),
            "digraph_cost_weighted": df["digraph_cost_weighted"].tolist(),
            "single_letter_cost_weighted": df["single_letter_cost_weighted"].tolist(),
            "temp_improvement_iteration": temp_group["last_iter"].tolist(),
            "temp_improvement": temp_group["improvement"].fillna(0).tolist(),
        }
    }
    return jsonify(out)

@app.route("/api/summary")
def api_summary():
    df = load_data(max_rows=5000)
    if df is None:
        return jsonify({"ok": False, "error": f"Log file not found or unreadable: {CSV_PATH}"}), 404
    if df.shape[0] == 0:
        return jsonify({"ok": True, "summary": {"status": "header_only"}})

    last = df.iloc[-1]
    # Overall acceptance rate (over loaded window)
    overall_acceptance = float(df["acceptance_ratio"].mean()) if df.shape[0] else 0.0

    summary = {
        "status": "running",
        "rows": int(df.shape[0]),
        "iteration": int(last["iteration"]) if pd.notna(last["iteration"]) else None,
        "elapsed_seconds": float(last["elapsed_seconds"]) if pd.notna(last["elapsed_seconds"]) else None,
        "temperature": float(last["temperature"]) if pd.notna(last["temperature"]) else None,
        "current_cost": float(last["current_cost"]) if pd.notna(last["current_cost"]) else None,
        "best_cost": float(last["best_cost"]) if pd.notna(last["best_cost"]) else None,
        "overall_acceptance": overall_acceptance,
        "acceptance_rate_200": float(last["acceptance_rate_200"]) if pd.notna(last["acceptance_rate_200"]) else None,
    }
    return jsonify({"ok": True, "summary": summary})

@app.route("/api/keyboard")
def api_keyboard():
    layout = load_keyboard_layout()
    if layout is None:
        return jsonify({"ok": False, "error": "No results layout found."}), 404

    keys = []
    for letter, pos in layout.items():
        if not isinstance(pos, (list, tuple)) or len(pos) != 2:
            continue
        x, y = pos
        keys.append({"letter": letter, "x": float(x), "y": float(y)})

    return jsonify({"ok": True, "keys": keys})

if __name__ == "__main__":
    # Bind to 0.0.0.0 only if you understand the security implications.
    app.run(host="127.0.0.1", port=8000, debug=False)
