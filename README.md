# MODESYS
**Motion Detection System by Triplesiete**

MODESYS is a high-performance, studio-grade desktop application designed for AI-assisted video analysis, motion tracking, and post-production asset generation. It leverages state-of-the-art models (**YOLO-World**, **YOLO-Face**, and **Depth Anything V2**) to detect objects, generate customizable futuristic HUDs, and export multi-layer sequences ready for professional VFX compositing.

![Version](https://img.shields.io/badge/version-8.4.1-00bcd4?style=for-the-badge&labelColor=151515)
![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge)
![PySide6](https://img.shields.io/badge/GUI-PySide6-41CD52?style=for-the-badge)
![Acceleration](https://img.shields.io/badge/Metal_MPS_CUDA-Enabled-purple?style=for-the-badge)

## Key Features

### Advanced VFX Compositing Export
* **Multi-Layer Rendering:** Exports synchronized, transparent PNG sequences for independent post-production control.
* **Separated BBoxes:** Automatically separates Face, Person, and Object bounding boxes into distinct folders.
* **Modular HUD:** Renders isolated sequences for Minimap, Advanced Stats, Timecode, Custom Messages, and Collage.
* **Automated Face Cropping:** Generates high-quality JPG crops of detected faces frame-by-frame.

### Constellation Link Module
* **Topological Overlays:** Generates network-style lines connecting detected targets.
* **Routing Algorithms:** Choose between Mesh (proximity triangulation), Sequential (x-axis routing), or Hub (center fixation).
* **Bezier Curves & Dynamic Nodes:** Mathematical quadratic Bezier interpolation with UI-controlled geometric node scaling (0-200px) for futuristic data links.

### Native Inspector Architecture
* **Progressive Disclosure UI:** Collapsible HUD configuration panels for a clean, uncrowded user experience.
* **QSplitter Layout:** A seamless, OS-native interface that dynamically adapts to both 16:9 and 9:16 video formats without squashing the preview.
* **Tabbed Dashboard:** Organized controls divided into AI Models, HUD Settings, and Export configurations.

### Deep Tech Analysis
* **High-Density Crowd Tracking:** Dynamic AI Sensitivity sliders with engine limits expanded (1000 max detections) to handle massive crowds.
* **Precision Latency Tracking:** Real-time hardware performance monitoring with conditional visual alerts (red text if processing exceeds 100ms per frame).
* **Hardware Auto-Detection:** Seamlessly utilizes Apple Silicon (Metal/MPS) or Nvidia (CUDA) for maximum inference speed.
* **Z-Depth Pass:** Integrates Depth Anything V2 for cinematic depth map generation.

## Installation

**Prerequisites:** macOS (Apple Silicon Recommended) or Linux/Windows, Python 3.10+, and FFmpeg.

### Automated Setup (macOS/Linux)
Simply run the included installer. It will handle the virtual environment, download the optimized dependencies, and fetch the necessary AI models:
```bash
chmod +x install_modesys.sh
./install_modesys.sh
```

### Manual Setup
```Bash
git clone [https://github.com/dpvmx/MODESYS.git](https://github.com/dpvmx/MODESYS.git)
cd MODESYS
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
(Place your YOLO weights in the models/ directory. Depth Anything V2 will download automatically on the first run).
```
### Usage Workflow
* **Launch:** Run Launch MODESYS.command (or python main.py).

* **Import:** Load any .mp4 or .mov file.

* **AI Models:** Select targets (Faces, Persons) or type custom open-vocabulary tags (e.g., "laptop, coffee cup"). Adjust the sensitivity sliders for crowd density.

## HUD Settings: Customize colors, padding, and layout for BBoxes, Constellation links, and Data Panels.

* **Export:** Select "Compositing Ready" to generate separated VFX assets, or "Final Render" for a baked companion video.