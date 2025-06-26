
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://dogzamak.github.io"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/upload_raw_data")
async def upload_raw_data(file: UploadFile = File(...)):
    # ตัวอย่าง response สมมุติ
    return JSONResponse(content={
        "months": ["Mar 2025", "Apr 2025", "May 2025"],
        "category2Options": ["HRIS", "HRMS"],
        "category3Options": ["Login เข้า", "จัดการไม่ได้"],
        "statusOptions": ["Open", "Closed"],
        "processStatusOptions": ["In Progress", "Done"]
    })
