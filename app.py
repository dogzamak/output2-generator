
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import pandas as pd
import io
import datetime

app = Flask(__name__)
CORS(app)

@app.route("/")
def index():
    return "✅ Output2 API is running."

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
        months = sorted(df["Month"].dropna().unique().tolist())
        category2 = sorted(df["หมวดหมู่2"].dropna().unique().tolist())
        category3 = sorted(df["หมวดหมู่3"].dropna().unique().tolist())
        status = sorted(df.iloc[:, 8].dropna().unique().tolist())  # คอลัมน์ I
        process_status = sorted(df.iloc[:, 9].dropna().unique().tolist())  # คอลัมน์ J

        return jsonify({
            "months": months,
            "category2": category2,
            "category3": category3,
            "status": status,
            "process_status": process_status
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/generate_output2", methods=["POST"])
def generate_output2():
    try:
        file = request.files.get("rawFile")
        if not file:
            return jsonify({"error": "No file uploaded"}), 400

        df = pd.read_excel(file, sheet_name="Data")
        df["Created"] = pd.to_datetime(df["Created"], errors="coerce")
        df = df.dropna(subset=["Created"])
        df["Month"] = df["Created"].dt.strftime("%b %Y")

        selected_months = request.form.getlist("months[]")
        selected_c2 = request.form.getlist("category2[]")
        selected_c3 = request.form.getlist("category3[]")
        selected_status = request.form.getlist("status[]")
        selected_process = request.form.getlist("processStatus[]")
        filter_type = request.form.get("filterType", "top5")

        df = df[df["Month"].isin(selected_months)]
        if selected_c2:
            df = df[df["หมวดหมู่2"].str.lower().isin([x.lower() for x in selected_c2])]
        if selected_c3:
            df = df[df["หมวดหมู่3"].str.lower().isin([x.lower() for x in selected_c3])]
        if selected_status:
            df = df[df.iloc[:, 8].astype(str).isin(selected_status)]
        if selected_process:
            df = df[df.iloc[:, 9].astype(str).isin(selected_process)]

        group = df.groupby(["หมวดหมู่2", "หมวดหมู่3", "Month"]).size().reset_index(name="Ticket")
        pivot = group.pivot_table(index=["หมวดหมู่2", "หมวดหมู่3"], columns="Month", values="Ticket", fill_value=0)
        pivot["Grand Total"] = pivot.sum(axis=1)
        pivot = pivot.reset_index()

        # Apply Top 5 per category2
        if filter_type == "top5":
            pivot["Rank"] = pivot.groupby("หมวดหมู่2")["Grand Total"].rank(method="first", ascending=False)
            pivot = pivot[pivot["Rank"] <= 5]
            pivot = pivot.drop(columns=["Rank"])

        # Add index based on Grand Total of category2
        c2_total = pivot.groupby("หมวดหมู่2")["Grand Total"].sum().reset_index(name="DEBUG_Total_หมวดหมู่2")
        c2_total = c2_total.sort_values(by="DEBUG_Total_หมวดหมู่2", ascending=False).reset_index(drop=True)
        c2_total["ลำดับ"] = c2_total.index + 1
        df_final = pivot.merge(c2_total, on="หมวดหมู่2", how="left")

        # จัดลำดับคอลัมน์
        columns = ["ลำดับ", "หมวดหมู่2", "หมวดหมู่3"] + sorted([c for c in df_final.columns if c not in ["ลำดับ", "หมวดหมู่2", "หมวดหมู่3", "Grand Total", "DEBUG_Total_หมวดหมู่2"]]) + ["Grand Total", "DEBUG_Total_หมวดหมู่2"]
        df_final = df_final[columns]

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df_final.to_excel(writer, index=False, sheet_name="Output2")
        output.seek(0)

        return send_file(
            output,
            download_name="Output2.xlsx",
            as_attachment=True,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
