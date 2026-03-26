# Surgical Phase Annotator

A simple tool for labeling surgical phases in videos. Runs locally on your machine so no internet connection is required after installation, and videos never leave your computer.

---

## Installation (only done once)

### Step 1 - Install Python
If you don't have Python installed, download it from https://www.python.org/downloads/  
Choose **Python 3.10 or newer**. During installation, check the box **"Add Python to PATH"**.

### Step 2 - Download the repository from GitHub
On the GitHub repository website, navigate to the green **Code** button and choose **Download ZIP**. Once you have it downloaded, choose a folder where you want to unzip the files. If you want to see the code and easily navigate through the tool, I recommend having Visual Studio Code (https://code.visualstudio.com/) or a similar environment. This will also make running the commands for tool activation easier.

### Step 3 - Install the streamlit library
Open a terminal (Mac/Linux), Command Prompt (Windows) or New Terminal in Visual Studio Code and run:

```
pip install streamlit
```

That is all, there are no other requirements for running the labeling tool.

---

## Running the tool

1. Open a terminal / Command Prompt
2. Navigate to the folder where you saved this tool:
   ```
   cd /path/to/Surgical-Video-Labeling
   ```
3. Run:
   ```
   streamlit run app.py
   ```
4. Your browser will open automatically at `http://localhost:8501`

In case you are using VS Code or a similar environment:

1. Open the Surgical-Video-Labeling project using VS Code
2. In the bar on the top of the page, choose **Terminal** then click on **New Terminal**
3. In the terminal type:
   ```
   streamlit run app.py
   ```
4. Your browser will open automatically at `http://localhost:8501`
---

## How to annotate

1. **Enter your video folder path** in the sidebar (e.g. `C:\Users\YourName\Videos` on Windows, or `/Users/YourName/Videos` on Mac). It is recommended to have the videos you want to annotate in one folder so that you can easily access them
2. **Enter your annotations folder path** in the sidebar. This is where annotations will be saved automatically. If you don't enter anything, annotations will be saved in the "annotations\" folder in the same path that you ran the `streamlit run app.py` command from.
3. **Select a video** from the dropdown, it will play in the browser on the main part of the website
4. **Play the video** and when you reach the desired timestamp, pause the video
5. Click **Copy current time** which copies the timestamp to your clipboard
6. **Fill in the form** below the video:
   - Start time: paste the timestamp using **Ctrl + V** or enter the timestamp manually (accepted formats: `MM:SS`,`MM:SS.mmm`,`HH:MM:SS`, `HH:MM:SS.mmm`)
   - End time: same as Start time
   - Phase: select from the dropdown
   - Notes: optional free-text observations
7. Click **Add Phase** which saves the annotation automatically to a JSON file format
9. Repeat for each phase in the video
9. When done with a certain video, you can choose a different one from the sidebar

---

## Output files

Annotations per each video are saved automatically as JSON files in the path you decided on in the second step of **How to annotate** section. The JSON files are named in a format `video-name_annotations.json`. If you want to be sure that annotations for that video are saved, then click the button **Download JSON for this video** and the file should show up in your Downloads folder. When all videos are done, click **Export all as CSV** in the sidebar to get a single spreadsheet with all annotations.

**CSV columns:** `video`, `phase`, `start_time_sec`, `end_time_sec`, `duration_sec`, `start_hms`, `end_hms`, `notes`

---

## Surgical phases

The first six phases that are available in the dropdown were defined in the Laparoscopic TME Performance Tool document. The following labels can be chosen from:

- Splenic flexure / left colon mobilization - Task Area 1
- Abdominal Posterior Mesorectal Dissection - Task Area 2a + 2b (NOTE: POSSIBLY SEPARATE THEM)
- Abdominal Anterior Mesorectal Dissection - Task Area 3
- Abdominal Lateral Mesorectal Dissection - Task Area 4
- Lymphadenectomy & Arterial Ligation - Task Area 5a + 5b + 5c
- Resection and Anastomosis - Task Area 6a + 6b
- Idle - no movement with camera/instruments for >5 seconds
- Exception - an additional named task that takes >30 seconds. This phase comprises some unique phases that occurred exceptionally and unexpectedly during the annotation of the videos, due to the complexity of colorectal procedures. This included the closing of a bladder lesion, excisions of liver tissue for biopsy, appendectomy, a second resection of the rectum during the same procedure, resection of a mesocolonic cyst, cholecystectomy, elaborate hemostasis of splenic bleeding and a suturing of the abdominal wall due to bleeding from a trocar incision.


---

## Troubleshooting

Make sure to always use the same path for saving annotations so that you can work on the same video even after closing a session and taking a break.

**"streamlit is not recognized"** → Close and reopen the terminal after installing Python, or try `python -m streamlit run app.py`

**Video doesn't play** → Make sure the video is in MP4, AVI, MOV, MKV, or M4V format. Though MP4 works best in browsers.

**Page doesn't open automatically** → Open your browser manually and go to `http://localhost:8501`

**To stop the tool** → Press `Ctrl+C` in the terminal