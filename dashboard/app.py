import os
import pandas as pd
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

file_counter = 1
while os.path.exists(f"annealing/result_log/results{file_counter}.txt"):
    file_counter += 1
CSV_PATH = f"annealing/progress_logs/annealing_progress{file_counter}.csv"

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
    expected = ["iteration", "elapsed_seconds", "temperature", "current_cost", "best_cost", "accepted"]
    for col in expected:
        if col not in df.columns:
            df[col] = None

    # Compute rolling acceptance rate (window)
    df["accepted"] = pd.to_numeric(df["accepted"], errors="coerce").fillna(0).astype(int)
    df["acceptance_rate_200"] = df["accepted"].rolling(200, min_periods=1).mean()

    return df

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

    # Convert to plain lists for Chart.js
    out = {
        "ok": True,
        "rows": {
            "iteration": df["iteration"].tolist(),
            "elapsed_seconds": df["elapsed_seconds"].tolist(),
            "temperature": df["temperature"].tolist(),
            "current_cost": df["current_cost"].tolist(),
            "best_cost": df["best_cost"].tolist(),
            "accepted": df["accepted"].tolist(),
            "acceptance_rate_200": df["acceptance_rate_200"].tolist(),
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
    overall_acceptance = float(df["accepted"].mean()) if df.shape[0] else 0.0

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

if __name__ == "__main__":
    # Bind to 0.0.0.0 only if you understand the security implications.
    app.run(host="127.0.0.1", port=8000, debug=False)