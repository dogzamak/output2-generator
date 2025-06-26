
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import pandas as pd
import io

app = Flask(__name__)
CORS(app, origins=["https://dogzamak.github.io"], supports_credentials=True)

@app.route('/')
def home():
    return 'Backend is running with CORS enabled for https://dogzamak.github.io'

@app.route('/upload_raw_data', methods=['POST'])
def upload_raw_data():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    try:
        df = pd.read_excel(file)
        cols = df.columns.tolist()
        return jsonify({'columns': cols})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download_sample_output2', methods=['GET'])
def download_sample_output2():
    output = io.BytesIO()
    df = pd.DataFrame({
        'ลำดับ': [1, 2],
        'หมวดหมู่2': ['HRIS', 'WORKFLOW'],
        'หมวดหมู่3': ['Login เข้าไม่ได้', 'ติดตั้งโปรแกรม'],
        'Mar 2025': [16, 60],
        'Apr 2025': [31, 54],
        'May 2025': [11, 43],
        'Grand Total': [58, 157],
    })
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Output2')
    output.seek(0)
    return send_file(output, download_name='Output2.xlsx', as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
