
from flask import Flask, request, send_file, jsonify
import pandas as pd
import io
from datetime import datetime

app = Flask(__name__)

@app.route('/extract_months_categories', methods=['POST'])
def extract_months_categories():
    file = request.files['rawFile']
    df = pd.read_excel(file, sheet_name="Data")

    df['Created'] = pd.to_datetime(df['Created'], errors='coerce')
    df = df.dropna(subset=['Created'])
    df['เดือน'] = df['Created'].dt.month.map({
        1: 'ม.ค.', 2: 'ก.พ.', 3: 'มี.ค.', 4: 'เม.ย.', 5: 'พ.ค.', 6: 'มิ.ย.',
        7: 'ก.ค.', 8: 'ส.ค.', 9: 'ก.ย.', 10: 'ต.ค.', 11: 'พ.ย.', 12: 'ธ.ค.'
    })
    df['ปี'] = df['Created'].dt.year + 543
    df['เดือนปี'] = df['เดือน'] + ' ' + df['ปี'].astype(str)

    unique_months = sorted(df['เดือนปี'].unique().tolist())
    cat2 = sorted(df['หมวดหมู่2'].dropna().unique().tolist())
    cat3 = sorted(df['หมวดหมู่3'].dropna().unique().tolist())

    return jsonify({
        "months": unique_months,
        "category2": cat2,
        "category3": cat3
    })

@app.route('/generate_output2', methods=['POST'])
def generate_output2():
    file = request.files['rawFile']
    months = request.form.getlist('months[]')
    cat2_filters = request.form.getlist('category2[]')
    cat3_filters = request.form.getlist('category3[]')
    filter_type = request.form.get('filterType', 'top5')

    df = pd.read_excel(file, sheet_name="Data")
    df['Created'] = pd.to_datetime(df['Created'], errors='coerce')
    df = df.dropna(subset=['Created'])

    df['เดือน'] = df['Created'].dt.month.map({
        1: 'ม.ค.', 2: 'ก.พ.', 3: 'มี.ค.', 4: 'เม.ย.', 5: 'พ.ค.', 6: 'มิ.ย.',
        7: 'ก.ค.', 8: 'ส.ค.', 9: 'ก.ย.', 10: 'ต.ค.', 11: 'พ.ย.', 12: 'ธ.ค.'
    })
    df['ปี'] = df['Created'].dt.year + 543
    df['เดือนปี'] = df['เดือน'] + ' ' + df['ปี'].astype(str)

    df = df[df['เดือนปี'].isin(months)]

    if cat2_filters:
        df = df[df['หมวดหมู่2'].isin(cat2_filters)]
    if cat3_filters:
        df = df[df['หมวดหมู่3'].isin(cat3_filters)]

    pivot = pd.pivot_table(df,
                           index=['หมวดหมู่2', 'หมวดหมู่3'],
                           columns='เดือนปี',
                           aggfunc='size', fill_value=0)

    pivot = pivot.reset_index()
    pivot['Grand Total'] = pivot[months].sum(axis=1)

    cat2_totals = pivot.groupby('หมวดหมู่2')['Grand Total'].sum().sort_values(ascending=False)
    cat2_order = {cat2: i+1 for i, cat2 in enumerate(cat2_totals.index)}
    pivot['ลำดับ'] = pivot['หมวดหมู่2'].map(cat2_order)

    pivot = pivot.sort_values(['ลำดับ', 'Grand Total'], ascending=[True, False])

    if filter_type == 'top5':
        top5_each = pivot.groupby('หมวดหมู่2').head(5)
        final = top5_each
    else:
        final = pivot

    final = final[['ลำดับ', 'หมวดหมู่2', 'หมวดหมู่3'] + months + ['Grand Total']]

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        final.to_excel(writer, index=False, sheet_name='Output2')
    output.seek(0)

    return send_file(output, as_attachment=True, download_name='Output2.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

if __name__ == '__main__':
    app.run(debug=True)
