
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import pandas as pd
import io

app = Flask(__name__)
CORS(app)

@app.route("/")
def index():
    return "✅ Output2 Generator API is running."

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

        months = sorted(df["Month"].dropna().unique().tolist(), key=lambda x: pd.to_datetime(x))
        category2 = sorted(df["หมวดหมู่2"].dropna().unique().tolist(), key=str.lower)
        category3 = sorted(df["หมวดหมู่3"].dropna().unique().tolist(), key=str.lower)
        status = sorted(df["สถานะ"].dropna().unique().tolist())
        process_status = sorted(df["สถานะ Process"].dropna().unique().tolist())

        return jsonify({
            "months": months,
            "category2": category2,
            "category3": category3,
            "status": status,
            "processStatus": process_status
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/generate_output2", methods=["POST"])
def generate_output2():
    try:
        file = request.files.get("file")
        payload = request.form.to_dict(flat=False)

        months = payload.get("months[]", [])
        category2 = payload.get("category2[]", [])
        category3 = payload.get("category3[]", [])
        status = payload.get("status[]", [])
        process_status = payload.get("processStatus[]", [])
        top5_only = payload.get("top5Only", ["false"])[0].lower() == "true"

        df = pd.read_excel(file, sheet_name="Data")
        df["Created"] = pd.to_datetime(df["Created"], errors="coerce")
        df = df.dropna(subset=["Created"])
        df["Month"] = df["Created"].dt.strftime("%b %Y")

        df = df[df["Month"].isin(months)]
        if category2:
            df = df[df["หมวดหมู่2"].str.lower().isin([c.lower() for c in category2])]
        if category3:
            df = df[df["หมวดหมู่3"].str.lower().isin([c.lower() for c in category3])]
        if status:
            df = df[df["สถานะ"].isin(status)]
        if process_status:
            df = df[df["สถานะ Process"].isin(process_status)]

        pivot = pd.pivot_table(df, index=["หมวดหมู่2", "หมวดหมู่3"], columns="Month", aggfunc="size", fill_value=0)
        pivot["Grand Total"] = pivot.sum(axis=1)
        pivot = pivot.reset_index()

        # จัดลำดับหมวดหมู่2 โดยใช้ Grand Total รวมของหมวดหมู่2
        sum_by_cat2 = pivot.groupby("หมวดหมู่2")["Grand Total"].sum().sort_values(ascending=False)
        cat2_order = {cat: i+1 for i, cat in enumerate(sum_by_cat2.index)}
        pivot["ลำดับ"] = pivot["หมวดหมู่2"].map(cat2_order)

        # เรียงคอลัมน์เดือนจากเก่าไปใหม่
        month_order = sorted([col for col in pivot.columns if col not in ["ลำดับ", "หมวดหมู่2", "หมวดหมู่3", "Grand Total"]], key=lambda x: pd.to_datetime(x))
        cols = ["ลำดับ", "หมวดหมู่2", "หมวดหมู่3"] + month_order + ["Grand Total"]
        pivot = pivot[cols]

        # แสดงเฉพาะ Top 5 หมวดหมู่3 ต่อหมวดหมู่2
        if top5_only:
            pivot = pivot.sort_values(by=["ลำดับ", "Grand Total"], ascending=[True, False])
            top5 = pivot.groupby("หมวดหมู่2").head(5)
            pivot = top5

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            pivot.to_excel(writer, sheet_name="Output2", index=False)
        output.seek(0)

        return send_file(output, download_name="Output2.xlsx", as_attachment=True)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
