import streamlit as st
import streamlit.components.v1 as components
import json
import csv
import os
from pathlib import Path
import threading
import http.server
import socketserver

# -- Page config ---------------------------------------------------------------
st.set_page_config(
    page_title="Surgical Phase Annotator",
    page_icon="🔬",
    layout="wide",
)

# -- Styling -------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif;
}

.stApp {
    background-color: #f0f6ff;
    color: #0f1f3d;
}

h1, h2, h3 {
    font-family: 'IBM Plex Mono', monospace !important;
    letter-spacing: -0.02em;
    color: #0f1f3d;
}

section[data-testid="stSidebar"] {
    background-color: #daeaf7;
    border-right: 1px solid #b6d4ee;
}

section[data-testid="stSidebar"] * {
    color: #0f1f3d !important;
}

.status-bar {
    background: #e4f0fb;
    border: 1px solid #b6d4ee;
    border-radius: 4px;
    padding: 8px 14px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.8rem;
    color: #3d6a99;
    margin-bottom: 16px;
}

.video-badge {
    background: #2a7fc1;
    color: white;
    padding: 2px 8px;
    border-radius: 3px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.75rem;
    font-weight: 600;
}

.instructions {
    background: #ffffff;
    border: 1px solid #b6d4ee;
    border-top: 2px solid #2a7fc1;
    border-radius: 4px;
    padding: 14px 16px;
    margin-bottom: 20px;
    font-size: 0.85rem;
    color: #3d6a99;
    line-height: 1.7;
}

div[data-testid="metric-container"] {
    background: #ffffff;
    border: 1px solid #b6d4ee;
    border-radius: 6px;
    padding: 12px 16px;
}

div[data-testid="stSelectbox"] label,
div[data-testid="stNumberInput"] label,
div[data-testid="stTextInput"] label {
    color: #3d6a99 !important;
    font-size: 0.78rem !important;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    font-family: 'IBM Plex Mono', monospace !important;
}

.stButton > button {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.82rem;
    letter-spacing: 0.03em;
    border-radius: 4px;
    color: #0f1f3d !important;
    border-color: #b6d4ee !important;
    background-color: #e4f0fb !important;
}

.stButton > button[kind="primary"] {
    background-color: #2a7fc1 !important;
    border-color: #1a6aad !important;
    color: #ffffff !important;
}

.stButton > button:hover {
    border-color: #2a7fc1 !important;
    background-color: #cce3f5 !important;
    color: #0f1f3d !important;
}

.stButton > button[kind="primary"]:hover {
    background-color: #1a6aad !important;
    color: #ffffff !important;
}

hr {
    border-color: #b6d4ee;
    margin: 20px 0;
}

div[data-testid="stNumberInput"] input,
div[data-testid="stTextInput"] input {
    background-color: #ffffff !important;
    border-color: #b6d4ee !important;
    color: #0f1f3d !important;
    font-family: 'IBM Plex Mono', monospace;
}

div[data-testid="stSelectbox"] > div > div {
    background-color: #ffffff !important;
    border-color: #b6d4ee !important;
    color: #0f1f3d !important;
}
</style>
""", unsafe_allow_html=True)

# -- Phases -- edit this list to match your study ------------------------------
SURGICAL_PHASES = [
    "Splenic flexure / left colon mobilization",
    "Abdominal Posterior Mesorectal Dissection",
    "Abdominal Anterior Mesorectal Dissection",
    "Abdominal Lateral Mesorectal Dissection",
    "Lymphadenectomy & Arterial Ligation",
    "Resection and Anastomosis",
    "Idle",
]

# -- Helpers -------------------------------------------------------------------

def start_video_server(directory, port=8765):
    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=directory, **kwargs)
        def log_message(self, format, *args):
            pass
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", port), Handler) as httpd:
        httpd.serve_forever()


def seconds_to_hms(s: float) -> str:
    """Convert seconds to HH:MM:SS.mmm string."""
    ms = round((s % 1) * 1000)
    s = int(s)
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    if h:
        return f"{h:02d}:{m:02d}:{sec:02d}.{ms:03d}"
    return f"{m:02d}:{sec:02d}.{ms:03d}"


def hms_to_seconds(hms: str) -> float:
    """
    Accept any of these formats:
      MM:SS
      MM:SS.mmm
      HH:MM:SS
      HH:MM:SS.mmm
      plain seconds (e.g. 83.5)
    Returns -1.0 on parse failure.
    """
    hms = hms.strip()
    try:
        parts = hms.split(":")
        if len(parts) == 1:
            # plain seconds, possibly with decimal
            return float(parts[0])
        elif len(parts) == 2:
            # MM:SS or MM:SS.mmm
            return int(parts[0]) * 60 + float(parts[1])
        else:
            # HH:MM:SS or HH:MM:SS.mmm
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    except ValueError:
        return -1.0


def clean_path(folder: str) -> str:
    """Strip hidden unicode chars that appear when copy-pasting Windows paths."""
    return folder.strip().strip(
        "\u202a\u202b\u200b\u200e\u200f\ufeff"
    ).replace("\\", "/")


def get_video_files(folder: str):
    exts = {".mp4", ".avi", ".mov", ".mkv", ".wmv", ".m4v"}
    folder = clean_path(folder)
    p = Path(folder)
    if not p.exists():
        return []
    return sorted([f for f in p.iterdir() if f.suffix.lower() in exts])


def annotation_save_path(video_path: Path, save_dir: str) -> Path:
    return Path(save_dir) / (video_path.stem + "_annotations.json")


def load_annotations(video_path: Path, save_dir: str):
    path = annotation_save_path(video_path, save_dir)
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return []


def save_annotations(video_path: Path, save_dir: str, annotations: list):
    Path(save_dir).mkdir(parents=True, exist_ok=True)
    path = annotation_save_path(video_path, save_dir)
    with open(path, "w") as f:
        json.dump(annotations, f, indent=2)


def export_all_csv(save_dir: str, video_files: list):
    rows = []
    for vf in video_files:
        anns = load_annotations(vf, save_dir)
        for a in anns:
            rows.append({
                "video": vf.name,
                "phase": a["phase"],
                "start_time_sec": a["start_sec"],
                "end_time_sec": a["end_sec"],
                "duration_sec": round(a["end_sec"] - a["start_sec"], 3),
                "start_hms": seconds_to_hms(a["start_sec"]),
                "end_hms": seconds_to_hms(a["end_sec"]),
                "notes": a.get("notes", ""),
            })
    csv_path = Path(save_dir) / "all_annotations.csv"
    if rows:
        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
    return csv_path, rows


# -- Session state init --------------------------------------------------------
if "video_idx" not in st.session_state:
    st.session_state.video_idx = 0
if "captured_start" not in st.session_state:
    st.session_state.captured_start = ""
if "captured_end" not in st.session_state:
    st.session_state.captured_end = ""

# -- Read captured timestamps from URL hash ------------------------------------
# The iframe writes "start:<t>" or "end:<t>" to window.parent.location.hash.
# Streamlit exposes this via st.query_params.
params = st.query_params
if "capture" in params:
    val = params["capture"]          # e.g. "start:83.521" or "end:225.000"
    if val.startswith("start:"):
        st.session_state.captured_start = val[6:]
        st.query_params.clear()
        st.rerun()
    elif val.startswith("end:"):
        st.session_state.captured_end = val[4:]
        st.query_params.clear()
        st.rerun()

# -- Sidebar -------------------------------------------------------------------
with st.sidebar:
    st.markdown("## Surgical Annotator")
    st.markdown("---")

    video_folder = st.text_input(
        "Video folder path",
        value="",
        placeholder="C:\\Users\\name\\Videos",
        help="Folder containing .mp4 / .avi / .mov files",
    )
    save_dir = st.text_input(
        "Annotation save folder",
        value="annotations",
        help="Where JSON and CSV files will be saved",
    )

    video_files = get_video_files(video_folder) if video_folder else []

    if video_folder:
        resolved = clean_path(video_folder)
        exists = Path(resolved).exists()
        st.caption(f"Path: `{resolved}`")
        st.caption(f"Folder found: {'yes' if exists else 'NO - check the path'}")

    if video_files:
        st.markdown(f"**{len(video_files)} video(s) found**")
        video_names = [v.name for v in video_files]
        selected_name = st.selectbox(
            "Select video",
            video_names,
            index=st.session_state.video_idx,
        )
        st.session_state.video_idx = video_names.index(selected_name)

        st.markdown("---")
        st.markdown("**Progress**")
        for i, vf in enumerate(video_files):
            anns = load_annotations(vf, save_dir)
            status = f"done ({len(anns)} phases)" if anns else "not started"
            marker = "**to**" if i == st.session_state.video_idx else "&nbsp;&nbsp;&nbsp;"
            st.markdown(
                f"<small>{marker} <code>{vf.name[:28]}</code><br>"
                f"&nbsp;&nbsp;&nbsp;&nbsp;{status}</small>",
                unsafe_allow_html=True,
            )

        st.markdown("---")
        if st.button("Export all as CSV", use_container_width=True):
            csv_path, rows = export_all_csv(save_dir, video_files)
            if rows:
                import io
                buf = io.StringIO()
                writer = csv.DictWriter(buf, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
                st.download_button(
                    "Download CSV",
                    buf.getvalue(),
                    file_name="all_annotations.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
            else:
                st.warning("No annotations yet.")
    else:
        if video_folder:
            st.error("No video files found in that folder.")
        else:
            st.info("Enter a folder path above to get started.")

# -- Start video server --------------------------------------------------------
if video_files and "video_server" not in st.session_state:
    thread = threading.Thread(
        target=start_video_server,
        args=(str(Path(clean_path(video_folder))), 8765),
        daemon=True,
    )
    thread.start()
    st.session_state.video_server = True

# -- Main area -----------------------------------------------------------------
if not video_files:
    st.markdown("# Surgical Phase Annotator")
    st.markdown("""
    <div class="instructions">
    <strong>Getting started:</strong><br>
    1. Enter the path to your video folder in the sidebar<br>
    2. Select a video to annotate<br>
    3. Pause the video at the start of a phase and click <em>Capture start time</em>,
       then do the same at the end and click <em>Capture end time</em><br>
    4. Select the phase, add any notes, and click <em>Add Phase</em><br>
    5. Export all annotations as CSV when done
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# Active video
video_path = video_files[st.session_state.video_idx]
annotations = load_annotations(video_path, save_dir)

# Header
col_title, col_badge = st.columns([6, 1])
with col_title:
    st.markdown(f"## {video_path.name}")
with col_badge:
    st.markdown(
        f'<div style="text-align:right;padding-top:14px">'
        f'<span class="video-badge">{st.session_state.video_idx + 1} / {len(video_files)}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

st.markdown(
    '<div class="status-bar">'
    f'Folder: {video_path.parent} &nbsp;|&nbsp; '
    f'Saving to: {annotation_save_path(video_path, save_dir)}'
    '</div>',
    unsafe_allow_html=True,
)

st.markdown("""
<div class="instructions">
<strong>How to annotate:</strong> &nbsp;
Pause the video at the start of a phase and click <em>Capture start time</em>,
then scrub to the end and click <em>Capture end time</em>.
You can also type timestamps manually: <code>MM:SS</code>, <code>MM:SS.mmm</code>,
<code>HH:MM:SS</code>, or <code>HH:MM:SS.mmm</code>.
</div>
""", unsafe_allow_html=True)

# -- Video player with capture buttons -----------------------------------------
# The buttons live inside the iframe so they have direct access to video.currentTime.
# They communicate back to Streamlit by setting window.parent.location.search,
# which Streamlit reads as query params, triggering a rerun that pre-fills the fields.
components.html(
    f"""
    <style>
        body {{ margin: 0; background: #f0f6ff; font-family: 'IBM Plex Sans', sans-serif; }}
        video {{ display: block; width: 100%; max-height: 480px; background: #000; }}
        .btn-row {{
            display: flex;
            gap: 10px;
            margin-top: 10px;
        }}
        button {{
            flex: 1;
            padding: 8px 0;
            font-family: 'IBM Plex Mono', monospace;
            font-size: 0.82rem;
            border-radius: 4px;
            cursor: pointer;
            border: 1px solid #b6d4ee;
            transition: background 0.15s;
        }}
        #btn-start {{
            background: #e4f0fb;
            color: #0f1f3d;
            border-color: #2a7fc1;
        }}
        #btn-start:hover {{ background: #cce3f5; }}
        #btn-end {{
            background: #2a7fc1;
            color: #ffffff;
            border-color: #1a6aad;
        }}
        #btn-end:hover {{ background: #1a6aad; }}
        .captured {{
            margin-top: 6px;
            font-family: 'IBM Plex Mono', monospace;
            font-size: 0.78rem;
            color: #3d6a99;
            min-height: 1.2em;
        }}
    </style>

    <video id="player" controls>
        <source
            src="http://localhost:8765/{video_path.name}?v={st.session_state.video_idx}"
            type="video/mp4"
        >
    </video>

    <div class="btn-row">
        <button id="btn-start" onclick="capture('start')">
            &#9654; Capture start time
        </button>
        <button id="btn-end" onclick="capture('end')">
            &#9654; Capture end time
        </button>
    </div>
    <div class="captured" id="status">Pause the video then click a button to capture the timestamp.</div>

    <script>
        document.getElementById("player").load();

        function capture(which) {{
            var t = document.getElementById("player").currentTime;
            // Format as HH:MM:SS.mmm
            var ms  = Math.round((t % 1) * 1000);
            var s   = Math.floor(t);
            var h   = Math.floor(s / 3600);
            var m   = Math.floor((s % 3600) / 60);
            var sec = s % 60;
            var ts  = (h > 0 ? pad(h) + ":" : "") +
                      pad(m) + ":" + pad(sec) + "." + pad3(ms);

            // Show feedback inside the iframe
            document.getElementById("status").textContent =
                (which === "start" ? "Start" : "End") + " captured: " + ts;

            // Send to Streamlit via query param — triggers a Python rerun
            window.parent.location.search = "?capture=" + which + ":" + t.toFixed(3);
        }}

        function pad(n)  {{ return String(n).padStart(2, "0"); }}
        function pad3(n) {{ return String(n).padStart(3, "0"); }}
    </script>
    """,
    height=580,
    scrolling=False,
)

st.markdown("---")

# -- Add annotation form -------------------------------------------------------
st.markdown("### Add Phase Annotation")

# Push captured values into the widget keys directly
if st.session_state.captured_start:
    st.session_state["start_inp"] = st.session_state.captured_start
    st.session_state.captured_start = ""
if st.session_state.captured_end:
    st.session_state["end_inp"] = st.session_state.captured_end
    st.session_state.captured_end = ""

col1, col2, col3, col4 = st.columns([2, 2, 3, 3])
with col1:
    start_input = st.text_input(
        "Start time",
        placeholder="e.g. 01:23.500",
        key="start_inp",
    )
with col2:
    end_input = st.text_input(
        "End time",
        placeholder="e.g. 03:45.000",
        key="end_inp",
    )
with col3:
    phase_select = st.selectbox("Phase", SURGICAL_PHASES, key="phase_sel")
with col4:
    notes_input = st.text_input(
        "Notes (optional)", placeholder="Any observations...", key="notes_inp"
    )

add_col, clear_col, _ = st.columns([2, 2, 4])
with add_col:
    add_clicked = st.button("Add Phase", type="primary", use_container_width=True)
with clear_col:
    if st.button("Clear times", use_container_width=True):
        st.session_state.captured_start = ""
        st.session_state.captured_end = ""
        st.rerun()

if add_clicked:
    start_sec = hms_to_seconds(start_input) if start_input else -1
    end_sec   = hms_to_seconds(end_input)   if end_input   else -1

    if start_sec < 0:
        st.error("Enter a valid start time.")
    elif end_sec < 0:
        st.error("Enter a valid end time.")
    elif end_sec <= start_sec:
        st.error("End time must be after start time.")
    else:
        annotations.append({
            "phase":     phase_select,
            "start_sec": round(start_sec, 3),
            "end_sec":   round(end_sec,   3),
            "notes":     notes_input.strip(),
        })
        annotations.sort(key=lambda x: x["start_sec"])
        save_annotations(video_path, save_dir, annotations)
        # Clear captures after a successful save
        st.session_state.captured_start = ""
        st.session_state.captured_end   = ""
        st.success(
            f"Saved: {phase_select}  "
            f"{seconds_to_hms(start_sec)} to {seconds_to_hms(end_sec)}"
        )
        st.rerun()

# -- Annotations table ---------------------------------------------------------
st.markdown("---")
st.markdown(f"### Annotations for this video &nbsp; `{len(annotations)} phase(s)`")

if not annotations:
    st.markdown(
        '<div style="color:#5a7fa8;font-family:\'IBM Plex Mono\','
        'monospace;font-size:0.85rem;padding:16px 0">'
        'No phases annotated yet.'
        '</div>',
        unsafe_allow_html=True,
    )
else:
    hcols = st.columns([1, 2, 2, 3, 4, 1])
    for col, label in zip(hcols, ["#", "Start", "End", "Duration", "Phase", "Del"]):
        col.markdown(
            f'<div style="color:#5a7fa8;font-size:0.72rem;text-transform:uppercase;'
            f'letter-spacing:0.08em;font-family:\'IBM Plex Mono\','
            f'monospace;padding-bottom:4px">{label}</div>',
            unsafe_allow_html=True,
        )

    for i, ann in enumerate(annotations):
        dur = ann["end_sec"] - ann["start_sec"]
        c1, c2, c3, c4, c5, c6 = st.columns([1, 2, 2, 3, 4, 1])
        c1.markdown(
            f'<div style="font-family:\'IBM Plex Mono\',monospace;'
            f'font-size:0.82rem;color:#5a7fa8">{i+1}</div>',
            unsafe_allow_html=True,
        )
        c2.markdown(
            f'<div style="font-family:\'IBM Plex Mono\',monospace;'
            f'font-size:0.82rem;color:#0f1f3d">{seconds_to_hms(ann["start_sec"])}</div>',
            unsafe_allow_html=True,
        )
        c3.markdown(
            f'<div style="font-family:\'IBM Plex Mono\',monospace;'
            f'font-size:0.82rem;color:#0f1f3d">{seconds_to_hms(ann["end_sec"])}</div>',
            unsafe_allow_html=True,
        )
        c4.markdown(
            f'<div style="font-family:\'IBM Plex Mono\',monospace;'
            f'font-size:0.82rem;color:#5a7fa8">{seconds_to_hms(dur)}</div>',
            unsafe_allow_html=True,
        )
        notes_html = (
            f"&nbsp; <span style='color:#5a7fa8;font-size:0.78rem'>"
            f"{ann['notes']}</span>"
            if ann.get("notes") else ""
        )
        c5.markdown(
            f'<div style="font-family:\'IBM Plex Mono\',monospace;font-size:0.82rem">'
            f'<span style="background:#dbeeff;border:1px solid #2a7fc1;color:#1a5f9e;'
            f'padding:1px 7px;border-radius:3px;font-size:0.75rem">{ann["phase"]}</span>'
            f'{notes_html}'
            f'</div>',
            unsafe_allow_html=True,
        )
        if c6.button("x", key=f"del_{i}", help="Delete this annotation"):
            annotations.pop(i)
            save_annotations(video_path, save_dir, annotations)
            st.rerun()

# -- Navigation ----------------------------------------------------------------
st.markdown("---")
nav1, nav2, nav3 = st.columns([2, 4, 2])
with nav1:
    if st.session_state.video_idx > 0:
        if st.button("Previous video", use_container_width=True):
            st.session_state.captured_start = ""
            st.session_state.captured_end   = ""
            st.session_state.video_idx -= 1
            st.rerun()
with nav3:
    if st.session_state.video_idx < len(video_files) - 1:
        if st.button("Next video", type="primary", use_container_width=True):
            st.session_state.captured_start = ""
            st.session_state.captured_end   = ""
            st.session_state.video_idx += 1
            st.rerun()

# -- Per-video JSON download ---------------------------------------------------
if annotations:
    st.download_button(
        "Download JSON for this video",
        data=json.dumps(annotations, indent=2),
        file_name=f"{video_path.stem}_annotations.json",
        mime="application/json",
    )