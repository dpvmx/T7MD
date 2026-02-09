# T7MD 👁️ Motion Detection Software

**Professional Computer Vision & HUD Generation Studio**

T7MD Vision Pro is a high-performance desktop application designed for AI-assisted video analysis and post-production. It leverages state-of-the-art models (**YOLO-World**, **YOLO-Face**, and **Depth Anything V2**) to detect objects, generate customizable futuristic HUDs, and create cinematic depth maps.

![Interfaz T7MD Vision Pro](assets/demo_preview.png)

![Version](https://img.shields.io/badge/version-8.2.0-00bcd4?style=for-the-badge&labelColor=151515)
![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge)
![PySide6](https://img.shields.io/badge/GUI-PySide6-41CD52?style=for-the-badge)
![Acceleration](https://img.shields.io/badge/Metal_MPS-Enabled-purple?style=for-the-badge)

## ✨ Key Features

### 🌊 Depth Analysis (New in v8.0+)
* **Depth Anything V2 Integration:** Generates high-fidelity Z-Depth maps (grayscale) for every frame.
* **Anti-Flicker Technology:** Implements **Temporal Smoothing** (Exponential Moving Average) to eliminate strobe effects in depth maps, ensuring distinct, stable planes for compositing.
* **Cinematic Export:** Automatically exports a secondary video file (`_depth.mp4`) ready for Lens Blur or Fog effects in post-production.

### 🧠 Advanced AI Engine
* **Unified Detection Logic:** Seamlessly blends **YOLO-World** (Open Vocabulary) with specific class detection. You can activate "Persons" and type specific objects simultaneously without conflict.
* **Dual-Model Architecture:** Runs **YOLO-World** and **YOLO-Face** simultaneously for maximum accuracy.
* **Open Vocabulary:** Detect any object by simply typing its name (e.g., "coffee cup, laptop, cat")—no retraining required.

### 🎨 Studio UI (V8)
* **Cyber Lime & Cyan Aesthetic:** Professional dark mode interface with high-contrast accents (`#BCFF4E` for UI, `#00BCD4` for Depth features).
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
* macOS (Silicon Recommended) or Linux/Windows.
* Python 3.10 or higher.
* **FFmpeg** installed on your system.

### 1. Clone the Repository
```bash
git clone [https://github.com/dpvmx/T7MD.git](https://github.com/dpvmx/T7MD.git)
cd T7DM
```

### 2. Setup Virtual Environment
It is highly recommended to use a virtual environment to manage dependencies.

```bash
# Create environment
python3 -m venv .venv

# Activate environment
source .venv/bin/activate

# Install dependencies (Transformers is required for Depth)
pip install -r requirements.txt
pip install transformers
```

### 3. Setup Models (Automatic & Manual)
* **Depth Model:** The system will automatically download `Depth-Anything-V2-Small` (approx 100MB) on the first run.
* **YOLO Models:** Place your specific model weights in the `models/` directory:
    * `models/yolov8m-world.pt`
    * `models/yolov8m-face-lindevs.pt`

---

## 📖 Usage Guide

### Starting the App
**Option A: Quick Launcher (macOS)**
Double-click the `T7MD Vision Pro.command` file.

**Option B: Terminal**
```bash
source .venv/bin/activate
python main.py
```

### 🖥️ User Interface Workflow

#### 1. The Header (Import)
* **Load Video:** Click the top-right button to import `.mp4` or `.mov` files.

#### 2. The AI Toolbar (Detection Settings)
Located below the video preview.
* **Checkboxes:** Toggle `Faces`, `Persons`, or `Objects`.
* **Depth Checkbox (Cyan):** Activates the **Z-Depth Pass**.
    * *Note:* This will increase processing time but generates a companion `_depth.mp4` file.
* **YOLO Input Field:** Type any object names in English, separated by commas.
    * *Example:* `cell phone, backpack, tie`

#### 3. The Dashboard (Visual Customization)
The bottom panel allows you to customize the HUD modules in real-time:
* **BBOXES:** Configure color, thickness, and label size.
* **STATS:** A floating text panel showing FPS and detection counters.
* **MINIMAP:** A tactical radar that plots detections relative to the frame center.
* **COLLAGE:** Automatically creates a dynamic stack of cropped faces.
* **TIMECODE:** Displays the current timestamp.

#### 4. Export & Rendering
1.  **Select Profile:** (Final Render / Compositing / JSON Only).
2.  **Select Codec:** H.264 or H.265.
3.  **RENDER:** Click to start.

---

## ⚡️ Performance & Hardware Acceleration

**T7MD v8.2** is optimized for Apple Silicon (M1/M2/M3).
* **Mac Users:** The engine automatically detects **Metal Performance Shaders (MPS)**.
    * **YOLO:** Accelerated via MPS.
    * **Depth:** Accelerated via MPS.
* **Memory Management:** Includes failsafes (`.detach().cpu()`) to prevent GPU memory overflows during the drawing phase.

### ⚠️ Current Status (v8.2)
* **Detection Mode:** The system currently performs **Object Detection** (drawing bounding boxes per frame).
* **Tracking (IDs):** Persistent ID Tracking (assigning unique numbers to people) is temporarily disabled to ensure stability with the new Depth engine.
* **Depth Generation:** Fully functional with temporal smoothing enabled (`alpha=0.8`).

---

## 🔌 Integration with Adobe After Effects

This tool features a CEP panel for After Effects that allows analyzing video directly from the timeline.

### 🛠️ Panel Installation
1.  Copy the `T7MD_Panel` folder to:
    * **Mac:** `~/Library/Application Support/Adobe/CEP/extensions/`
    * **Win:** `C:\Program Files (x86)\Common Files\Adobe\CEP\extensions\`
2.  Enable debug mode in terminal:
    ```bash
    defaults write com.adobe.CSXS.15 PlayerDebugMode 1
    ```

---

**Developed by Damián Paz © 2026**