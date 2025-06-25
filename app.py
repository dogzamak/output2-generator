
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import pandas as pd

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

        # แปลงวันที่จากคอลัมน์ Created (สมมติว่าอยู่ในคอลัมน์ 'Created')
        df["Created"] = pd.to_datetime(df["Created"], errors="coerce")
        df = df.dropna(subset=["Created"])

        # ดึงเดือน+ปี
        df["Month"] = df["Created"].dt.strftime("%b %Y")  # เช่น "Mar 2025"
        unique_months = sorted(df["Month"].unique().tolist())

        # หมวดหมู่
        categories2 = sorted(df["หมวดหมู่2"].dropna().unique().tolist())
        categories3 = sorted(df["หมวดหมู่3"].dropna().unique().tolist())

        return jsonify({
            "months": unique_months,
            "category2": categories2,
            "category3": categories3
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
