
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins=["https://dogzamak.github.io"], supports_credentials=True)

@app.route("/")
def index():
    return "Output2 Generator Backend"

@app.route("/upload_raw_data", methods=["POST", "OPTIONS"])
def upload_raw_data():
    if request.method == "OPTIONS":
        # Respond to preflight with allowed headers and methods
        response = app.make_response('')
        response.headers["Access-Control-Allow-Origin"] = "https://dogzamak.github.io"
        response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response

    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file uploaded"}), 400

    # Echo back filename for now
    return jsonify({"message": f"Received: {file.filename}"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
