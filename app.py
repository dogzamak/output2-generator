from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins=["https://dogzamak.github.io"], supports_credentials=True)

@app.route("/upload_raw_data", methods=["POST", "OPTIONS"])
def upload_raw_data():
    if request.method == "OPTIONS":
        return '', 200

    file = request.files.get("file")
    if file:
        return jsonify({"message": f"Received file: {file.filename}"}), 200
    return jsonify({"error": "No file uploaded"}), 400

@app.route("/", methods=["GET"])
def index():
    return "Backend is running and CORS enabled!"
