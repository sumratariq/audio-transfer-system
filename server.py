from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
import os
import io
import uuid
from supabase import create_client, Client

app = FastAPI(title="Audio Transfer Server")

# ── Supabase setup ────────────────────────────────────────────────────────────
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
BUCKET_NAME = os.environ.get("SUPABASE_BUCKET", "audio-files")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError(
        "SUPABASE_URL and SUPABASE_KEY must be set as environment variables."
    )

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

ALLOWED_EXTENSIONS = [".mp3", ".wav", ".ogg", ".flac", ".m4a", ".aac"]


@app.get("/")
async def root():
    return {
        "message": "Audio Transfer Server is running",
        "storage": "Supabase",
        "endpoints": [
            "/receive (POST)",
            "/send (GET)  -> latest file",
            "/files (GET) -> upload history",
        ],
    }


@app.post("/receive")
async def receive_audio(file: UploadFile = File(...)):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Unsupported audio format.")

    contents = await file.read()

    # Use a random storage key so filenames never collide in the bucket
    storage_path = f"{uuid.uuid4()}{ext}"

    try:
        supabase.storage.from_(BUCKET_NAME).upload(
            storage_path,
            contents,
            {"content-type": file.content_type or "audio/mpeg"},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Storage upload failed: {e}")

    record = {
        "filename": file.filename,
        "storage_path": storage_path,
        "content_type": file.content_type or "audio/mpeg",
        "size_bytes": len(contents),
    }

    try:
        result = supabase.table("audio_files").insert(record).execute()
    except Exception as e:
        # Roll back the uploaded blob if the metadata write fails
        supabase.storage.from_(BUCKET_NAME).remove([storage_path])
        raise HTTPException(status_code=500, detail=f"Database insert failed: {e}")

    return {
        "status": "success",
        "message": "File received and stored.",
        "filename": file.filename,
        "size_bytes": len(contents),
        "id": result.data[0]["id"] if result.data else None,
    }


@app.get("/send")
async def send_audio():
    """Returns the most recently uploaded audio file."""
    result = (
        supabase.table("audio_files")
        .select("*")
        .order("uploaded_at", desc=True)
        .limit(1)
        .execute()
    )

    if not result.data:
        raise HTTPException(status_code=404, detail="No uploaded audio file found.")

    record = result.data[0]

    try:
        file_bytes = supabase.storage.from_(BUCKET_NAME).download(record["storage_path"])
    except Exception:
        raise HTTPException(status_code=404, detail="File exists in database but not in storage.")

    return StreamingResponse(
        io.BytesIO(file_bytes),
        media_type=record["content_type"],
        headers={"Content-Disposition": f'attachment; filename="{record["filename"]}"'},
    )


@app.get("/files")
async def list_files():
    """Bonus: lets the frontend show a history of uploads instead of only the latest."""
    result = (
        supabase.table("audio_files")
        .select("id, filename, size_bytes, uploaded_at")
        .order("uploaded_at", desc=True)
        .execute()
    )
    return {"files": result.data}