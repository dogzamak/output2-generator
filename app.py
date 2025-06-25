
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import pandas as pd
from io import BytesIO

app = Flask(__name__)
CORS(app)

@app.route("/generate_output2", methods=["POST"])
def generate_output2():
    try:
        file = request.files.get("rawFile")
        selected_months = request.form.getlist("months[]")
        category2_filter = request.form.getlist("category2[]")
        category3_filter = request.form.getlist("category3[]")
        show_top5_only = request.form.get("topOnly") == "true"

        if not file:
            return "No file uploaded", 400

        df = pd.read_excel(file, sheet_name="Data")
        df["Created"] = pd.to_datetime(df["Created"], errors="coerce")
        df = df.dropna(subset=["Created"])
        df["Month"] = df["Created"].dt.strftime("%b %Y")

        if selected_months:
            df = df[df["Month"].isin(selected_months)]
        if category2_filter:
            df = df[df["หมวดหมู่2"].isin(category2_filter)]
        if category3_filter:
            df = df[df["หมวดหมู่3"].isin(category3_filter)]

        grouped = df.groupby(["หมวดหมู่2", "หมวดหมู่3", "Month"]).size().unstack(fill_value=0)
        for m in selected_months:
            if m not in grouped.columns:
                grouped[m] = 0
        grouped = grouped[selected_months]
        grouped["Grand Total"] = grouped.sum(axis=1)

        if show_top5_only:
            top5 = grouped.groupby("หมวดหมู่2")["Grand Total"].sum().nlargest(5).index
            grouped = grouped.loc[grouped.index.get_level_values("หมวดหมู่2").isin(top5)]

        grand_total_per_cat2 = grouped.groupby(level="หมวดหมู่2")["Grand Total"].sum()
        cat2_order = grand_total_per_cat2.sort_values(ascending=False).index.tolist()

        grouped = grouped.reset_index()
        grouped["DEBUG_Total_หมวดหมู่2"] = grouped["หมวดหมู่2"].map(grand_total_per_cat2)
        grouped["ลำดับ"] = grouped["หมวดหมู่2"].map(lambda x: cat2_order.index(x) + 1)
        grouped = grouped.sort_values(by=["ลำดับ", "หมวดหมู่2", "หมวดหมู่3"])

        columns = ["ลำดับ", "หมวดหมู่2", "หมวดหมู่3"] + selected_months + ["Grand Total"]
        if "DEBUG_Total_หมวดหมู่2" in grouped.columns:
            columns.append("DEBUG_Total_หมวดหมู่2")

        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            grouped.to_excel(writer, index=False, sheet_name="Output2", columns=columns)
        output.seek(0)

        return send_file(output, as_attachment=True, download_name="Output2.xlsx", mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route("/")
def index():
    return "✅ Output2 Backend API is running."

if __name__ == "__main__":
    app.run(debug=True)
