from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
import shutil
import os

app = FastAPI(title="Audio Transfer Server")

IS_VERCEL = os.getenv("VERCEL") == "1"

UPLOAD_DIR = "uploaded_audio"

if not IS_VERCEL:
    os.makedirs(UPLOAD_DIR, exist_ok=True)
STORED_FILE_PATH = None


@app.post("/receive")
async def receive_audio(file: UploadFile = File(...)):
    """Receive an audio file from the client and store it."""
    global STORED_FILE_PATH

    allowed_types = ["audio/mpeg", "audio/mp3", "audio/wav", "audio/ogg", "audio/flac", "audio/x-wav", "audio/mp4"]
    if file.content_type not in allowed_types:
        # Be lenient — also accept by extension
        ext = os.path.splitext(file.filename)[-1].lower()
        if ext not in [".mp3", ".wav", ".ogg", ".flac", ".m4a", ".aac"]:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.content_type}")

    contents = await file.read()

    if not IS_VERCEL:
        save_path = os.path.join(UPLOAD_DIR, file.filename)

        with open(save_path, "wb") as buffer:
            buffer.write(contents)

    return {
        "message": "File received successfully",
        "filename": file.filename,
        "size_bytes": len(contents)
    }

    STORED_FILE_PATH = save_path

    return {
        "status": "success",
        "message": f"✅ File '{file.filename}' received successfully by server.",
        "filename": file.filename,
        "size_bytes": os.path.getsize(save_path),
    }


@app.get("/send")
async def send_audio():
    """Send the most recently uploaded audio file back to the client."""
    global STORED_FILE_PATH

    if STORED_FILE_PATH is None or not os.path.exists(STORED_FILE_PATH):
        raise HTTPException(status_code=404, detail="No audio file available on server. Upload one first.")

    filename = os.path.basename(STORED_FILE_PATH)
    if IS_VERCEL:
    return {
        "message": "Download endpoint is disabled on Vercel."
    }
    return FileResponse(
        path=STORED_FILE_PATH,
        media_type="audio/mpeg",
        filename=filename,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@app.get("/")
async def root():
    return {"message": "Audio Transfer Server is running", "endpoints": ["/receive (POST)", "/send (GET)"]}
