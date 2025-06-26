
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import pandas as pd
import io

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route("/")
def index():
    return "Output2 Generator Backend is running with CORS enabled."

@app.route("/upload_raw_data", methods=["POST"])
def upload_raw_data():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    try:
        df = pd.read_excel(file, sheet_name=None)
        return jsonify({"message": "File uploaded and read successfully", "sheets": list(df.keys())})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/generate_output2", methods=["POST"])
def generate_output2():
    try:
        # In practice, replace this with actual logic to generate the file
        df = pd.DataFrame({
            'ลำดับ': [1, 2],
            'หมวดหมู่2': ['HRIS', 'WORKFLOW'],
            'หมวดหมู่3': ['เข้าสู่ระบบไม่ได้', 'ตั้งค่าโปรแกรม'],
            'Grand Total': [123, 99]
        })
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Output2')
        output.seek(0)
        return send_file(output, download_name="Output2.xlsx", as_attachment=True)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
