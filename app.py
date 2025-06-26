
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

app = FastAPI()

# อนุญาต origin ของ frontend
origins = [
    "https://dogzamak.github.io"
]

# เปิดใช้งาน CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # หรือระบุเป็น ["POST", "GET", "OPTIONS"]
    allow_headers=["*"],
)

# Route ที่ frontend เรียก
@app.post("/upload_raw_data")
async def upload_raw_data(file: UploadFile = File(...)):
    contents = await file.read()
    if not contents:
        return JSONResponse(content={"error": "Empty file"}, status_code=400)
    return {"message": "File received", "filename": file.filename}
