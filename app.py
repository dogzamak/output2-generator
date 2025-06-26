from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import pandas as pd
import io
import datetime

app = Flask(__name__)
CORS(app)

@app.route("/")
def index():
    return "✅ Output2 API is running."

@app.route("/generate_output2", methods=["POST"])
def generate_output2():
    try:
        file = request.files['rawFile']
        selected_months = request.form.getlist('selectedMonths[]')
        selected_category2 = request.form.getlist('selectedCategory2[]')
        selected_category3 = request.form.getlist('selectedCategory3[]')
        selected_status = request.form.getlist('selectedStatus[]')
        selected_status_process = request.form.getlist('selectedStatusProcess[]')
        show_top5_only = request.form.get('showTop5Only') == 'true'

        df = pd.read_excel(file, sheet_name='Data')
        df["Created"] = pd.to_datetime(df["Created"], errors='coerce')
        df = df.dropna(subset=["Created"])
        df["Month"] = df["Created"].dt.strftime("%b %Y")

        for col in ["หมวดหมู่2", "หมวดหมู่3", "สถานะ", "สถานะ Process"]:
            df[col] = df[col].astype(str).str.strip().str.lower()

        if selected_months:
            df = df[df["Month"].isin([m.lower() for m in map(str.lower, selected_months)])]
        if selected_category2:
            df = df[df["หมวดหมู่2"].isin([c.lower() for c in selected_category2])]
        if selected_category3:
            df = df[df["หมวดหมู่3"].isin([c.lower() for c in selected_category3])]
        if selected_status:
            df = df[df["สถานะ"].isin([s.lower() for s in selected_status])]
        if selected_status_process:
            df = df[df["สถานะ Process"].isin([s.lower() for s in selected_status_process])]

        pivot = df.pivot_table(index=["หมวดหมู่2", "หมวดหมู่3"],
                               columns="Month", aggfunc="size", fill_value=0).reset_index()

        pivot.columns.name = None
        pivot["Grand Total"] = pivot.loc[:, pivot.columns[2:]].sum(axis=1)

        category2_total = pivot.groupby("หมวดหมู่2")["Grand Total"].transform("sum")
        pivot["DEBUG_Total_หมวดหมู่2"] = category2_total

        if show_top5_only:
            top_rows = (
                pivot.sort_values("Grand Total", ascending=False)
                .groupby("หมวดหมู่2", group_keys=False)
                .head(5)
            )
            pivot = top_rows.copy()

        pivot = pivot.sort_values(by=["DEBUG_Total_หมวดหมู่2", "หมวดหมู่2", "Grand Total"],
                                  ascending=[False, True, False])
        pivot.insert(0, "ลำดับ", pivot.groupby("หมวดหมู่2", sort=False).ngroup() + 1)

        ordered_months = sorted([m for m in pivot.columns if m not in ["หมวดหมู่2", "หมวดหมู่3", "Grand Total", "DEBUG_Total_หมวดหมู่2", "ลำดับ"]],
                                key=lambda x: datetime.datetime.strptime(x, "%b %Y"))
        final_cols = ["ลำดับ", "หมวดหมู่2", "หมวดหมู่3"] + ordered_months + ["Grand Total", "DEBUG_Total_หมวดหมู่2"]
        pivot = pivot[final_cols]

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            pivot.to_excel(writer, index=False, sheet_name="Output2")
        output.seek(0)

        return send_file(output, download_name="Output2.xlsx", as_attachment=True)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)