# Surgical Phase Annotator

A simple tool for labeling surgical phases in videos. Runs locally on your machine — no internet connection required after installation, and videos never leave your computer.

---

## Installation (do this once)

### Step 1 — Install Python
If you don't have Python installed, download it from https://www.python.org/downloads/  
Choose **Python 3.10 or newer**. During installation, check the box **"Add Python to PATH"**.

### Step 2 — Install the tool
Open a terminal (Mac/Linux) or Command Prompt (Windows) and run:

```
pip install streamlit
```

That's it. There are no other dependencies.

---

## Running the tool

1. Open a terminal / Command Prompt
2. Navigate to the folder where you saved this tool:
   ```
   cd /path/to/surgical_annotator
   ```
3. Run:
   ```
   streamlit run app.py
   ```
4. Your browser will open automatically at `http://localhost:8501`

---

## How to annotate

1. **Enter your video folder path** in the sidebar (e.g. `C:\Users\YourName\Videos` on Windows, or `/Users/YourName/Videos` on Mac)
2. **Select a video** from the dropdown — it will play in the browser
3. **Watch the video** and note the timestamps when phases start and end (the timestamp is shown in the video player when you pause)
4. **Fill in the form** below the video:
   - Start time: type in `MM:SS` format (e.g. `01:23`) or `HH:MM:SS`
   - End time: same format
   - Phase: select from the dropdown
   - Notes: optional free-text observations
5. Click **Add Phase** — it saves automatically
6. Repeat for each phase in the video
7. Use **Next video →** to move to the next one

---

## Output files

Annotations are saved automatically as JSON files next to your videos (or in the folder you specify). When all videos are done, click **Export all as CSV** in the sidebar to get a single spreadsheet with all annotations.

**CSV columns:** `video`, `phase`, `start_time_sec`, `end_time_sec`, `duration_sec`, `start_hms`, `end_hms`, `notes`

---

## Surgical phases

The following phases are available in the dropdown:

- Preparation
- Incision
- Dissection
- Haemostasis
- Target Phase
- Suturing
- Wound Closure
- Other

> **To change the phase list**, open `app.py` in a text editor and edit the `SURGICAL_PHASES` list near the top of the file.

---

## Troubleshooting

**"streamlit is not recognized"** → Close and reopen the terminal after installing Python, or try `python -m streamlit run app.py`

**Video doesn't play** → Make sure the video is in MP4, AVI, MOV, MKV, or M4V format. MP4 (H.264) works best in browsers.

**Page doesn't open automatically** → Open your browser manually and go to `http://localhost:8501`

**To stop the tool** → Press `Ctrl+C` in the terminal