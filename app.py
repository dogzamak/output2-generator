from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import pandas as pd
from io import BytesIO

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # อนุญาตทุก origin (หรือระบุ origin ที่เฉพาะเจาะจง)

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

        # แปลงวันที่จากคอลัมน์ Created
        df["Created"] = pd.to_datetime(df["Created"], errors="coerce")
        df = df.dropna(subset=["Created"])
        df["Month"] = df["Created"].dt.strftime("%b %Y")

        unique_months = sorted(df["Month"].unique().tolist())
        category2 = sorted(df["หมวดหมู่2"].dropna().unique().tolist())
        category3 = sorted(df["หมวดหมู่3"].dropna().unique().tolist())
        status_list = sorted(df["สถานะ"].dropna().unique().tolist())
        process_status = sorted(df["สถานะ Process"].dropna().unique().tolist())

        return jsonify({
            "months": unique_months,
            "category2": category2,
            "category3": category3,
            "status": status_list,
            "processStatus": process_status
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# เพิ่ม endpoint ทดสอบดาวน์โหลด (จำลอง)
@app.route("/test_download", methods=["GET"])
def test_download():
    output = BytesIO()
    df = pd.DataFrame({"A": [1, 2], "B": [3, 4]})
    df.to_excel(output, index=False)
    output.seek(0)
    return send_file(output, download_name="test_output.xlsx", as_attachment=True)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
