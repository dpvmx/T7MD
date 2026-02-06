"""
Panel de procesamiento: Incluye Configuración de Salida + Controles de Ejecución.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QProgressBar, QLabel, QFrame, QComboBox, QLineEdit, QCheckBox, QSizePolicy
)
from PySide6.QtCore import Qt, Signal

class ProcessingPanel(QWidget):
    """Panel unificado: Salida + Render"""
    
    # Señales de ejecución
    render_started = Signal()
    render_paused = Signal()
    render_stopped = Signal()
    
    # Señal para pedir al Main Window que abra el diálogo de carpeta
    request_output_dir = Signal()
    
    def __init__(self):
        super().__init__()
        self.is_processing = False
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        # Frame contenedor con estilo
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 5, 0, 0)
        
        container = QFrame()
        container.setObjectName("ProcessingContainer")
        container.setStyleSheet("""
            #ProcessingContainer {
                background-color: #252526;
                border: 1px solid #444;
                border-radius: 5px;
            }
            QLabel { color: #aaa; font-size: 11px; font-weight: bold; }
        """)
        
        # Layout interno del contenedor
        layout = QVBoxLayout(container)
        layout.setContentsMargins(15, 10, 15, 15)
        layout.setSpacing(15)
        
        # --- FILA 1: CONFIGURACIÓN DE SALIDA ---
        row_config = QHBoxLayout()
        row_config.setSpacing(15)
        
        # Perfil
        row_config.addWidget(QLabel("PERFIL:"))
        self.cmb_profile = QComboBox()
        self.cmb_profile.addItems(["Final Render", "ProRes 422", "JSON Only"])
        self.cmb_profile.setFixedWidth(120)
        row_config.addWidget(self.cmb_profile)
        
        # Codec
        row_config.addWidget(QLabel("CODEC:"))
        self.cmb_codec = QComboBox()
        self.cmb_codec.addItems(["H.264", "H.265 (HEVC)"])
        self.cmb_codec.setFixedWidth(80)
        row_config.addWidget(self.cmb_codec)
        
        # Nombre Archivo
        row_config.addWidget(QLabel("NOMBRE:"))
        self.txt_filename = QLineEdit()
        self.txt_filename.setPlaceholderText("Auto (Video Original)")
        row_config.addWidget(self.txt_filename, 1) # Expansible
        
        # Botón Carpeta
        self.btn_out_dir = QPushButton("📂 Destino...")
        self.btn_out_dir.setFixedWidth(100)
        row_config.addWidget(self.btn_out_dir)
        
        # Crops
        self.chk_save_crops = QCheckBox("Guardar Crops")
        self.chk_save_crops.setChecked(True)
        row_config.addWidget(self.chk_save_crops)
        
        layout.addLayout(row_config)
        
        # Línea divisora sutil
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("background-color: #333;")
        layout.addWidget(line)
        
        # --- FILA 2: CONTROLES DE EJECUCIÓN ---
        row_exec = QHBoxLayout()
        row_exec.setSpacing(15)
        
        # Botones
        self.btn_render = QPushButton("▶ RENDERIZAR")
        self.btn_render.setMinimumWidth(130)
        self.btn_render.setFixedHeight(35)
        self.btn_render.setStyleSheet("background-color: #0d47a1; color: white; font-weight: bold; font-size: 12px;")
        
        self.btn_pause = QPushButton("⏸")
        self.btn_pause.setFixedWidth(40)
        self.btn_pause.setFixedHeight(35)
        self.btn_pause.setEnabled(False)
        
        self.btn_cancel = QPushButton("⏹")
        self.btn_cancel.setFixedWidth(40)
        self.btn_cancel.setFixedHeight(35)
        self.btn_cancel.setStyleSheet("QPushButton:enabled { background-color: #d32f2f; }")
        self.btn_cancel.setEnabled(False)
        
        row_exec.addWidget(self.btn_render)
        row_exec.addWidget(self.btn_pause)
        row_exec.addWidget(self.btn_cancel)
        
        # Barra de Progreso e Info
        progress_container = QVBoxLayout()
        progress_container.setSpacing(2)
        
        # Labels info
        lbl_layout = QHBoxLayout()
        self.lbl_status = QLabel("Listo")
        self.lbl_status.setStyleSheet("color: #ccc; font-weight: normal;")
        
        self.lbl_time = QLabel("--:--")
        self.lbl_time.setAlignment(Qt.AlignRight)
        
        lbl_layout.addWidget(self.lbl_status)
        lbl_layout.addStretch()
        lbl_layout.addWidget(self.lbl_time)
        
        # Barra
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar { border: none; background-color: #1e1e1e; border-radius: 3px; }
            QProgressBar::chunk { background-color: #007acc; border-radius: 3px; }
        """)
        
        progress_container.addLayout(lbl_layout)
        progress_container.addWidget(self.progress_bar)
        
        row_exec.addLayout(progress_container, 1) # Expansible
        
        layout.addLayout(row_exec)
        main_layout.addWidget(container)
    
    def setup_connections(self):
        self.btn_render.clicked.connect(self.start_render)
        self.btn_pause.clicked.connect(self.toggle_pause)
        self.btn_cancel.clicked.connect(self.cancel_render)
        # Emitimos señal para que Main Window maneje el diálogo de carpeta
        self.btn_out_dir.clicked.connect(lambda: self.request_output_dir.emit())
    
    def start_render(self):
        self.is_processing = True
        self.update_ui_state()
        self.lbl_status.setText("Inicializando...")
        self.lbl_status.setStyleSheet("color: #00ff00;")
        self.render_started.emit()
    
    def toggle_pause(self):
        if self.btn_pause.text() == "⏸":
            self.btn_pause.setText("▶")
            self.lbl_status.setText("Pausado")
            self.lbl_status.setStyleSheet("color: #ffff00;")
            self.render_paused.emit()
        else:
            self.btn_pause.setText("⏸")
            self.lbl_status.setText("Renderizando...")
            self.lbl_status.setStyleSheet("color: #00ff00;")
            self.render_started.emit()
    
    def cancel_render(self):
        self.is_processing = False
        self.update_ui_state()
        self.progress_bar.setValue(0)
        self.lbl_status.setText("Cancelado")
        self.lbl_status.setStyleSheet("color: #ff4444;")
        self.render_stopped.emit()
    
    def update_ui_state(self):
        # Deshabilitar configuración durante render
        inputs_enabled = not self.is_processing
        self.cmb_profile.setEnabled(inputs_enabled)
        self.cmb_codec.setEnabled(inputs_enabled)
        self.txt_filename.setEnabled(inputs_enabled)
        self.btn_out_dir.setEnabled(inputs_enabled)
        self.chk_save_crops.setEnabled(inputs_enabled)
        
        # Botones de control
        self.btn_render.setEnabled(inputs_enabled)
        self.btn_pause.setEnabled(self.is_processing)
        self.btn_cancel.setEnabled(self.is_processing)
        if not self.is_processing:
            self.btn_pause.setText("⏸")
    
    def update_progress(self, value, time_remaining="--:--", memory="--"):
        self.progress_bar.setValue(value)
        self.lbl_time.setText(time_remaining)