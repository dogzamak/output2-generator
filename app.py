
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

app = FastAPI()

# Allow CORS for frontend app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/upload_raw_data")
async def upload_raw_data(rawFile: UploadFile = File(...)):
    if not rawFile:
        return JSONResponse(status_code=400, content={"detail": "No file uploaded"})
    return {"filename": rawFile.filename}
