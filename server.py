from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
import os
import io
import uuid
import requests
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

# Used only for the database table (this part of the library works fine).
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Storage is handled with direct REST calls instead of the storage3 client,
# which has a bug in some versions that throws:
#   'dict' object has no attribute 'text'
STORAGE_BASE = f"{SUPABASE_URL}/storage/v1/object"
STORAGE_HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
}

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
    content_type = file.content_type or "audio/mpeg"
    storage_path = f"{uuid.uuid4()}{ext}"

    upload_resp = requests.post(
        f"{STORAGE_BASE}/{BUCKET_NAME}/{storage_path}",
        headers={**STORAGE_HEADERS, "Content-Type": content_type},
        data=contents,
    )
    if upload_resp.status_code not in (200, 201):
        raise HTTPException(
            status_code=500,
            detail=f"Storage upload failed: {upload_resp.status_code} {upload_resp.text}",
        )

    record = {
        "filename": file.filename,
        "storage_path": storage_path,
        "content_type": content_type,
        "size_bytes": len(contents),
    }

    try:
        result = supabase.table("audio_files").insert(record).execute()
    except Exception as e:
        requests.delete(f"{STORAGE_BASE}/{BUCKET_NAME}/{storage_path}", headers=STORAGE_HEADERS)
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

    download_resp = requests.get(
        f"{STORAGE_BASE}/{BUCKET_NAME}/{record['storage_path']}",
        headers=STORAGE_HEADERS,
    )
    if download_resp.status_code != 200:
        raise HTTPException(status_code=404, detail="File exists in database but not in storage.")

    return StreamingResponse(
        io.BytesIO(download_resp.content),
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