
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import pandas as pd
import os
from io import BytesIO

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

        categories2 = sorted(df["หมวดหมู่2"].dropna().unique().tolist(), key=lambda x: str(x).lower())
        categories3 = sorted(df["หมวดหมู่3"].dropna().unique().tolist(), key=lambda x: str(x).lower())
        statuses = sorted(df["สถานะ"].dropna().unique().tolist())
        status_processes = sorted(df["สถานะ Process"].dropna().unique().tolist())

        return jsonify({
            "months": unique_months,
            "category2": categories2,
            "category3": categories3,
            "status": statuses,
            "status_process": status_processes
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/generate_output2", methods=["POST"])
def generate_output2():
    try:
        file = request.files.get("rawFile")
        selected_months = request.form.getlist("months[]")
        selected_cat2 = request.form.getlist("category2[]")
        selected_cat3 = request.form.getlist("category3[]")
        selected_status = request.form.getlist("status[]")
        selected_status_process = request.form.getlist("status_process[]")
        top5_only = request.form.get("top5") == "true"

        df = pd.read_excel(file, sheet_name="Data")
        df["Created"] = pd.to_datetime(df["Created"], errors="coerce")
        df = df.dropna(subset=["Created"])
        df["Month"] = df["Created"].dt.strftime("%b %Y")

        df["หมวดหมู่2"] = df["หมวดหมู่2"].astype(str).str.lower()
        df["หมวดหมู่3"] = df["หมวดหมู่3"].astype(str).str.lower()

        if selected_cat2:
            selected_cat2 = [x.lower() for x in selected_cat2]
            df = df[df["หมวดหมู่2"].str.lower().isin(selected_cat2)]

        if selected_cat3:
            selected_cat3 = [x.lower() for x in selected_cat3]
            df = df[df["หมวดหมู่3"].str.lower().isin(selected_cat3)]

        if selected_status:
            df = df[df["สถานะ"].isin(selected_status)]

        if selected_status_process:
            df = df[df["สถานะ Process"].isin(selected_status_process)]

        df = df[df["Month"].isin(selected_months)]

        grouped = df.groupby(["หมวดหมู่2", "หมวดหมู่3", "Month"]).size().unstack(fill_value=0)
        grouped["Grand Total"] = grouped.sum(axis=1)

        grand_total_per_cat2 = grouped.groupby(level=0)["Grand Total"].sum()
        grouped["DEBUG_Total_หมวดหมู่2"] = grouped.index.get_level_values(0).map(grand_total_per_cat2)

        if top5_only:
            top5 = grouped.groupby(level=1)["Grand Total"].sum().nlargest(5).index
            grouped = grouped[grouped.index.get_level_values(1).isin(top5)]

        grouped = grouped.sort_values(by="DEBUG_Total_หมวดหมู่2", ascending=False)
        grouped = grouped.reset_index()

        grouped["ลำดับ"] = grouped["หมวดหมู่2"].map(
            {k: i+1 for i, k in enumerate(grouped.groupby("หมวดหมู่2")["DEBUG_Total_หมวดหมู่2"].first().sort_values(ascending=False).index)}
        )

        columns_order = ["ลำดับ", "หมวดหมู่2", "หมวดหมู่3"] + sorted(selected_months, key=lambda x: pd.to_datetime(x)) + ["Grand Total", "DEBUG_Total_หมวดหมู่2"]
        result = grouped[columns_order]

        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            result.to_excel(writer, index=False, sheet_name="Output2")
        output.seek(0)

        return send_file(output, as_attachment=True, download_name="Output2.xlsx", mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
