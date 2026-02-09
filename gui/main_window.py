"""
T7MD Vision Pro - Studio Layout V8.0 (Depth Integration)
Updates:
- Integración de Checkbox "Depth" con estilo Cyan.
- Conexión automática a configuración 'models.use_depth'.
"""

import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QComboBox, QSlider, QCheckBox,
    QGroupBox, QStatusBar, QFileDialog, QMessageBox, QLineEdit, 
    QFrame, QColorDialog, QScrollArea, QSizePolicy, QPlainTextEdit
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor, QCloseEvent, QPixmap, QImageReader

from gui.enhanced_preview import EnhancedVideoPreview as VideoPreviewWidget
from core.config_manager import ConfigManager
from core.video_engine import VideoEngine
from gui.styles import MAIN_STYLESHEET, ACCENT_COLOR

class ColorBtn(QPushButton):
    def __init__(self, hex_col, cb):
        super().__init__()
        self.setFixedSize(40, 20)
        self.hex = hex_col
        self.cb = cb
        self.upd()
        self.clicked.connect(self.pick)
    
    def upd(self):
        self.setStyleSheet(f"background-color: {self.hex}; border: 1px solid #555;")
    
    def pick(self):
        c = QColorDialog.getColor(QColor(self.hex), self, "Color")
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
        self.setWindowTitle("T7MD Vision Pro - Studio V8.0")
        self.setMinimumSize(1400, 950)
        self.setStyleSheet(MAIN_STYLESHEET)
        
        central = QWidget()
        self.setCentralWidget(central)
        main_l = QVBoxLayout(central)
        main_l.setSpacing(0)
        main_l.setContentsMargins(0,0,0,0)
        
        # 1. Header (64px Compacto)
        main_l.addWidget(self.mk_header())
        
        # 2. Preview
        self.preview = VideoPreviewWidget(self.config)
        main_l.addWidget(self.preview, 1)
        
        # 3. AI Toolbar (Aquí está el cambio del Depth)
        main_l.addWidget(self.mk_ai_toolbar())
        
        # 4. Dashboard (Sin Scroll)
        self.dash = QWidget()
        self.dash.setStyleSheet("background-color: #151515;")
        self.dash_l = QHBoxLayout(self.dash)
        self.dash_l.setSpacing(5)
        self.dash_l.setContentsMargins(10, 5, 10, 5)
        
        self.mk_col_bboxes()    
        self.mk_col_stats()     
        self.mk_col_minimap()   
        self.mk_col_collage()   
        self.mk_col_timecode()  
        self.mk_col_msg()       
        
        main_l.addWidget(self.dash)
        
        # 5. Output
        main_l.addWidget(self.mk_output_bar())
        
        # Status Bar Negra
        self.sb = QStatusBar()
        self.sb.setStyleSheet("background-color: #000; color: #666; border-top: 1px solid #222;")
        self.setStatusBar(self.sb)

    def mk_header(self):
        fr = QFrame()
        fr.setStyleSheet("background-color: #000; border-bottom: 1px solid #333;")
        fr.setFixedHeight(64)
        l = QHBoxLayout(fr)
        l.setContentsMargins(20, 0, 20, 0)
        
        logo_lbl = QLabel()
        logo_path = "logo/logo.png"
        if os.path.exists(logo_path):
            try:
                reader = QImageReader(logo_path)
                if reader.canRead():
                    pix = QPixmap.fromImage(reader.read()).scaledToHeight(40, Qt.SmoothTransformation)
                    logo_lbl.setPixmap(pix)
                else:
                    logo_lbl.setText("IMG ERR")
            except:
                logo_lbl.setText("LOGO ERR")
        else:
            logo_lbl.setText("T7MD VISION")
            logo_lbl.setStyleSheet(f"color: {ACCENT_COLOR}; font-weight: bold; font-size: 24px;")
        l.addWidget(logo_lbl)
        
        l.addStretch()
        
        btn = QPushButton("Abrir Video")
        btn.setFixedSize(100, 30)
        btn.setStyleSheet("border: 1px solid #444; color: #ccc; font-size: 12px;")
        btn.clicked.connect(self.load_video)
        l.addWidget(btn)
        
        self.lbl_vid_name = QLabel("Sin Archivo")
        self.lbl_vid_name.setStyleSheet(f"color: {ACCENT_COLOR}; font-weight: bold; margin-left: 15px; font-size: 12px;")
        l.addWidget(self.lbl_vid_name)
        return fr

    def mk_ai_toolbar(self):
        fr = QFrame()
        fr.setStyleSheet("background-color: #222; border-bottom: 1px solid #333;")
        fr.setFixedHeight(50)
        l = QHBoxLayout(fr)
        l.setContentsMargins(15, 5, 15, 5)
        l.setSpacing(20)
        
        # Checkboxes
        l.addWidget(QLabel(f"<b style='color:{ACCENT_COLOR}'>INTELIGENCIA ARTIFICIAL:</b>"))
        l.addWidget(self._chk("Caras", "models.use_faces"))
        l.addWidget(self._chk("Personas", "models.use_persons"))
        l.addWidget(self._chk("Objetos", "models.use_objects"))
        
        # --- NUEVO: Checkbox Depth ---
        # Usamos tu helper _chk pero guardamos la referencia para aplicar estilo
        chk_depth = self._chk("Depth", "models.use_depth")
        chk_depth.setStyleSheet("color: #00bcd4; font-weight: bold;") # Cyan Style
        chk_depth.setToolTip("Generar Mapa de Profundidad (Z-Depth)")
        l.addWidget(chk_depth)
        # -----------------------------
        
        # Campo YOLO Fluido
        l.addWidget(QLabel("| YOLO:"))
        self.txt_yo = QLineEdit()
        self.txt_yo.setPlaceholderText("cell phone, laptop")
        self.txt_yo.setText(",".join(self.config.get("models.custom_classes", [])))
        self.txt_yo.textChanged.connect(self.upd_yolo)
        l.addWidget(self.txt_yo, 1)
        
        # Padding (Fijo a la derecha)
        l.addWidget(QLabel("Padding Global:"))
        pad_sl = self._slider(0, 200, self.config.get("style.global_margin"), lambda v: self.upd("style.global_margin", v), "px")
        pad_sl.setFixedWidth(150)
        l.addWidget(pad_sl)
        
        return fr

    def mk_output_bar(self):
        fr = QFrame()
        fr.setStyleSheet("background-color: #1a1a1a; border-top: 1px solid #333;")
        fr.setFixedHeight(70)
        l = QHBoxLayout(fr)
        l.setContentsMargins(20, 10, 20, 10)
        l.setSpacing(15)
        l.addWidget(QLabel("PERFIL:"))
        self.cmb_prof = QComboBox(); self.cmb_prof.addItems(["Final Render", "Compositing", "JSON Only"])
        l.addWidget(self.cmb_prof)
        l.addWidget(QLabel("CODEC:"))
        self.cmb_cod = QComboBox(); self.cmb_cod.addItems(["H.264", "H.265"])
        l.addWidget(self.cmb_cod)
        l.addWidget(QLabel("NOMBRE:"))
        self.txt_name = QLineEdit(); self.txt_name.setPlaceholderText("Auto")
        l.addWidget(self.txt_name, 1)
        self.btn_dest = QPushButton("Destino..."); self.btn_dest.clicked.connect(self.sel_out)
        l.addWidget(self.btn_dest)
        
        self.btn_render = QPushButton("▶ RENDERIZAR")
        self.btn_render.setFixedSize(160, 40)
        self.btn_render.setStyleSheet(f"""
            QPushButton {{ 
                background-color: {ACCENT_COLOR}; 
                color: #000000; 
                font-weight: bold; 
                border-radius: 4px; 
                border: none;
                font-size: 13px;
            }}
            QPushButton:hover {{ background-color: #ccff66; }}
            QPushButton:pressed {{ background-color: #aaff44; }}
        """)
        self.btn_render.clicked.connect(self.run_render)
        l.addWidget(self.btn_render)
        
        self.lbl_prog = QLabel("--:--")
        l.addWidget(self.lbl_prog)
        return fr

    def mk_col_bboxes(self):
        g = QGroupBox("BBOXES"); l = QGridLayout(g); k = "modules.bboxes"
        l.addWidget(self._chk("Activar", f"{k}.enabled"), 0, 0, 1, 3)
        l.addWidget(QLabel("Personas"), 1, 0); l.addWidget(ColorBtn(self.config.get(f"{k}.person_color"), lambda c: self.upd(f"{k}.person_color", c)), 1, 1); l.addWidget(self._slider(1, 10, self.config.get(f"{k}.person_thick"), lambda v: self.upd(f"{k}.person_thick", v), "px"), 1, 2)
        l.addWidget(QLabel("Caras"), 2, 0); l.addWidget(ColorBtn(self.config.get(f"{k}.face_color"), lambda c: self.upd(f"{k}.face_color", c)), 2, 1); l.addWidget(self._slider(1, 10, self.config.get(f"{k}.face_thick"), lambda v: self.upd(f"{k}.face_thick", v), "px"), 2, 2)
        l.addWidget(QLabel("Objetos"), 3, 0); l.addWidget(ColorBtn(self.config.get(f"{k}.object_color"), lambda c: self.upd(f"{k}.object_color", c)), 3, 1); l.addWidget(self._slider(1, 10, self.config.get(f"{k}.object_thick"), lambda v: self.upd(f"{k}.object_thick", v), "px"), 3, 2)
        l.addWidget(QLabel("Etiqueta"), 4, 0); l.addWidget(self._slider(10, 200, self.config.get(f"{k}.label_scale"), lambda v: self.upd(f"{k}.label_scale", v), "%"), 4, 1, 1, 2)
        l.addWidget(QLabel("Color Texto"), 5, 0); l.addWidget(ColorBtn(self.config.get(f"{k}.label_text_color"), lambda c: self.upd(f"{k}.label_text_color", c)), 5, 1)
        l.addWidget(self._chk("Crosshair", f"{k}.show_crosshair"), 6, 0, 1, 3)
        self.dash_l.addWidget(g)

    def mk_col_stats(self):
        g = QGroupBox("STATS"); l = QGridLayout(g); k = "modules.stats"
        l.addWidget(self._chk("Activar", f"{k}.enabled"), 0, 0, 1, 2)
        ht = QLineEdit(); ht.setText(self.config.get(f"{k}.header_text")); ht.textChanged.connect(lambda x: self.upd(f"{k}.header_text", x)); l.addWidget(QLabel("Titulo:"), 1, 0); l.addWidget(ht, 1, 1)
        l.addWidget(QLabel("Posicion"), 2, 0); l.addWidget(self._pos_combo(f"{k}.position"), 2, 1)
        l.addWidget(QLabel("Tamaño"), 3, 0); l.addWidget(self._slider(10, 200, self.config.get(f"{k}.scale"), lambda v: self.upd(f"{k}.scale", v), "%"), 3, 1)
        l.addWidget(QLabel("Texto"), 4, 0); l.addWidget(ColorBtn(self.config.get(f"{k}.text_color"), lambda c: self.upd(f"{k}.text_color", c)), 4, 1)
        l.addWidget(QLabel("Fondo"), 5, 0); l.addWidget(ColorBtn(self.config.get(f"{k}.bg_color"), lambda c: self.upd(f"{k}.bg_color", c)), 5, 1)
        l.addWidget(QLabel("Opacidad"), 6, 0); l.addWidget(self._slider(0, 100, self.config.get(f"{k}.bg_opacity"), lambda v: self.upd(f"{k}.bg_opacity", v), "%"), 6, 1)
        self.dash_l.addWidget(g)

    def mk_col_minimap(self):
        g = QGroupBox("MINIMAP"); l = QGridLayout(g); k = "modules.minimap"
        l.addWidget(self._chk("Activar", f"{k}.enabled"), 0, 0, 1, 2)
        l.addWidget(QLabel("Posicion"), 1, 0); l.addWidget(self._pos_combo(f"{k}.position"), 1, 1)
        l.addWidget(QLabel("Tamaño"), 2, 0); l.addWidget(self._slider(50, 200, self.config.get(f"{k}.scale"), lambda v: self.upd(f"{k}.scale", v), "%"), 2, 1)
        l.addWidget(QLabel("Borde"), 3, 0); l.addWidget(self._slider(0, 10, self.config.get(f"{k}.border_thick"), lambda v: self.upd(f"{k}.border_thick", v), "px"), 3, 1)
        l.addWidget(QLabel("Col Borde"), 4, 0); l.addWidget(ColorBtn(self.config.get(f"{k}.border_color"), lambda c: self.upd(f"{k}.border_color", c)), 4, 1)
        l.addWidget(QLabel("Tam. Puntos"), 5, 0); l.addWidget(self._slider(1, 10, self.config.get(f"{k}.dot_size"), lambda v: self.upd(f"{k}.dot_size", v), "px"), 5, 1)
        l.addWidget(QLabel("Fondo"), 6, 0); l.addWidget(ColorBtn(self.config.get(f"{k}.bg_color"), lambda c: self.upd(f"{k}.bg_color", c)), 6, 1)
        l.addWidget(QLabel("Opacidad"), 7, 0); l.addWidget(self._slider(0, 100, self.config.get(f"{k}.bg_opacity"), lambda v: self.upd(f"{k}.bg_opacity", v), "%"), 7, 1)
        self.dash_l.addWidget(g)

    def mk_col_collage(self):
        g = QGroupBox("COLLAGE"); l = QGridLayout(g); k = "modules.collage"
        l.addWidget(self._chk("Activar", f"{k}.enabled"), 0, 0, 1, 2)
        l.addWidget(QLabel("Posicion"), 1, 0); l.addWidget(self._pos_combo(f"{k}.position"), 1, 1)
        l.addWidget(QLabel("Tamaño Fotos"), 2, 0); l.addWidget(self._slider(5, 30, self.config.get(f"{k}.thumb_size_pct"), lambda v: self.upd(f"{k}.thumb_size_pct", v), "%"), 2, 1)
        l.addWidget(QLabel("Borde"), 3, 0); l.addWidget(self._slider(0, 10, self.config.get(f"{k}.border_thick"), lambda v: self.upd(f"{k}.border_thick", v), "px"), 3, 1)
        l.addWidget(QLabel("Col Borde"), 4, 0); l.addWidget(ColorBtn(self.config.get(f"{k}.border_color"), lambda c: self.upd(f"{k}.border_color", c)), 4, 1)
        l.addWidget(QLabel("Gap"), 5, 0); l.addWidget(self._slider(0, 50, self.config.get(f"{k}.gap_pct"), lambda v: self.upd(f"{k}.gap_pct", v), "%"), 5, 1)
        l.addWidget(QLabel("Opacidad"), 6, 0); l.addWidget(self._slider(0, 100, self.config.get(f"{k}.opacity"), lambda v: self.upd(f"{k}.opacity", v), "%"), 6, 1)
        self.dash_l.addWidget(g)

    def mk_col_timecode(self):
        g = QGroupBox("TIMECODE"); l = QGridLayout(g); k = "modules.timecode"
        l.addWidget(self._chk("Activar", f"{k}.enabled"), 0, 0, 1, 2)
        l.addWidget(QLabel("Posicion"), 1, 0); l.addWidget(self._pos_combo(f"{k}.position"), 1, 1)
        l.addWidget(QLabel("Tamaño"), 2, 0); l.addWidget(self._slider(10, 200, self.config.get(f"{k}.scale"), lambda v: self.upd(f"{k}.scale", v), "%"), 2, 1)
        l.addWidget(QLabel("Texto"), 3, 0); l.addWidget(ColorBtn(self.config.get(f"{k}.text_color"), lambda c: self.upd(f"{k}.text_color", c)), 3, 1)
        l.addWidget(QLabel("Fondo"), 4, 0); l.addWidget(ColorBtn(self.config.get(f"{k}.bg_color"), lambda c: self.upd(f"{k}.bg_color", c)), 4, 1)
        l.addWidget(QLabel("Opacidad"), 5, 0); l.addWidget(self._slider(0, 100, self.config.get(f"{k}.bg_opacity"), lambda v: self.upd(f"{k}.bg_opacity", v), "%"), 5, 1)
        self.dash_l.addWidget(g)

    def mk_col_msg(self):
        g = QGroupBox("MENSAJE"); l = QGridLayout(g); k = "modules.custom_msg"
        l.addWidget(self._chk("Activar", f"{k}.enabled"), 0, 0, 1, 2)
        t = QPlainTextEdit(); t.setPlainText(self.config.get(f"{k}.text")); t.setFixedHeight(60); t.textChanged.connect(lambda: self.upd(f"{k}.text", t.toPlainText())); l.addWidget(t, 1, 0, 1, 2)
        l.addWidget(QLabel("Posicion"), 2, 0); l.addWidget(self._pos_combo(f"{k}.position"), 2, 1)
        l.addWidget(QLabel("Tamaño"), 3, 0); l.addWidget(self._slider(10, 200, self.config.get(f"{k}.scale"), lambda v: self.upd(f"{k}.scale", v), "%"), 3, 1)
        l.addWidget(QLabel("Texto"), 4, 0); l.addWidget(ColorBtn(self.config.get(f"{k}.text_color"), lambda c: self.upd(f"{k}.text_color", c)), 4, 1)
        l.addWidget(QLabel("Fondo"), 5, 0); l.addWidget(ColorBtn(self.config.get(f"{k}.bg_color"), lambda c: self.upd(f"{k}.bg_color", c)), 5, 1)
        l.addWidget(QLabel("Opacidad"), 6, 0); l.addWidget(self._slider(0, 100, self.config.get(f"{k}.bg_opacity"), lambda v: self.upd(f"{k}.bg_opacity", v), "%"), 6, 1)
        self.dash_l.addWidget(g)

    def _chk(self, t, k):
        c = QCheckBox(t); c.setChecked(self.config.get(k, True)); c.toggled.connect(lambda v: self.upd(k, v)); return c
    def _slider(self, mn, mx, v, fn, unit=""):
        w = QWidget(); l = QHBoxLayout(w); l.setContentsMargins(0,0,0,0); l.setSpacing(5)
        s = QSlider(Qt.Horizontal); s.setRange(mn, mx); s.setValue(int(v or mn)); lbl = QLabel(f"{s.value()}{unit}"); lbl.setFixedWidth(35)
        def chg(val): fn(val); lbl.setText(f"{val}{unit}")
        s.valueChanged.connect(chg); l.addWidget(s); l.addWidget(lbl); return w
    def _pos_combo(self, k):
        c = QComboBox(); c.addItems(["top_left", "top_center", "top_right", "center_left", "center_center", "center_right", "bottom_left", "bottom_center", "bottom_right"])
        c.setCurrentText(self.config.get(k, "top_left")); c.currentTextChanged.connect(lambda t: self.upd(k, t)); return c
    
    def upd(self, key, val): 
        self.config.set(key, val)
        self.preview.update_config_live()
        self.preview.force_refresh()
    
    def upd_yolo(self, t): 
        l = [x.strip() for x in t.split(",") if x.strip()]
        self.config.set("models.custom_classes", l)
        self.upd("models.custom_classes", l)
    
    def setup_conns(self):
        self.engine.progress_updated.connect(lambda p,f,t: self.lbl_prog.setText(f"{p}%"))
        self.engine.processing_finished.connect(self.end_render)
    
    def load_video(self):
        f, _ = QFileDialog.getOpenFileName(self, "Video", "", "Video (*.mp4 *.mov)")
        if f:
            self.lbl_vid_name.setText(os.path.basename(f))
            self.preview.load_video(f)
            self.txt_name.setText(os.path.basename(f).split('.')[0] + "_proc")
            self.engine.video_path = f

    def sel_out(self):
        d = QFileDialog.getExistingDirectory(self, "Salida")
        if d:
            self.config.set("output.output_dir", d)
            self.btn_dest.setText(".../" + os.path.basename(d))

    def run_render(self):
        if not hasattr(self.engine, 'video_path'): return
        self.config.set("output.custom_filename", self.txt_name.text())
        self.config.set("output.profile", self.cmb_prof.currentText())
        self.config.set("output.codec", self.cmb_cod.currentText())
        self.engine.setup_render(self.engine.video_path)
        self.preview.pause_playback()
        self.engine.start()
        self.btn_render.setEnabled(False)
        self.btn_render.setText("Procesando...")

    def end_render(self, s):
        QMessageBox.information(self, "Fin", f"Guardado en:\n{s['output_dir']}")
        self.btn_render.setEnabled(True)
        self.btn_render.setText("▶ RENDERIZAR")
        self.lbl_prog.setText("100%")

    def closeEvent(self, e: QCloseEvent):
        self.config.save_config()
        self.preview.close()
        e.accept()