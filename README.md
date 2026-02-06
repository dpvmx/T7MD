# T7MD Vision Pro 👁️

**Professional Computer Vision & HUD Generation Studio**

T7MD Vision Pro is a high-performance desktop application designed for AI-assisted video analysis and post-production. It leverages state-of-the-art models (**YOLO-World** and **YOLO-Face**) to detect objects, people, and faces, generating customizable futuristic HUDs (Head-Up Displays) and data overlays.

![Version](https://img.shields.io/badge/version-1.0.0-BCFF4E?style=for-the-badge&labelColor=151515)
![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge)
![PySide6](https://img.shields.io/badge/GUI-PySide6-41CD52?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Production_Ready-success?style=for-the-badge)

## ✨ Key Features

### 🧠 Advanced AI Engine
* **Dual Detection System:** Runs **YOLO-World** (Open Vocabulary) and **YOLO-Face** (Specialized Face Detection) simultaneously for maximum accuracy.
* **Open Vocabulary:** Detect any object by simply typing its name (e.g., "coffee cup, laptop, cat")—no retraining required.
* **Smart Model Management:** Prioritizes local models to ensure consistency and offline functionality.

### 🎨 Studio UI (V6)
* **Cyber Lime Aesthetic:** Professional dark mode interface with high-contrast accents (`#BCFF4E`).
* **Fluid Dashboard:** Responsive controls for real-time visualization customization.
* **Verbose Terminal:** "Hacker-style" terminal logs with ASCII art and detailed frame-by-frame progress.

### 🎬 Rendering & Export Profiles
* **Final Render:** Exports a `.mp4` video with all graphics baked in.
* **Compositing Mode:** Exports separate image sequences for professional post-production (After Effects/Davinci Resolve):
    * `/seq_bbox`: Only the bounding boxes (transparent PNGs).
    * `/seq_hud`: Only the data overlays and widgets (transparent PNGs).
    * `/crops_faces`: Individual image crops of every detected face.
* **JSON Only:** Exports analysis data without video rendering.

---

## 🚀 Installation

### Prerequisites
* macOS (Silicon/Intel) or Linux.
* Python 3.10 or higher.

### 1. Clone the Repository
~~~bash
git clone https://github.com/dpvmx/T7MD.git
cd T7DM
~~~

### 2. Setup Virtual Environment
It is highly recommended to use a virtual environment to manage dependencies.

~~~bash
# Create environment
python3 -m venv .venv

# Activate environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
~~~

### 3. Setup Models (Important)
For optimal performance, place your specific model weights in the `models/` directory. The system looks for these exact filenames:

* `models/yolov8m-world.pt` (Medium model for Objects/People)
* `models/yolov8m-face-lindevs.pt` (High-accuracy Face model)

---

## 📖 Usage Guide

You can launch the application using the included script or via terminal.

### Starting the App
**Option A: Quick Launcher (macOS)**
Double-click the `T7MD Vision Pro.command` file.
*(Note: If it doesn't open, run `chmod +x "T7MD Vision Pro.command"` in terminal first).*

**Option B: Terminal**
~~~bash
source .venv/bin/activate
python main.py
~~~

### 🖥️ User Interface Workflow

#### 1. The Header (Import)
* **Load Video:** Click the top-right button to import `.mp4` or `.mov` files.
* **Status:** The filename will appear in green once loaded.

#### 2. The AI Toolbar (Detection Settings)
Located below the video preview.
* **Checkboxes:** Toggle `Faces`, `Persons`, or `Objects` on/off independently.
* **YOLO Input Field:** This is a fluid text box. Type any object names in English, separated by commas.
    * *Example:* `cell phone, backpack, tie`
    * The system will immediately start detecting these items using YOLO-World.
* **Padding:** Adjusts the global safety margin for UI elements.

#### 3. The Dashboard (Visual Customization)
The bottom panel allows you to customize the HUD modules in real-time:

* **BBOXES:** Configure color, thickness, and label size for bounding boxes. The **"Crosshair"** option adds a tactical center target to each detection.
* **STATS:** A floating text panel showing FPS and detection counters. You can move it to any corner (e.g., Top Right, Bottom Left).
* **MINIMAP:** A tactical radar that plots detections relative to the frame center. Useful for "Tech" aesthetic.
* **COLLAGE:** Automatically creates a dynamic stack of cropped faces detected in the current frame.
* **TIMECODE:** Displays the current timestamp and frame count.
* **CUSTOM MSG:** Type any text (e.g., "PROJECT: ALPHA") to display a persistent watermark or label on screen.

#### 4. Export & Rendering
Located at the very bottom.

1.  **Select Profile:**
    * *Final Render:* Good for quick previews or final delivery.
    * *Compositing:* Best for editing. Generates folders with image sequences.
2.  **Select Codec:** H.264 (Standard) or H.265 (High Efficiency).
3.  **Naming:** (Optional) Set a custom output filename.
4.  **RENDER:** Click to start. The terminal will show a detailed progress log:
    > `[RENDER] Frame 00150/02400 (6%) | Detections: Faces=2, Persons=1`

---

## 📂 Project Structure

~~~text
T7DM/
├── core/               # Backend Logic (AI & Engine)
│   ├── video_engine.py     # Rendering Thread
│   ├── yolo_processor.py   # AI Logic & Model Loading
│   └── hud_renderer.py     # Graphics Drawing System
├── gui/                # Frontend (PySide6)
│   ├── main_window.py      # Main Layout
│   └── enhanced_preview.py # Video Player
├── models/             # Local .pt files
├── outputs/            # Render results saved here
└── main.py             # Entry point
~~~

## ⚠️ Troubleshooting

* **"Model not found":** Ensure your `.pt` files are inside the `models/` folder and named exactly as listed in the installation section.
* **PyTorch Warning:** You might see a warning about `weights_only=True`. The application includes a patch to handle this automatically for YOLO models.

---

**Developed by Damián Paz © 2026**