
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import pandas as pd
import io

app = Flask(__name__)
CORS(app)

@app.route("/")
def index():
    return "✅ Output2 Backend API is running."

@app.route("/extract_months_categories", methods=["POST"])
def extract_data():
    file = request.files.get("rawFile")
    if not file:
        return jsonify({"error": "No file uploaded"}), 400

    try:
        df = pd.read_excel(file, sheet_name="Data")

        df["Created"] = pd.to_datetime(df["Created"], errors="coerce")
        df = df.dropna(subset=["Created"])
        df["Month"] = df["Created"].dt.strftime("%b %Y")
        unique_months = sorted(df["Month"].unique().tolist())

        # Make category2 and category3 case-insensitive unique values
        category2 = sorted(df["หมวดหมู่2"].dropna().astype(str).str.lower().str.strip().unique().tolist())
        category3 = sorted(df["หมวดหมู่3"].dropna().astype(str).str.lower().str.strip().unique().tolist())

        # Extract filters from column I and J
        status_list = sorted(df.iloc[:, 8].dropna().astype(str).unique().tolist())
        process_list = sorted(df.iloc[:, 9].dropna().astype(str).unique().tolist())

        return jsonify({
            "months": unique_months,
            "category2": category2,
            "category3": category3,
            "status": status_list,
            "process_status": process_list
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
