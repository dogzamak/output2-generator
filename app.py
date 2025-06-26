
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
import pandas as pd
import io

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/upload_raw_data")
async def upload_raw_data(rawFile: UploadFile = File(...)):
    try:
        contents = await rawFile.read()
        df = pd.read_excel(io.BytesIO(contents), sheet_name="Data")

        category2 = sorted(df["หมวดหมู่2"].dropna().astype(str).str.strip().unique().tolist())
        category3 = sorted(df["หมวดหมู่3"].dropna().astype(str).str.strip().unique().tolist())
        status = sorted(df["สถานะ"].dropna().astype(str).str.strip().unique().tolist())
        status_process = sorted(df["สถานะ Process"].dropna().astype(str).str.strip().unique().tolist())

        return JSONResponse(content={
            "category2": category2,
            "category3": category3,
            "status": status,
            "status_process": status_process
        })
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=400)


@app.post("/generate_output2")
async def generate_output2(
    rawFile: UploadFile = File(...),
    months: str = Form(...),
    category2: str = Form(...),
    category3: str = Form(...),
    status: str = Form(...),
    status_process: str = Form(...),
    top5: bool = Form(...),
):
    try:
        contents = await rawFile.read()
        df = pd.read_excel(io.BytesIO(contents), sheet_name="Data")

        df["Created"] = pd.to_datetime(df["Created"], errors="coerce")
        df = df.dropna(subset=["Created"])
        df["MonthStr"] = df["Created"].dt.strftime("%b %Y")

        selected_months = months.split(",")
        df = df[df["MonthStr"].isin(selected_months)]

        def normalize(col):
            return df[col].dropna().astype(str).str.strip().str.lower()

        if category2:
            selected_cat2 = [v.lower() for v in category2.split(",")]
            df = df[normalize("หมวดหมู่2").isin(selected_cat2)]
        if category3:
            selected_cat3 = [v.lower() for v in category3.split(",")]
            df = df[normalize("หมวดหมู่3").isin(selected_cat3)]
        if status:
            selected_status = [v.lower() for v in status.split(",")]
            df = df[normalize("สถานะ").isin(selected_status)]
        if status_process:
            selected_status_process = [v.lower() for v in status_process.split(",")]
            df = df[normalize("สถานะ Process").isin(selected_status_process)]

        df["หมวดหมู่2"] = df["หมวดหมู่2"].astype(str).str.strip()
        df["หมวดหมู่3"] = df["หมวดหมู่3"].astype(str).str.strip()

        pivot = pd.pivot_table(
            df,
            values="Ticket",
            index=["หมวดหมู่2", "หมวดหมู่3"],
            columns="MonthStr",
            aggfunc="sum",
            fill_value=0,
        ).reset_index()

        month_cols = [col for col in selected_months if col in pivot.columns]
        pivot["Grand Total"] = pivot[month_cols].sum(axis=1)

        grand_total_by_cat2 = pivot.groupby("หมวดหมู่2")["Grand Total"].transform("sum")
        pivot["ลำดับ"] = pivot.groupby("หมวดหมู่2")["Grand Total"].rank(method="first", ascending=False).astype(int)
        pivot["DEBUG_Total_หมวดหมู่2"] = grand_total_by_cat2

        if top5:
            pivot = pivot.sort_values(["หมวดหมู่2", "Grand Total"], ascending=[True, False])
            pivot = pivot.groupby("หมวดหมู่2").head(5)

        final = pivot.copy()
        final = final.sort_values(by="DEBUG_Total_หมวดหมู่2", ascending=False)
        final.insert(0, "A", final["DEBUG_Total_หมวดหมู่2"].rank(method="dense", ascending=False).astype(int))
        final = final.drop(columns=["DEBUG_Total_หมวดหมู่2"])

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            final.to_excel(writer, index=False, sheet_name="Output2")
        output.seek(0)
        return StreamingResponse(output, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                 headers={"Content-Disposition": "attachment; filename=Output2.xlsx"})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
