"""
MODESYS - Motion Detection System
Architecture: Native Splitter UI with Inspector Panel
Updates:
- Feat: Rebranding to MODESYS. Minimalist header.
- Feat: Added UI Sliders for dynamic AI detection sensitivity.
- Feat: Collapsible HUD modules (Progressive Disclosure UX).
- Feat: Dynamic slider for Constellation Node Size (Range expanded to 200px).
"""

import os
import sys
import subprocess
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QComboBox, QSlider, QCheckBox,
    QGroupBox, QStatusBar, QFileDialog, QMessageBox, QLineEdit, 
    QFrame, QColorDialog, QScrollArea, QSizePolicy, QPlainTextEdit,
    QSplitter, QTabWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QCloseEvent, QFont

from gui.enhanced_preview import EnhancedVideoPreview as VideoPreviewWidget
from core.config_manager import ConfigManager
from core.video_engine import VideoEngine

class ColorBtn(QPushButton):
    def __init__(self, hex_col, cb):
        super().__init__()
        self.setFixedSize(40, 20)
        self.hex = hex_col
        self.cb = cb
        self.upd()
        self.clicked.connect(self.pick)
    
    def upd(self):
        self.setStyleSheet(f"background-color: {self.hex}; border: 1px solid palette(mid); border-radius: 4px;")
    
    def pick(self):
        c = QColorDialog.getColor(QColor(self.hex), self, "Select Color")
        if c.isValid():
            self.hex = c.name()
            self.upd()
            self.cb(self.hex)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = ConfigManager()
        self.engine = VideoEngine(self.config)
        self.setup_ui()
        self.setup_conns()
    
    def setup_ui(self):
        self.setWindowTitle("MODESYS - v8.4.1")
        self.setMinimumSize(1280, 800)
        
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        header = self.mk_header()
        main_layout.addWidget(header, 0) 
        
        self.splitter = QSplitter(Qt.Horizontal)
        
        video_container = QWidget()
        video_layout = QVBoxLayout(video_container)
        video_layout.setContentsMargins(0, 0, 0, 0)
        self.preview = VideoPreviewWidget(self.config)
        video_layout.addWidget(self.preview)
        
        self.splitter.addWidget(video_container)
        
        self.tabs = QTabWidget()
        self.tabs.setMinimumWidth(380)
        self.tabs.setMaximumWidth(450)
        
        self.tabs.addTab(self.mk_tab_ai_models(), "AI Models")
        self.tabs.addTab(self.mk_tab_hud_settings(), "HUD Settings")
        self.tabs.addTab(self.mk_tab_export(), "Export")
        
        self.splitter.addWidget(self.tabs)
        
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 0)
        
        main_layout.addWidget(self.splitter, 1) 
        
        self.sb = QStatusBar()
        self.setStatusBar(self.sb)
        self.sb.showMessage("Ready")

    def mk_header(self):
        header_widget = QWidget()
        header_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        layout = QHBoxLayout(header_widget)
        layout.setContentsMargins(5, 5, 5, 5)
        
        title_layout = QVBoxLayout()
        title_layout.setSpacing(0)
        
        lbl_title = QLabel("MODESYS")
        font_title = QFont()
        font_title.setPointSize(24)
        font_title.setBold(True)
        lbl_title.setFont(font_title)
        
        title_layout.addWidget(lbl_title)
        
        layout.addLayout(title_layout)
        layout.addStretch()
        
        self.lbl_vid_name = QLabel("No File Loaded")
        self.lbl_vid_name.setStyleSheet("color: palette(dark);")
        
        btn_open = QPushButton("Open Video")
        btn_open.setMinimumWidth(120)
        btn_open.clicked.connect(self.load_video)
        
        layout.addWidget(self.lbl_vid_name)
        layout.addSpacing(15)
        layout.addWidget(btn_open)
        
        return header_widget

    def mk_tab_ai_models(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(15)
        
        grp_detect = QGroupBox("Target Detection")
        lay_detect = QVBoxLayout(grp_detect)
        
        lay_detect.addWidget(self._chk("Detect Faces", "models.use_faces"))
        lay_detect.addWidget(self._chk("Detect Persons", "models.use_persons"))
        lay_detect.addWidget(self._chk("Detect Objects", "models.use_objects"))
        
        lbl_yolo = QLabel("Custom YOLO Targets (comma separated):")
        lbl_yolo.setStyleSheet("color: palette(dark); margin-top: 10px;")
        
        self.txt_yo = QLineEdit()
        self.txt_yo.setPlaceholderText("e.g. cell phone, laptop, backpack")
        self.txt_yo.setText(",".join(self.config.get("models.custom_classes", [])))
        self.txt_yo.textChanged.connect(self.upd_yolo)
        
        self.lbl_yolo_tags = QLabel()
        self.lbl_yolo_tags.setStyleSheet("color: palette(dark); font-size: 11px;")
        self.upd_yolo(self.txt_yo.text())
        
        lay_detect.addWidget(lbl_yolo)
        lay_detect.addWidget(self.txt_yo)
        lay_detect.addWidget(self.lbl_yolo_tags)
        
        layout.addWidget(grp_detect)

        grp_sens = QGroupBox("AI Sensitivity (Confidence)")
        lay_sens = QVBoxLayout(grp_sens)
        lay_sens.addWidget(self._lbl("Face Detection Sensitivity:"))
        lay_sens.addWidget(self._slider(10, 100, int(self.config.get("models.face_confidence", 0.4) * 100), lambda v: self.upd("models.face_confidence", v / 100.0), "%"))
        lay_sens.addWidget(self._lbl("Person & Object Sensitivity:"))
        lay_sens.addWidget(self._slider(10, 100, int(self.config.get("models.person_confidence", 0.25) * 100), lambda v: self.upd("models.person_confidence", v / 100.0), "%"))
        layout.addWidget(grp_sens)
        
        grp_fx = QGroupBox("Depth Analysis")
        lay_fx = QVBoxLayout(grp_fx)
        
        chk_depth = self._chk("Generate Z-Depth Pass", "models.use_depth")
        lay_fx.addWidget(chk_depth)
        
        self.lbl_depth_warn = QLabel("Warning: Depth generation increases render time (~2x)")
        self.lbl_depth_warn.setStyleSheet("color: palette(dark); font-size: 11px;")
        self.lbl_depth_warn.setVisible(self.config.get("models.use_depth", False))
        
        def toggle_depth_warn(v):
            self.lbl_depth_warn.setVisible(v)
            self.upd("models.use_depth", v)
            
        chk_depth.toggled.disconnect()
        chk_depth.toggled.connect(toggle_depth_warn)
        lay_fx.addWidget(self.lbl_depth_warn)
        
        layout.addWidget(grp_fx)
        layout.addStretch()
        
        scroll.setWidget(content)
        return scroll

    def mk_tab_hud_settings(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(15)
        
        grp_global = QGroupBox("Global Layout")
        lay_global = QVBoxLayout(grp_global)
        lbl_pad = QLabel("Screen Padding:")
        lbl_pad.setStyleSheet("color: palette(dark);")
        lay_global.addWidget(lbl_pad)
        lay_global.addWidget(self._slider(0, 200, self.config.get("style.global_margin"), lambda v: self.upd("style.global_margin", v), "px"))
        layout.addWidget(grp_global)

        layout.addWidget(self.mk_group_constellation())
        layout.addWidget(self.mk_group_bboxes())
        layout.addWidget(self.mk_group_stats())
        layout.addWidget(self.mk_group_minimap())
        layout.addWidget(self.mk_group_collage())
        layout.addWidget(self.mk_group_timecode())
        layout.addWidget(self.mk_group_msg())
        
        layout.addStretch()
        scroll.setWidget(content)
        return scroll

    # --- CONTENEDORES COLAPSABLES ---

    def mk_group_constellation(self):
        group = QGroupBox("Constellation Link")
        main_lay = QVBoxLayout(group)
        k = "modules.constellation"
        
        chk_enable = self._chk("Enable Module", f"{k}.enabled")
        main_lay.addWidget(chk_enable)

        # Contenedor que colapsará
        content = QWidget()
        layout = QGridLayout(content)
        layout.setContentsMargins(0, 10, 0, 0)
        
        layout.addWidget(self._lbl("Link Style"), 0, 0)
        combo_style = QComboBox()
        for t, d in [("Mesh (Proximity)", "mesh"), ("Sequential (X-Axis)", "sequential"), ("Hub (Center Fix)", "hub")]:
            combo_style.addItem(t, d)
        idx_style = combo_style.findData(self.config.get(f"{k}.style", "mesh"))
        if idx_style >= 0: combo_style.setCurrentIndex(idx_style)
        combo_style.currentIndexChanged.connect(lambda idx, cb=combo_style: self.upd(f"{k}.style", cb.itemData(idx)))
        layout.addWidget(combo_style, 0, 1)

        layout.addWidget(self._lbl("Targets"), 1, 0)
        combo_tgt = QComboBox()
        for t, d in [("All Detected", ["face", "person", "object"]), ("Faces Only", ["face"]), ("Persons Only", ["person"]), ("Objects Only", ["object"])]:
            combo_tgt.addItem(t, d)
        
        current_tgt = self.config.get(f"{k}.targets", ["face", "person", "object"])
        for i in range(combo_tgt.count()):
            if combo_tgt.itemData(i) == current_tgt:
                combo_tgt.setCurrentIndex(i)
                break
        
        combo_tgt.currentIndexChanged.connect(lambda idx, cb=combo_tgt: self.upd(f"{k}.targets", cb.itemData(idx)))
        layout.addWidget(combo_tgt, 1, 1)

        layout.addWidget(self._lbl("Line Shape"), 2, 0)
        combo_shape = QComboBox()
        for t, d in [("Straight Line", "straight"), ("Bezier Curve", "curved")]:
            combo_shape.addItem(t, d)
        idx_shape = combo_shape.findData(self.config.get(f"{k}.line_shape", "straight"))
        if idx_shape >= 0: combo_shape.setCurrentIndex(idx_shape)
        combo_shape.currentIndexChanged.connect(lambda idx, cb=combo_shape: self.upd(f"{k}.line_shape", cb.itemData(idx)))
        layout.addWidget(combo_shape, 2, 1)
        
        layout.addWidget(self._lbl("Line Color"), 3, 0)
        layout.addWidget(ColorBtn(self.config.get(f"{k}.color", "#BCFF4E"), lambda c: self.upd(f"{k}.color", c)), 3, 1)
        
        layout.addWidget(self._lbl("Thickness"), 4, 0)
        layout.addWidget(self._slider(1, 10, self.config.get(f"{k}.thick", 1), lambda v: self.upd(f"{k}.thick", v), "px"), 4, 1)
        
        layout.addWidget(self._lbl("Opacity"), 5, 0)
        layout.addWidget(self._slider(0, 100, self.config.get(f"{k}.opacity", 80), lambda v: self.upd(f"{k}.opacity", v), "%"), 5, 1)

        # --- NUEVO SLIDER: TAMAÑO DE NODO (Rango 0 - 200) ---
        layout.addWidget(self._lbl("Node Size"), 6, 0)
        layout.addWidget(self._slider(0, 200, self.config.get(f"{k}.node_size", 4), lambda v: self.upd(f"{k}.node_size", v), "px"), 6, 1)
        # ------------------------------------

        main_lay.addWidget(content)
        
        # Lógica de Colapso
        content.setVisible(chk_enable.isChecked())
        chk_enable.toggled.connect(content.setVisible)

        return group

    def mk_group_bboxes(self):
        group = QGroupBox("Bounding Boxes")
        main_lay = QVBoxLayout(group)
        k = "modules.bboxes"
        
        chk_enable = self._chk("Enable Module", f"{k}.enabled")
        main_lay.addWidget(chk_enable)

        content = QWidget()
        layout = QGridLayout(content)
        layout.setContentsMargins(0, 10, 0, 0)
        
        layout.addWidget(self._lbl("Persons"), 0, 0)
        layout.addWidget(ColorBtn(self.config.get(f"{k}.person_color"), lambda c: self.upd(f"{k}.person_color", c)), 0, 1)
        layout.addWidget(self._slider(1, 10, self.config.get(f"{k}.person_thick"), lambda v: self.upd(f"{k}.person_thick", v), "px"), 0, 2)
        
        layout.addWidget(self._lbl("Faces"), 1, 0)
        layout.addWidget(ColorBtn(self.config.get(f"{k}.face_color"), lambda c: self.upd(f"{k}.face_color", c)), 1, 1)
        layout.addWidget(self._slider(1, 10, self.config.get(f"{k}.face_thick"), lambda v: self.upd(f"{k}.face_thick", v), "px"), 1, 2)
        
        layout.addWidget(self._lbl("Objects"), 2, 0)
        layout.addWidget(ColorBtn(self.config.get(f"{k}.object_color"), lambda c: self.upd(f"{k}.object_color", c)), 2, 1)
        layout.addWidget(self._slider(1, 10, self.config.get(f"{k}.object_thick"), lambda v: self.upd(f"{k}.object_thick", v), "px"), 2, 2)
        
        layout.addWidget(self._lbl("Label Size"), 3, 0)
        layout.addWidget(self._slider(10, 200, self.config.get(f"{k}.label_scale"), lambda v: self.upd(f"{k}.label_scale", v), "%"), 3, 1, 1, 2)
        
        layout.addWidget(self._lbl("Text Color"), 4, 0)
        layout.addWidget(ColorBtn(self.config.get(f"{k}.label_text_color"), lambda c: self.upd(f"{k}.label_text_color", c)), 4, 1)
        
        layout.addWidget(self._chk("Tactical Crosshair", f"{k}.show_crosshair"), 5, 0, 1, 3)
        
        main_lay.addWidget(content)
        content.setVisible(chk_enable.isChecked())
        chk_enable.toggled.connect(content.setVisible)

        return group

    def mk_group_stats(self):
        group = QGroupBox("Data Panel")
        main_lay = QVBoxLayout(group)
        k = "modules.stats"
        
        chk_enable = self._chk("Enable Module", f"{k}.enabled")
        main_lay.addWidget(chk_enable)

        content = QWidget()
        layout = QGridLayout(content)
        layout.setContentsMargins(0, 10, 0, 0)
        
        layout.addWidget(self._lbl("Title:"), 0, 0)
        txt_header = QLineEdit()
        txt_header.setText(self.config.get(f"{k}.header_text"))
        txt_header.textChanged.connect(lambda x: self.upd(f"{k}.header_text", x))
        layout.addWidget(txt_header, 0, 1)
        
        layout.addWidget(self._lbl("Position"), 1, 0)
        layout.addWidget(self._pos_combo(f"{k}.position"), 1, 1)
        
        layout.addWidget(self._lbl("Size"), 2, 0)
        layout.addWidget(self._slider(10, 200, self.config.get(f"{k}.scale"), lambda v: self.upd(f"{k}.scale", v), "%"), 2, 1)
        
        layout.addWidget(self._lbl("Text Color"), 3, 0)
        layout.addWidget(ColorBtn(self.config.get(f"{k}.text_color"), lambda c: self.upd(f"{k}.text_color", c)), 3, 1)
        
        layout.addWidget(self._lbl("Background"), 4, 0)
        layout.addWidget(ColorBtn(self.config.get(f"{k}.bg_color"), lambda c: self.upd(f"{k}.bg_color", c)), 4, 1)
        
        layout.addWidget(self._lbl("Opacity"), 5, 0)
        layout.addWidget(self._slider(0, 100, self.config.get(f"{k}.bg_opacity"), lambda v: self.upd(f"{k}.bg_opacity", v), "%"), 5, 1)
        
        main_lay.addWidget(content)
        content.setVisible(chk_enable.isChecked())
        chk_enable.toggled.connect(content.setVisible)

        return group

    def mk_group_minimap(self):
        group = QGroupBox("Minimap Radar")
        main_lay = QVBoxLayout(group)
        k = "modules.minimap"
        
        chk_enable = self._chk("Enable Module", f"{k}.enabled")
        main_lay.addWidget(chk_enable)

        content = QWidget()
        layout = QGridLayout(content)
        layout.setContentsMargins(0, 10, 0, 0)
        
        layout.addWidget(self._lbl("Position"), 0, 0)
        layout.addWidget(self._pos_combo(f"{k}.position"), 0, 1)
        
        layout.addWidget(self._lbl("Size"), 1, 0)
        layout.addWidget(self._slider(50, 200, self.config.get(f"{k}.scale"), lambda v: self.upd(f"{k}.scale", v), "%"), 1, 1)
        
        layout.addWidget(self._lbl("Border Width"), 2, 0)
        layout.addWidget(self._slider(0, 10, self.config.get(f"{k}.border_thick"), lambda v: self.upd(f"{k}.border_thick", v), "px"), 2, 1)
        
        layout.addWidget(self._lbl("Border Color"), 3, 0)
        layout.addWidget(ColorBtn(self.config.get(f"{k}.border_color"), lambda c: self.upd(f"{k}.border_color", c)), 3, 1)
        
        layout.addWidget(self._lbl("Dot Size"), 4, 0)
        layout.addWidget(self._slider(1, 10, self.config.get(f"{k}.dot_size"), lambda v: self.upd(f"{k}.dot_size", v), "px"), 4, 1)
        
        layout.addWidget(self._lbl("Background"), 5, 0)
        layout.addWidget(ColorBtn(self.config.get(f"{k}.bg_color"), lambda c: self.upd(f"{k}.bg_color", c)), 5, 1)
        
        layout.addWidget(self._lbl("Opacity"), 6, 0)
        layout.addWidget(self._slider(0, 100, self.config.get(f"{k}.bg_opacity"), lambda v: self.upd(f"{k}.bg_opacity", v), "%"), 6, 1)
        
        main_lay.addWidget(content)
        content.setVisible(chk_enable.isChecked())
        chk_enable.toggled.connect(content.setVisible)

        return group

    def mk_group_collage(self):
        group = QGroupBox("Face Collage")
        main_lay = QVBoxLayout(group)
        k = "modules.collage"
        
        chk_enable = self._chk("Enable Module", f"{k}.enabled")
        main_lay.addWidget(chk_enable)

        content = QWidget()
        layout = QGridLayout(content)
        layout.setContentsMargins(0, 10, 0, 0)
        
        layout.addWidget(self._lbl("Position"), 0, 0)
        layout.addWidget(self._pos_combo(f"{k}.position"), 0, 1)
        
        layout.addWidget(self._lbl("Thumb Size"), 1, 0)
        layout.addWidget(self._slider(5, 30, self.config.get(f"{k}.thumb_size_pct"), lambda v: self.upd(f"{k}.thumb_size_pct", v), "%"), 1, 1)
        
        layout.addWidget(self._lbl("Border Width"), 2, 0)
        layout.addWidget(self._slider(0, 10, self.config.get(f"{k}.border_thick"), lambda v: self.upd(f"{k}.border_thick", v), "px"), 2, 1)
        
        layout.addWidget(self._lbl("Border Color"), 3, 0)
        layout.addWidget(ColorBtn(self.config.get(f"{k}.border_color"), lambda c: self.upd(f"{k}.border_color", c)), 3, 1)
        
        layout.addWidget(self._lbl("Spacing Gap"), 4, 0)
        layout.addWidget(self._slider(0, 50, self.config.get(f"{k}.gap_pct"), lambda v: self.upd(f"{k}.gap_pct", v), "%"), 4, 1)
        
        layout.addWidget(self._lbl("Opacity"), 5, 0)
        layout.addWidget(self._slider(0, 100, self.config.get(f"{k}.opacity"), lambda v: self.upd(f"{k}.opacity", v), "%"), 5, 1)
        
        main_lay.addWidget(content)
        content.setVisible(chk_enable.isChecked())
        chk_enable.toggled.connect(content.setVisible)

        return group

    def mk_group_timecode(self):
        group = QGroupBox("Timecode")
        main_lay = QVBoxLayout(group)
        k = "modules.timecode"
        
        chk_enable = self._chk("Enable Module", f"{k}.enabled")
        main_lay.addWidget(chk_enable)

        content = QWidget()
        layout = QGridLayout(content)
        layout.setContentsMargins(0, 10, 0, 0)
        
        layout.addWidget(self._lbl("Position"), 0, 0)
        layout.addWidget(self._pos_combo(f"{k}.position"), 0, 1)
        
        layout.addWidget(self._lbl("Size"), 1, 0)
        layout.addWidget(self._slider(10, 200, self.config.get(f"{k}.scale"), lambda v: self.upd(f"{k}.scale", v), "%"), 1, 1)
        
        layout.addWidget(self._lbl("Text Color"), 2, 0)
        layout.addWidget(ColorBtn(self.config.get(f"{k}.text_color"), lambda c: self.upd(f"{k}.text_color", c)), 2, 1)
        
        layout.addWidget(self._lbl("Background"), 3, 0)
        layout.addWidget(ColorBtn(self.config.get(f"{k}.bg_color"), lambda c: self.upd(f"{k}.bg_color", c)), 3, 1)
        
        layout.addWidget(self._lbl("Opacity"), 4, 0)
        layout.addWidget(self._slider(0, 100, self.config.get(f"{k}.bg_opacity"), lambda v: self.upd(f"{k}.bg_opacity", v), "%"), 4, 1)
        
        main_lay.addWidget(content)
        content.setVisible(chk_enable.isChecked())
        chk_enable.toggled.connect(content.setVisible)

        return group

    def mk_group_msg(self):
        group = QGroupBox("Custom Message")
        main_lay = QVBoxLayout(group)
        k = "modules.custom_msg"
        
        chk_enable = self._chk("Enable Module", f"{k}.enabled")
        main_lay.addWidget(chk_enable)

        content = QWidget()
        layout = QGridLayout(content)
        layout.setContentsMargins(0, 10, 0, 0)
        
        txt_msg = QPlainTextEdit()
        txt_msg.setPlainText(self.config.get(f"{k}.text"))
        txt_msg.setFixedHeight(60)
        txt_msg.textChanged.connect(lambda: self.upd(f"{k}.text", txt_msg.toPlainText()))
        layout.addWidget(txt_msg, 0, 0, 1, 2)
        
        layout.addWidget(self._lbl("Position"), 1, 0)
        layout.addWidget(self._pos_combo(f"{k}.position"), 1, 1)
        
        layout.addWidget(self._lbl("Size"), 2, 0)
        layout.addWidget(self._slider(10, 200, self.config.get(f"{k}.scale"), lambda v: self.upd(f"{k}.scale", v), "%"), 2, 1)
        
        layout.addWidget(self._lbl("Text Color"), 3, 0)
        layout.addWidget(ColorBtn(self.config.get(f"{k}.text_color"), lambda c: self.upd(f"{k}.text_color", c)), 3, 1)
        
        layout.addWidget(self._lbl("Background"), 4, 0)
        layout.addWidget(ColorBtn(self.config.get(f"{k}.bg_color"), lambda c: self.upd(f"{k}.bg_color", c)), 4, 1)
        
        layout.addWidget(self._lbl("Opacity"), 5, 0)
        layout.addWidget(self._slider(0, 100, self.config.get(f"{k}.bg_opacity"), lambda v: self.upd(f"{k}.bg_opacity", v), "%"), 5, 1)
        
        main_lay.addWidget(content)
        content.setVisible(chk_enable.isChecked())
        chk_enable.toggled.connect(content.setVisible)

        return group

    # -----------------------------------------------------------------
    # TAB 3: EXPORT
    # -----------------------------------------------------------------
    def mk_tab_export(self):
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(20)
        
        grp_settings = QGroupBox("Export Settings")
        lay_settings = QVBoxLayout(grp_settings)
        lay_settings.setSpacing(15)
        
        lbl_prof = QLabel("Profile:")
        self.cmb_prof = QComboBox()
        self.cmb_prof.addItems(["Final Render", "Compositing Ready", "JSON Only"])
        lay_settings.addWidget(lbl_prof)
        lay_settings.addWidget(self.cmb_prof)
        
        lbl_codec = QLabel("Codec:")
        self.cmb_cod = QComboBox()
        self.cmb_cod.addItems(["H.264", "H.265"])
        lay_settings.addWidget(lbl_codec)
        lay_settings.addWidget(self.cmb_cod)
        
        lbl_name = QLabel("File Name:")
        self.txt_name = QLineEdit()
        self.txt_name.setPlaceholderText("Auto")
        lay_settings.addWidget(lbl_name)
        lay_settings.addWidget(self.txt_name)
        
        lbl_dest = QLabel("Destination:")
        lay_settings.addWidget(lbl_dest)
        
        self.btn_dest = QPushButton("Select Folder...")
        self.btn_dest.clicked.connect(self.sel_out)
        lay_settings.addWidget(self.btn_dest)
        
        layout.addWidget(grp_settings)
        
        layout.addStretch()
        
        grp_action = QGroupBox("Action")
        lay_action = QVBoxLayout(grp_action)
        
        self.lbl_prog = QLabel("Ready")
        self.lbl_prog.setAlignment(Qt.AlignCenter)
        lay_action.addWidget(self.lbl_prog)
        
        self.btn_render = QPushButton("START RENDER")
        self.btn_render.setMinimumHeight(50)
        font_btn = QFont()
        font_btn.setBold(True)
        self.btn_render.setFont(font_btn)
        self.btn_render.clicked.connect(self.run_render)
        lay_action.addWidget(self.btn_render)
        
        self.btn_open_folder = QPushButton("Open Destination Folder")
        self.btn_open_folder.setVisible(False)
        self.btn_open_folder.clicked.connect(self.open_output_folder)
        lay_action.addWidget(self.btn_open_folder)
        
        layout.addWidget(grp_action)
        
        return content

    # -----------------------------------------------------------------
    # HELPERS & LOGIC BINDINGS 
    # -----------------------------------------------------------------
    def _lbl(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet("color: palette(dark);")
        return lbl

    def _chk(self, title, config_key):
        checkbox = QCheckBox(title)
        checkbox.setStyleSheet("color: palette(dark);")
        checkbox.setChecked(self.config.get(config_key, True))
        checkbox.toggled.connect(lambda v: self.upd(config_key, v))
        return checkbox

    def _slider(self, min_val, max_val, current_val, callback, unit=""):
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        slider = QSlider(Qt.Horizontal)
        slider.setRange(min_val, max_val)
        slider.setValue(int(current_val or min_val))
        
        label_value = QLabel(f"{slider.value()}{unit}")
        label_value.setFixedWidth(45)
        label_value.setStyleSheet("color: palette(dark);")
        
        def on_change(val):
            callback(val)
            label_value.setText(f"{val}{unit}")
            
        slider.valueChanged.connect(on_change)
        
        layout.addWidget(slider)
        layout.addWidget(label_value)
        return container

    def _pos_combo(self, config_key):
        combo = QComboBox()
        pos_map = [
            ("Top Left", "top_left"), ("Top Center", "top_center"), ("Top Right", "top_right"),
            ("Center Left", "center_left"), ("Center", "center_center"), ("Center Right", "center_right"),
            ("Bottom Left", "bottom_left"), ("Bottom Center", "bottom_center"), ("Bottom Right", "bottom_right")
        ]
        
        for text, internal_data in pos_map:
            combo.addItem(text, internal_data)
            
        current_val = self.config.get(config_key, "top_left")
        idx = combo.findData(current_val)
        if idx >= 0:
            combo.setCurrentIndex(idx)
            
        combo.currentIndexChanged.connect(lambda idx, cb=combo: self.upd(config_key, cb.itemData(idx)))
        return combo
    
    def upd(self, key, val): 
        self.config.set(key, val)
        self.preview.update_config_live()
        self.preview.force_refresh()
    
    def upd_yolo(self, text_input): 
        tags_list = [x.strip() for x in text_input.split(",") if x.strip()]
        self.config.set("models.custom_classes", tags_list)
        
        if tags_list:
            self.lbl_yolo_tags.setText("Active targets: " + ", ".join(tags_list))
        else:
            self.lbl_yolo_tags.setText("No custom targets active")
            
        self.upd("models.custom_classes", tags_list)
    
    def setup_conns(self):
        self.engine.progress_updated.connect(lambda p, f, fps: self.lbl_prog.setText(f"Processing Frame {f} | {p}% | ~{int(fps)} FPS"))
        self.engine.processing_finished.connect(self.end_render)
    
    def load_video(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Video", "", "Video Files (*.mp4 *.mov)")
        if file_path:
            filename = os.path.basename(file_path)
            self.lbl_vid_name.setText(filename)
            self.preview.load_video(file_path)
            self.txt_name.setText(filename.split('.')[0] + "_output")
            self.engine.video_path = file_path

    def sel_out(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if directory:
            self.config.set("output.output_dir", directory)
            self.btn_dest.setText(".../" + os.path.basename(directory))

    def run_render(self):
        if not hasattr(self.engine, 'video_path') or not self.engine.video_path: 
            QMessageBox.warning(self, "Warning", "Please open a video before rendering.")
            return
            
        self.config.set("output.custom_filename", self.txt_name.text())
        self.config.set("output.profile", self.cmb_prof.currentText())
        self.config.set("output.codec", self.cmb_cod.currentText())
        
        self.engine.setup_render(self.engine.video_path)
        self.preview.pause_playback()
        self.engine.start()
        
        self.btn_render.setEnabled(False)
        self.btn_render.setText("PROCESSING...")
        self.btn_open_folder.setVisible(False)

    def end_render(self, result_dict):
        if "error" in result_dict:
            QMessageBox.critical(self, "Error", result_dict["error"])
        else:
            out_dir = result_dict.get('output_dir', 'Unknown')
            self.sb.showMessage(f"Processing completed successfully: {out_dir}", 10000)
            self.last_out_dir = out_dir
            self.btn_open_folder.setVisible(True)
            
        self.btn_render.setEnabled(True)
        self.btn_render.setText("START RENDER")
        self.lbl_prog.setText("Render Complete")

    def open_output_folder(self):
        if hasattr(self, 'last_out_dir') and os.path.exists(self.last_out_dir):
            if sys.platform == 'darwin': 
                subprocess.Popen(['open', self.last_out_dir])
            elif sys.platform == 'win32': 
                os.startfile(self.last_out_dir)
            else: 
                subprocess.Popen(['xdg-open', self.last_out_dir])

    def closeEvent(self, event: QCloseEvent):
        self.config.save_config()
        self.preview.close()
        event.accept()