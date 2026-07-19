from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
import os

app = FastAPI(title="Audio Transfer Server")

# Detect whether the app is running on Vercel
IS_VERCEL = os.getenv("VERCEL") == "1"

UPLOAD_DIR = "uploaded_audio"

# Only create the upload directory when running locally
if not IS_VERCEL:
    os.makedirs(UPLOAD_DIR, exist_ok=True)

STORED_FILE_PATH = None


@app.get("/")
async def root():
    return {
        "message": "Audio Transfer Server is running",
        "environment": "Vercel" if IS_VERCEL else "Local",
        "endpoints": [
            "/receive (POST)",
            "/send (GET)"
        ]
    }


@app.post("/receive")
async def receive_audio(file: UploadFile = File(...)):
    global STORED_FILE_PATH

    allowed_extensions = [".mp3", ".wav", ".ogg", ".flac", ".m4a", ".aac"]
    ext = os.path.splitext(file.filename)[1].lower()

    if ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Unsupported audio format.")

    contents = await file.read()

    # Local machine: save the file
    if not IS_VERCEL:
        save_path = os.path.join(UPLOAD_DIR, file.filename)

        with open(save_path, "wb") as f:
            f.write(contents)

        STORED_FILE_PATH = save_path

    return {
        "status": "success",
        "message": "File received successfully.",
        "filename": file.filename,
        "size_bytes": len(contents)
    }


@app.get("/send")
async def send_audio():
    global STORED_FILE_PATH

    # Vercel cannot permanently store uploaded files
    if IS_VERCEL:
        return {
            "status": "info",
            "message": "Download endpoint is disabled on Vercel because the filesystem is read-only."
        }

    if STORED_FILE_PATH is None or not os.path.exists(STORED_FILE_PATH):
        raise HTTPException(
            status_code=404,
            detail="No uploaded audio file found."
        )

    filename = os.path.basename(STORED_FILE_PATH)

    return FileResponse(
        path=STORED_FILE_PATH,
        media_type="audio/mpeg",
        filename=filename
    )