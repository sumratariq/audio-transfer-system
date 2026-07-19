# 🎵 Audio Transfer App

A minimal Streamlit + FastAPI demo for uploading and retrieving audio files.

## Project Structure

```
.
audio-transfer-system/

│── api/
│     └── index.py
│
│── app.py
│── requirements.txt
│── vercel.json
```

## Setup

```bash
pip install -r requirements.txt
```

## Running

You need **two terminals** — one for each process.

### Terminal 1 — Start the FastAPI server
```bash
uvicorn server:app --reload --port 8000
```
Server runs at: http://127.0.0.1:8000  
Interactive API docs: http://127.0.0.1:8000/docs

### Terminal 2 — Start the Streamlit UI
```bash
streamlit run app.py
```
Opens automatically at: http://localhost:8501

## Flow

| Section | Action | Endpoint |
|---------|--------|----------|
| Section 01 | Pick an audio file → click **Upload to Server** | `POST /receive` |
| Section 02 | Click **Request File from Server** → save it | `GET /send` |

## Supported Audio Formats
`.mp3`, `.wav`, `.ogg`, `.flac`, `.m4a`, `.aac`

## Notes
- The server stores only the **most recently uploaded** file in `uploaded_audio/`.
- Click **Save File** after a successful download to write the file to disk.
- If the server isn't running, both buttons will show a connection error.
