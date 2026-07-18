import streamlit as st
import requests
import os

SERVER_URL = "http://127.0.0.1:8000"

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Audio Transfer",
    page_icon="🎵",
    layout="centered",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .main { background-color: #0f0f14; }

    .stApp {
        background: linear-gradient(135deg, #0f0f14 0%, #141420 100%);
    }

    .section-box {
        background: #1a1a2e;
        border: 1px solid #2a2a4a;
        border-radius: 16px;
        padding: 2rem 2rem 1.5rem 2rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 24px rgba(0,0,0,0.4);
    }

    .section-label {
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 0.15em;
        text-transform: uppercase;
        color: #6c63ff;
        margin-bottom: 0.4rem;
    }

    .section-title {
        font-size: 1.15rem;
        font-weight: 600;
        color: #e8e8f0;
        margin-bottom: 1.2rem;
    }

    .status-idle {
        font-size: 0.85rem;
        color: #555577;
        font-style: italic;
        padding: 0.5rem 0;
    }

    .status-success {
        font-size: 0.85rem;
        color: #4ecca3;
        padding: 0.5rem 0.75rem;
        background: rgba(78,204,163,0.1);
        border-left: 3px solid #4ecca3;
        border-radius: 4px;
    }

    .status-error {
        font-size: 0.85rem;
        color: #ff6b8a;
        padding: 0.5rem 0.75rem;
        background: rgba(255,107,138,0.1);
        border-left: 3px solid #ff6b8a;
        border-radius: 4px;
    }

    .stButton > button {
        background: linear-gradient(135deg, #6c63ff, #a78bfa);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1.4rem;
        font-weight: 600;
        font-size: 0.875rem;
        letter-spacing: 0.02em;
        transition: opacity 0.2s;
        width: 100%;
    }

    .stButton > button:hover {
        opacity: 0.88;
        border: none;
    }

    div[data-testid="stFileUploader"] {
        background: #12121e;
        border: 1.5px dashed #2a2a4a;
        border-radius: 10px;
        padding: 0.5rem;
    }

    h1 {
        color: #e8e8f0 !important;
        font-size: 1.8rem !important;
        font-weight: 700 !important;
        text-align: center;
        letter-spacing: -0.01em;
    }

    .subtitle {
        text-align: center;
        color: #555577;
        font-size: 0.85rem;
        margin-top: -0.5rem;
        margin-bottom: 2rem;
    }

    hr { border-color: #1e1e30 !important; }p
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("# 🎵 Audio Transfer")
st.markdown('<p class="subtitle">Upload & retrieve audio files via the local server</p>', unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
if "upload_status" not in st.session_state:
    st.session_state.upload_status = None
if "download_status" not in st.session_state:
    st.session_state.download_status = None
if "download_data" not in st.session_state:
    st.session_state.download_data = None
if "download_filename" not in st.session_state:
    st.session_state.download_filename = None

# ── Section 1 – Upload ────────────────────────────────────────────────────────
with st.container():
    st.markdown('<div class="section-box">', unsafe_allow_html=True)
    st.markdown('<div class="section-label">Section 01</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Send Audio to Server</div>', unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Choose an audio file",
        type=["mp3", "wav", "ogg", "flac", "m4a", "aac"],
        label_visibility="collapsed",
    )

    if st.button("⬆  Upload to Server", key="upload_btn"):
        if uploaded_file is None:
            st.session_state.upload_status = ("error", "⚠ Please select an audio file first.")
        else:
            with st.spinner("Sending to server…"):
                try:
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type or "audio/mpeg")}
                    resp = requests.post(f"{SERVER_URL}/receive", files=files, timeout=30)
                    if resp.status_code == 200:
                        data = resp.json()
                        size_kb = round(data.get("size_bytes", 0) / 1024, 1)
                        st.session_state.upload_status = (
                            "success",
                            f"{data.get('message', 'File received.')}  ({size_kb} KB)",
                        )
                    else:
                        detail = resp.json().get("detail", resp.text)
                        st.session_state.upload_status = ("error", f"Server error {resp.status_code}: {detail}")
                except requests.exceptions.ConnectionError:
                    st.session_state.upload_status = ("error", "Cannot reach server. Is it running on port 8000?")
                except Exception as e:
                    st.session_state.upload_status = ("error", f"Unexpected error: {e}")

    # Status text
    if st.session_state.upload_status is None:
        st.markdown('<p class="status-idle">Awaiting upload…</p>', unsafe_allow_html=True)
    else:
        kind, msg = st.session_state.upload_status
        css_class = "status-success" if kind == "success" else "status-error"
        st.markdown(f'<p class="{css_class}">{msg}</p>', unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# ── Section 2 – Download ──────────────────────────────────────────────────────
with st.container():
    st.markdown('<div class="section-box">', unsafe_allow_html=True)
    st.markdown('<div class="section-label">Section 02</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Receive Audio from Server</div>', unsafe_allow_html=True)

    if st.button("⬇  Request File from Server", key="download_btn"):
        with st.spinner("Fetching from server…"):
            try:
                resp = requests.get(f"{SERVER_URL}/send", timeout=30)
                if resp.status_code == 200:
                    cd = resp.headers.get("Content-Disposition", "")
                    fname = "received_audio.mp3"
                    if "filename=" in cd:
                        fname = cd.split("filename=")[-1].strip().strip('"')
                    st.session_state.download_data = resp.content
                    st.session_state.download_filename = fname
                    st.session_state.download_status = (
                        "success",
                        f"✅ File '{fname}' received successfully ({round(len(resp.content)/1024,1)} KB). Ready to save.",
                    )
                elif resp.status_code == 404:
                    st.session_state.download_status = ("error", "No file on server yet. Upload one first.")
                    st.session_state.download_data = None
                else:
                    st.session_state.download_status = ("error", f"Server returned {resp.status_code}: {resp.text}")
                    st.session_state.download_data = None
            except requests.exceptions.ConnectionError:
                st.session_state.download_status = ("error", "Cannot reach server. Is it running on port 8000?")
                st.session_state.download_data = None
            except Exception as e:
                st.session_state.download_status = ("error", f"Unexpected error: {e}")
                st.session_state.download_data = None

    # Status text
    if st.session_state.download_status is None:
        st.markdown('<p class="status-idle">Awaiting request…</p>', unsafe_allow_html=True)
    else:
        kind, msg = st.session_state.download_status
        css_class = "status-success" if kind == "success" else "status-error"
        st.markdown(f'<p class="{css_class}">{msg}</p>', unsafe_allow_html=True)

    # Show save button only when file is ready
    if st.session_state.download_data:
        st.download_button(
            label="💾 Save File",
            data=st.session_state.download_data,
            file_name=st.session_state.download_filename,
            mime="audio/mpeg",
        )

    st.markdown("</div>", unsafe_allow_html=True)
