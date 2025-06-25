
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import pandas as pd
import io

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

        unique_months = sorted(df["Month"].unique().tolist(), key=lambda x: pd.to_datetime(x, format="%b %Y"))
        categories2 = sorted(df["หมวดหมู่2"].dropna().unique().tolist())
        categories3 = sorted(df["หมวดหมู่3"].dropna().unique().tolist())

        return jsonify({
            "months": unique_months,
            "category2": categories2,
            "category3": categories3
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/generate_output2", methods=["POST"])
def generate_output2():
    file = request.files.get("rawFile")
    if not file:
        return jsonify({"error": "No file uploaded"}), 400

    try:
        df = pd.read_excel(file, sheet_name="Data")
        df["Created"] = pd.to_datetime(df["Created"], errors="coerce")
        df = df.dropna(subset=["Created"])
        df["Month"] = df["Created"].dt.strftime("%b %Y")

        selected_months = request.form.getlist("months[]")
        selected_cat2 = request.form.getlist("category2[]")
        selected_cat3 = request.form.getlist("category3[]")
        filter_type = request.form.get("filterType", "top5")

        if selected_months:
            df = df[df["Month"].isin(selected_months)]
        if selected_cat2:
            df = df[df["หมวดหมู่2"].isin(selected_cat2)]
        if selected_cat3:
            df = df[df["หมวดหมู่3"].isin(selected_cat3)]

        # Pivot Table
        pivot = df.groupby(["หมวดหมู่2", "หมวดหมู่3", "Month"]).size().unstack(fill_value=0)

        # จัดเรียงคอลัมน์เดือนเก่า → ใหม่
        pivot = pivot.reindex(sorted(pivot.columns, key=lambda x: pd.to_datetime(x, format="%b %Y")), axis=1)

        # คำนวณ Grand Total
        pivot["Grand Total"] = pivot.sum(axis=1)

        # ถ้าเลือก top5 → ตัดให้เหลือ 5 อันดับแรกต่อหมวดหมู่2
        if filter_type == "top5":
            pivot = (
                pivot.sort_values("Grand Total", ascending=False)
                .groupby("หมวดหมู่2", group_keys=False)
                .head(5)
            )

        # Reset Index
        pivot = pivot.reset_index()

        # ===== จัดลำดับหมวดหมู่2 ตามยอดเดือน "ใหม่ที่สุด" =====
        latest_month = max(selected_months, key=lambda x: pd.to_datetime(x, format="%b %Y"))
        group_total = df[df["Month"] == latest_month].groupby("หมวดหมู่2").size().sort_values(ascending=False)
        rank_map = {cat: i + 1 for i, cat in enumerate(group_total.index)}

        pivot["ลำดับ"] = pivot["หมวดหมู่2"].map(rank_map)
        pivot = pivot.sort_values(["ลำดับ", "Grand Total"], ascending=[True, False])

        # จัดลำดับคอลัมน์
        ordered_cols = ["ลำดับ", "หมวดหมู่2", "หมวดหมู่3"] + list(pivot.columns.difference(["ลำดับ", "หมวดหมู่2", "หมวดหมู่3", "Grand Total"], sort=False)) + ["Grand Total"]
        pivot = pivot[ordered_cols]

        # Export to Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            pivot.to_excel(writer, index=False, sheet_name="Output2")

        output.seek(0)
        return send_file(
            output,
            as_attachment=True,
            download_name="Output2.xlsx",
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
