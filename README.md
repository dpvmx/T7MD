# aiMODES
**Artificial Intelligence Motion Detection System**

aiMODES (formerly T7MD) is a high-performance, studio-grade desktop application designed for AI-assisted video analysis, motion tracking, and post-production asset generation. It leverages state-of-the-art models (**YOLO-World**, **YOLO-Face**, and **Depth Anything V2**) to detect objects, generate customizable futuristic HUDs, and export multi-layer sequences ready for professional VFX compositing.

![Version](https://img.shields.io/badge/version-8.4.0-00bcd4?style=for-the-badge&labelColor=151515)
![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge)
![PySide6](https://img.shields.io/badge/GUI-PySide6-41CD52?style=for-the-badge)
![Acceleration](https://img.shields.io/badge/Metal_MPS_CUDA-Enabled-purple?style=for-the-badge)

## Key Features (v8.4.0 Update)

### Native Inspector Architecture
* **QSplitter Layout:** A seamless, OS-native interface that dynamically adapts to both 16:9 (Horizontal) and 9:16 (Vertical) video formats without squashing the preview.
* **Tabbed Dashboard:** Clean, uncrowded controls organized into AI Models, HUD Settings, and Export.

### Advanced VFX Compositing Export
* **Multi-Layer Rendering:** Exports synchronized, transparent PNG sequences for independent post-production control.
* **Separated BBoxes:** Automatically separates Face, Person, and Object bounding boxes into distinct folders.
* **Modular HUD:** Renders isolated sequences for Minimap, Advanced Stats, Timecode, Custom Messages, and Collage.
* **Automated Face Cropping:** Generates high-quality JPG crops of detected faces frame-by-frame.

### Constellation Link Module
* **Topological Overlays:** Generates network-style lines connecting detected targets.
* **Routing Algorithms:** Choose between Mesh (proximity triangulation), Sequential (x-axis routing), or Hub (center fixation).
* **Bezier Curves:** Mathematical quadratic Bezier interpolation for smooth, futuristic data links.

### Deep Tech Analysis
* **Precision Latency Tracking:** Real-time hardware performance monitoring with conditional visual alerts (red text if processing exceeds 100ms per frame).
* **Hardware Auto-Detection:** Seamlessly utilizes Apple Silicon (Metal/MPS) or Nvidia (CUDA) for maximum inference speed.
* **Z-Depth Pass:** Integrates Depth Anything V2 for cinematic depth map generation.

## Installation

**Prerequisites:** macOS (Silicon Recommended) or Linux/Windows, Python 3.10+, and FFmpeg.

**1. Clone the Repository**
```bash
git clone https://github.com/dpvmx/aiMODES.git
cd aiMODES
```

**2. Setup Virtual Environment**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**3. Setup Models**
Place your weights in the `models/` directory:
* `models/yolov8m-world.pt`
* `models/yolov8m-face-lindevs.pt`
*(Depth Anything V2 will download automatically on first run).*

## Usage Workflow
1. **Import:** Load any `.mp4` or `.mov` file.
2. **AI Models:** Select targets (Faces, Persons) or type custom open-vocabulary tags (e.g., "laptop, coffee cup").
3. **HUD Settings:** Customize colors, padding, and layout for BBoxes, Constellation links, and Data Panels.
4. **Export:** Select "Compositing Ready" to generate separated VFX assets, or "Final Render" for a baked companion video.
