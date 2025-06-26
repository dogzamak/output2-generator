
from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
from io import BytesIO

app = Flask(__name__)
CORS(app, origins=["https://dogzamak.github.io"])

@app.route("/upload_raw_data", methods=["POST"])
def upload_raw_data():
    try:
        file = request.files.get("file")
        if not file:
            return jsonify({"error": "No file uploaded"}), 400

        df = pd.read_excel(file, sheet_name="Data")
        df.columns = df.columns.str.strip()

        # แปลงวันที่
        df["Created"] = pd.to_datetime(df["Created"], errors="coerce")
        df = df.dropna(subset=["Created"])

        # เดือน + ปี
        df["Month"] = df["Created"].dt.strftime("%b %Y")
        unique_months = sorted(df["Month"].unique().tolist(), key=lambda x: pd.to_datetime(x, format="%b %Y"))

        # ตัวเลือก filter ต่าง ๆ
        category2 = sorted(df["หมวดหมู่2"].dropna().astype(str).str.strip().str.title().unique().tolist())
        category3 = sorted(df["หมวดหมู่3"].dropna().astype(str).str.strip().str.title().unique().tolist())
        status = sorted(df["สถานะ"].dropna().astype(str).str.strip().unique().tolist()) if "สถานะ" in df.columns else []
        status_process = sorted(df["สถานะ Process"].dropna().astype(str).str.strip().unique().tolist()) if "สถานะ Process" in df.columns else []

        return jsonify({
            "months": unique_months,
            "category2Options": category2,
            "category3Options": category3,
            "statusOptions": status,
            "processStatusOptions": status_process
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
