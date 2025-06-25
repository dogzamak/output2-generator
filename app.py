
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import pandas as pd
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
    selected_months = request.form.getlist("months[]")
    selected_category2 = request.form.getlist("category2[]")
    selected_category3 = request.form.getlist("category3[]")
    filter_top5 = request.form.get("filter") == "top5"

    try:
        df = pd.read_excel(file, sheet_name="Data")
        df["Created"] = pd.to_datetime(df["Created"], errors="coerce")
        df = df.dropna(subset=["Created"])
        df["Month"] = df["Created"].dt.strftime("%b %Y")

        if selected_months:
            df = df[df["Month"].isin(selected_months)]
        if selected_category2:
            df = df[df["หมวดหมู่2"].isin(selected_category2)]
        if selected_category3:
            df = df[df["หมวดหมู่3"].isin(selected_category3)]

        grouped = df.groupby(["หมวดหมู่2", "หมวดหมู่3", "Month"]).size().reset_index(name="Ticket")
        pivot = grouped.pivot_table(index=["หมวดหมู่2", "หมวดหมู่3"], columns="Month", values="Ticket", fill_value=0)
        pivot = pivot[[m for m in selected_months if m in pivot.columns]]

        pivot["Grand Total"] = pivot.sum(axis=1)
        pivot = pivot.reset_index()

        # คำนวณ Grand Total รวมต่อหมวดหมู่2 เพื่อใช้จัดลำดับ
        total_by_cat2 = pivot.groupby("หมวดหมู่2")["Grand Total"].sum().reset_index()
        total_by_cat2.columns = ["หมวดหมู่2", "DEBUG_Total_หมวดหมู่2"]

        pivot = pivot.merge(total_by_cat2, on="หมวดหมู่2", how="left")
        pivot = pivot.sort_values(by=["DEBUG_Total_หมวดหมู่2", "หมวดหมู่2", "หมวดหมู่3"], ascending=[False, True, True])

        # สร้างคอลัมน์ "ลำดับ"
        pivot["ลำดับ"] = pivot["หมวดหมู่2"].map(
            {cat2: i+1 for i, cat2 in enumerate(pivot["หมวดหมู่2"].drop_duplicates())}
        )

        # เรียงคอลัมน์ใหม่
        ordered_cols = ["ลำดับ", "หมวดหมู่2", "หมวดหมู่3"] + selected_months + ["Grand Total"]
        if "DEBUG_Total_หมวดหมู่2" in pivot.columns:
            ordered_cols += ["DEBUG_Total_หมวดหมู่2"]
        pivot = pivot[ordered_cols]

        if filter_top5:
            top5_ids = pivot["ลำดับ"].unique()[:5]
            pivot = pivot[pivot["ลำดับ"].isin(top5_ids)]

        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            pivot.to_excel(writer, sheet_name="Output2", index=False)
        output.seek(0)
        return send_file(output, as_attachment=True, download_name="Output2.xlsx", mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
