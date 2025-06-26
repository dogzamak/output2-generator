
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import pandas as pd
from io import BytesIO
import datetime

app = Flask(__name__)
CORS(app, origins=["https://dogzamak.github.io"])

@app.route("/")
def index():
    return "✅ Output2 Backend API is running."

@app.route("/upload_raw_data", methods=["POST"])
def upload_raw_data():
    try:
        file = request.files.get("file")
        if not file:
            return jsonify({"error": "No file uploaded"}), 400

        df = pd.read_excel(file, sheet_name="Data")
        df.columns = df.columns.str.strip()
        df["Created"] = pd.to_datetime(df["Created"], errors="coerce")
        df = df.dropna(subset=["Created"])

        df["Month"] = df["Created"].dt.strftime("%b %Y")
        unique_months = sorted(df["Month"].unique().tolist(), key=lambda x: pd.to_datetime(x, format="%b %Y"))

        category2 = sorted(df["หมวดหมู่2"].dropna().astype(str).str.strip().str.title().unique().tolist())
        category3 = sorted(df["หมวดหมู่3"].dropna().astype(str).str.strip().str.title().unique().tolist())
        status = sorted(df["สถานะ"].dropna().astype(str).str.strip().unique().tolist()) if "สถานะ" in df.columns else []
        process_status = sorted(df["สถานะ Process"].dropna().astype(str).str.strip().unique().tolist()) if "สถานะ Process" in df.columns else []

        return jsonify({
            "months": unique_months,
            "category2Options": category2,
            "category3Options": category3,
            "statusOptions": status,
            "processStatusOptions": process_status
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/generate_output2", methods=["POST"])
def generate_output2():
    try:
        file = request.files.get("file")
        if not file:
            return jsonify({"error": "No file uploaded"}), 400

        selected_months = request.form.getlist("months[]")
        selected_cat2 = [c.lower() for c in request.form.getlist("category2[]")]
        selected_cat3 = [c.lower() for c in request.form.getlist("category3[]")]
        selected_status = request.form.getlist("status[]")
        selected_process = request.form.getlist("processStatus[]")
        top5_mode = request.form.get("top5", "false").lower() == "true"

        df = pd.read_excel(file, sheet_name="Data")
        df.columns = df.columns.str.strip()
        df["Created"] = pd.to_datetime(df["Created"], errors="coerce")
        df = df.dropna(subset=["Created"])
        df["Month"] = df["Created"].dt.strftime("%b %Y")

        # Filter
        df["หมวดหมู่2"] = df["หมวดหมู่2"].astype(str).str.lower().str.strip()
        df["หมวดหมู่3"] = df["หมวดหมู่3"].astype(str).str.lower().str.strip()
        if selected_cat2:
            df = df[df["หมวดหมู่2"].isin(selected_cat2)]
        if selected_cat3:
            df = df[df["หมวดหมู่3"].isin(selected_cat3)]
        if selected_status:
            df = df[df["สถานะ"].isin(selected_status)]
        if selected_process:
            df = df[df["สถานะ Process"].isin(selected_process)]
        if selected_months:
            df = df[df["Month"].isin(selected_months)]

        # Group
        pivot = df.pivot_table(index=["หมวดหมู่2", "หมวดหมู่3"], columns="Month", aggfunc="size", fill_value=0).reset_index()
        month_cols = [m for m in selected_months if m in pivot.columns]
        pivot["Grand Total"] = pivot[month_cols].sum(axis=1)
        pivot = pivot[["หมวดหมู่2", "หมวดหมู่3"] + month_cols + ["Grand Total"]]

        # สร้างคอลัมน์ A ลำดับหมวดหมู่2 ตาม Grand Total รวม
        group_total = pivot.groupby("หมวดหมู่2")["Grand Total"].sum().reset_index()
        group_total = group_total.sort_values("Grand Total", ascending=False).reset_index(drop=True)
        group_total["ลำดับ"] = group_total.index + 1

        result = pivot.merge(group_total, on="หมวดหมู่2")
        result = result.sort_values(by=["ลำดับ", "Grand Total"], ascending=[True, False])

        if top5_mode:
            result = result.groupby("หมวดหมู่2").head(5)

        result = result[["ลำดับ", "หมวดหมู่2", "หมวดหมู่3"] + month_cols + ["Grand Total"]]

        # สร้างไฟล์ Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            result.to_excel(writer, index=False, sheet_name="Output2")
        output.seek(0)

        filename = f"Output2_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        return send_file(output, as_attachment=True, download_name=filename, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
