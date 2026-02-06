# En load_video o donde cargues los modelos, haz esto:

def load_video(self, video_path):
    """Cargar video para preview"""
    try:
        self.video_path = video_path
        self.cap = cv2.VideoCapture(video_path)
        
        if not self.cap.isOpened():
            raise Exception("No se pudo abrir el video")
        
        # Cargar solo el modelo base (sin caras por ahora)
        self.load_base_model_only()
        
        # Obtener primer frame
        ret, frame = self.cap.read()
        if ret:
            self.current_frame = frame
            self.show_frame(frame)
            self.lbl_instructions.hide()
        
        # Iniciar timer para actualización (30 FPS para preview)
        self.timer.start(33)  # ~30 FPS
        
    except Exception as e:
        print(f"Error al cargar video: {e}")
        self.show_error_message(f"Error: {str(e)}")

def load_base_model_only(self):
    """Cargar solo el modelo base (evita problemas con el modelo de caras)"""
    try:
        from ultralytics import YOLO
        import torch
        
        # Determinar dispositivo
        self.device = "mps" if torch.backends.mps.is_available() else "cpu"
        
        # Cargar solo modelo base
        if os.path.exists("models/yolov8m.pt"):
            self.base_model = YOLO("models/yolov8m.pt").to(self.device)
            print(f"✅ Modelo base cargado en {self.device}")
        else:
            print("⚠️ Modelo base no encontrado")
            self.base_model = None
            
        # No cargar modelo de caras por ahora
        self.face_model = None
        
    except Exception as e:
        print(f"⚠️ Error cargando modelo: {e}")
        self.base_model = None
        self.face_model = None

class VideoPreviewWidget(QWidget):
    """Widget para mostrar preview de video"""
    
    def __init__(self):
        super().__init__()
        self.video_path = None
        self.cap = None
        self.current_frame = None
        self.timer = QTimer()
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """Configurar la interfaz del widget"""
        self.setMinimumHeight(400)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Etiqueta para el frame
        self.lbl_frame = QLabel()
        self.lbl_frame.setAlignment(Qt.AlignCenter)
        self.lbl_frame.setStyleSheet("""
            QLabel {
                background-color: #000;
                border: 1px solid #333;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.lbl_frame)
        
        # Etiqueta de instrucciones
        self.lbl_instructions = QLabel("Carga un video para comenzar")
        self.lbl_instructions.setAlignment(Qt.AlignCenter)
        self.lbl_instructions.setStyleSheet("color: #888; font-style: italic;")
        layout.addWidget(self.lbl_instructions)
    
    def setup_connections(self):
        """Conectar señales"""
        self.timer.timeout.connect(self.update_frame)
    
    def load_video(self, video_path):
        """Cargar video para preview"""
        try:
            self.video_path = video_path
            self.cap = cv2.VideoCapture(video_path)
            
            if not self.cap.isOpened():
                raise Exception("No se pudo abrir el video")
            
            # Obtener primer frame
            ret, frame = self.cap.read()
            if ret:
                self.current_frame = frame
                self.show_frame(frame)
                self.lbl_instructions.hide()
            
            # Iniciar timer para actualización (30 FPS para preview)
            self.timer.start(33)  # ~30 FPS
            
        except Exception as e:
            print(f"Error al cargar video: {e}")
            self.show_error_message(f"Error: {str(e)}")
    
    def update_frame(self):
        """Actualizar frame del preview"""
        if self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                self.current_frame = frame
                self.show_frame(frame)
            else:
                # Si llegamos al final, reiniciamos
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    
    def show_frame(self, frame):
        """Mostrar frame en el widget"""
        # Convertir BGR a RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Redimensionar manteniendo aspect ratio
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w
        
        # Convertir a QImage
        qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        
        # Escalar al tamaño del widget manteniendo aspect ratio
        scaled_pixmap = QPixmap.fromImage(qt_image).scaled(
            self.lbl_frame.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        
        self.lbl_frame.setPixmap(scaled_pixmap)
    
    def show_error_message(self, message):
        """Mostrar mensaje de error"""
        self.lbl_instructions.setText(message)
        self.lbl_instructions.setStyleSheet("color: #ff4444; font-style: normal;")
        self.lbl_instructions.show()
    
    def resizeEvent(self, event):
        """Redimensionar el frame cuando cambia el tamaño del widget"""
        super().resizeEvent(event)
        if self.current_frame is not None:
            self.show_frame(self.current_frame)
    
    def close(self):
        """Liberar recursos"""
        if self.cap:
            self.cap.release()
        self.timer.stop()
        super().close()