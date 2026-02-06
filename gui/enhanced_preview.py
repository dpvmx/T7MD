"""
Preview de video T7MD - UI V3.4
Fix: Eliminado botón loop (bucle infinito implícito).
"""

from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QPushButton, QHBoxLayout, QSizePolicy,
    QSlider, QStyle, QFrame
)
from PySide6.QtCore import Qt, QTimer, QThread, Signal, QObject
from PySide6.QtGui import QPixmap, QImage
import cv2
import numpy as np
from core.yolo_processor import YOLOProcessor
from gui.styles import ACCENT_COLOR 

class DetectionWorker(QObject):
    detection_done = Signal(np.ndarray, dict)
    
    def __init__(self, config_manager=None):
        super().__init__()
        self.processor = YOLOProcessor(config_manager)
        self.config_manager = config_manager
        self.active = False
    
    def update_config(self, config_manager):
        self.config_manager = config_manager
        self.processor.update_config(config_manager)

    def process_frame(self, frame: np.ndarray, frame_number: int = 0, fps: float = 30.0):
        if not self.active or frame is None:
            self.detection_done.emit(frame, {})
            return
        try:
            detections = self.processor.detect_frame(
                frame, 
                self.config_manager.get("models.use_faces", True),
                self.config_manager.get("models.use_persons", True),
                self.config_manager.get("models.use_objects", True),
                self.config_manager.get("models.custom_classes", [])
            )
            processed_frame = self.processor.draw_detections(frame, detections, frame_number, fps)
            self.detection_done.emit(processed_frame, detections)
        except Exception:
            self.detection_done.emit(frame, {})

class EnhancedVideoPreview(QWidget):
    def __init__(self, config_manager=None):
        super().__init__()
        self.config = config_manager
        self.cap = None
        self.current_raw_frame = None
        self.current_processed_frame = None
        
        self.is_playing = False
        self.total_frames = 0
        self.current_frame_idx = 0
        self.fps = 30.0
        self.playback_direction = 1
        self.loop_mode = "loop" # Default loop ON
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.next_frame)

        self.setup_ui()
        self.setup_workers()
        
    def setup_ui(self):
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 1. Video
        self.lbl_frame = QLabel()
        self.lbl_frame.setAlignment(Qt.AlignCenter)
        self.lbl_frame.setStyleSheet("background-color: #000;")
        self.lbl_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.lbl_frame)
        
        # 2. Control Bar
        control_bar = QFrame()
        control_bar.setStyleSheet("background-color: #1a1a1a; border-top: 1px solid #333;")
        control_bar.setFixedHeight(50)
        
        bar_layout = QHBoxLayout(control_bar)
        bar_layout.setContentsMargins(10, 5, 10, 5)
        bar_layout.setSpacing(10)
        
        # Play Btn
        self.btn_play = QPushButton("▶")
        self.btn_play.setFixedSize(30, 30)
        self.btn_play.setStyleSheet("color: white; border: 1px solid #555; border-radius: 4px;")
        self.btn_play.clicked.connect(self.toggle_playback)
        bar_layout.addWidget(self.btn_play)
        
        # Timeline
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setStyleSheet("""
            QSlider::groove:horizontal { height: 4px; background: #333; border-radius: 2px; }
            QSlider::handle:horizontal { background: #888; width: 12px; margin: -4px 0; border-radius: 6px; }
            QSlider::handle:horizontal:hover { background: #fff; }
        """)
        self.slider.sliderPressed.connect(self.on_slider_pressed)
        self.slider.sliderReleased.connect(self.on_slider_released)
        self.slider.valueChanged.connect(self.on_slider_moved)
        bar_layout.addWidget(self.slider)
        
        self.lbl_time = QLabel("00:00 / 00:00")
        self.lbl_time.setStyleSheet("color: #888; font-family: monospace; font-size: 11px;")
        bar_layout.addWidget(self.lbl_time)
        
        line = QFrame()
        line.setFrameShape(QFrame.VLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("color: #333;")
        bar_layout.addWidget(line)
        
        self.btn_ai = QPushButton("ANÁLISIS")
        self.btn_ai.setCheckable(True)
        self.btn_ai.setFixedWidth(100)
        self.btn_ai.setFixedHeight(30)
        self.btn_ai.setStyleSheet("""
            QPushButton { background-color: #8a1c1c; color: white; font-weight: bold; border-radius: 4px; border: none; }
            QPushButton:checked { background-color: #d32f2f; border: 2px solid #ff5555; }
            QPushButton:hover { background-color: #a32222; }
        """)
        self.btn_ai.toggled.connect(self.toggle_ai)
        bar_layout.addWidget(self.btn_ai)
        
        layout.addWidget(control_bar)

    def setup_workers(self):
        self.detection_thread = QThread()
        self.detection_worker = DetectionWorker(self.config)
        self.detection_worker.moveToThread(self.detection_thread)
        self.detection_worker.detection_done.connect(self.on_detection_done)
        self.detection_thread.start()

    def update_config_live(self):
        self.detection_worker.update_config(self.config)

    def load_video(self, path):
        self.cap = cv2.VideoCapture(path)
        if self.cap.isOpened():
            self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 30.0
            self.slider.setRange(0, self.total_frames - 1)
            self.current_frame_idx = 0
            self.update_frame(0)
            self.timer.setInterval(int(1000/self.fps))

    def next_frame(self):
        nxt = self.current_frame_idx + self.playback_direction
        if nxt >= self.total_frames:
            if self.loop_mode == "loop":
                nxt = 0
            else:
                self.pause_playback()
                return
        self.current_frame_idx = nxt
        self.update_frame(nxt)
        self.slider.blockSignals(True)
        self.slider.setValue(nxt)
        self.slider.blockSignals(False)

    def update_frame(self, idx):
        if not self.cap: return
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = self.cap.read()
        if ret:
            self.current_raw_frame = frame
            if self.btn_ai.isChecked():
                self.worker_process(frame)
            else:
                self.display(frame)
            
            cur = int(idx/self.fps)
            tot = int(self.total_frames/self.fps)
            self.lbl_time.setText(f"{cur//60:02}:{cur%60:02} / {tot//60:02}:{tot%60:02}")

    def worker_process(self, frame):
        self.detection_worker.process_frame(frame, self.current_frame_idx, self.fps)

    def on_detection_done(self, processed, dets):
        self.current_processed_frame = processed
        self.display(processed)

    def display(self, frame):
        if frame is None: return
        h, w, ch = frame.shape
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        qimg = QImage(rgb.data, w, h, ch*w, QImage.Format_RGB888)
        self.lbl_frame.setPixmap(QPixmap.fromImage(qimg).scaled(
            self.lbl_frame.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        ))

    def resizeEvent(self, e):
        if self.btn_ai.isChecked() and self.current_processed_frame is not None:
            self.display(self.current_processed_frame)
        elif self.current_raw_frame is not None:
            self.display(self.current_raw_frame)
        super().resizeEvent(e)

    def toggle_playback(self):
        if self.is_playing:
            self.pause_playback()
        else:
            self.start_playback()

    def start_playback(self):
        self.is_playing = True
        self.timer.start()
        self.btn_play.setText("⏸")

    def pause_playback(self):
        self.is_playing = False
        self.timer.stop()
        self.btn_play.setText("▶")
    
    def toggle_ai(self, active):
        self.detection_worker.active = active
        if self.current_raw_frame is not None:
            if active:
                self.worker_process(self.current_raw_frame)
            else:
                self.display(self.current_raw_frame)

    def on_slider_pressed(self):
        self.was_p = self.is_playing
        self.pause_playback()

    def on_slider_released(self): 
        if getattr(self, 'was_p', False):
            self.start_playback()

    def on_slider_moved(self, v):
        self.current_frame_idx = v
        self.update_frame(v)
    
    def force_refresh(self):
        if self.current_raw_frame is not None and self.btn_ai.isChecked():
            self.worker_process(self.current_raw_frame)
            
    def close(self):
        self.timer.stop()
        self.detection_thread.quit()
        if self.cap:
            self.cap.release()