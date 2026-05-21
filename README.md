# Caption-Syncer

An automated video captioning and synchronization utility. This project uses a hybrid architecture featuring a high-performance C++ desktop orchestrator for media management and system tasks, combined with an isolated Python AI alignment engine utilizing WhisperX for millisecond-accurate forced subtitle alignment.
---
## System Architecture & Data Pipeline

The application cleanly splits labor between native system processing and deep learning modules.

1. **The Input Gate (C++):** Accepts the target .mp4 video and the user's custom text script baseline.
2. **Audio Separation (FFmpeg):** The C++ manager automatically extracts the video's audio track and down-samples it to a clean 16kHz mono .wav file.
3. **The AI Alignment Engine (Python & WhisperX):** - **WhisperX** transcribes the raw audio sounds to discover acoustic phonetic time boundaries down to the millisecond.
   - **`align.py`** runs a guarded smart-merge loop, comparing WhisperX's timings against the user's provided "ground truth" text script—discarding AI typos and mapping exact timings to the user's clean text.
4. **Structured Output:** The synchronized data is exported into a standard, frame-accurate SubRip (.srt) file.
5. **Framelock Playback (FFplay):** The C++ app invokes a custom media viewer window, overlaying the generated subtitle file on top of the native video stream seamlessly.

---

## Repository & Directory Layout

To maintain a lightweight and professional footprint, heavy compilation binaries, temporary caching directories, and Python virtual environments are hidden from source control. They are rebuilt locally using the following structure:

```text
C:\Projects\
├── bin/                   <-- [LOCAL] Holds external tool executables (ffmpeg, ffplay)
├── env/                   <-- [LOCAL] Isolated Python virtual environment for AI dependencies
├── workspace/             <-- [LOCAL] Sandbox area for videos, temporary files, and final .srt tracks
└── Caption-Project/       <-- [GITHUB REPO ROOT] Core source code and scripts
    ├── .gitignore         <-- Keeps the localized parent directories out of GitHub
    ├── CMakeLists.txt     <-- Build configurations for the C++ application
    ├── main.cpp           <-- C++ application orchestrator and controller
    └── align.py           <-- Python AI sequence matching and alignment script
```

## Local Prerequisites & Setup

Follow these steps to set up the necessary local components that are excluded from GitHub:

1. External Media Utilities (bin/)
- Create a folder named bin at your root directory (C:\Projects\bin).

- Download the official static builds for Windows from the FFmpeg Official Website.

- Place ffmpeg.exe and ffplay.exe directly inside that bin/ directory.

2. Isolated AI Environment (env/)
- Open your terminal at your root project path (C:\Projects).

- Initialize a Python virtual environment:
  "python -m venv env"

- Activate the environment:
  "env\Scripts\activate"

- Install WhisperX and its associated deep learning framework requirements:
  "pip install whisperx"

3. Media Sandbox (workspace/)
- Create a folder named workspace at your root directory (C:\Projects\workspace).

- Move the video file you wish to process (e.g., test.mp4) directly inside this folder.

  ---

## Building and Running the Project

Compiling the C++ Application

Launch Visual Studio.

Select "Open a local folder" and choose C:\Projects\Caption-Project.

Select your target architecture configuration (e.g., x64-Debug or x64-Release).

Press Ctrl + Shift + B to let CMake generate build scripts and compile the native orchestrator binary.

---

## Execution

Run the project directly through Visual Studio (F5) or execute the compiled binary.

Enter the filename of your video when prompted (e.g., test.mp4).

Paste or input your clean, custom text script baseline.

The application will sequentially run audio extraction, spin up the background AI script, generate the precision .srt timestamp file, and instantly boot up an integrated media player with perfectly frame-locked subtitles.
