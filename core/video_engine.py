import cv2
import time
import json
import os
import urllib.parse
from PySide6.QtCore import QThread, Signal
from core.yolo_processor import YOLOProcessor

# Intentamos importar el procesador de profundidad
# Si falla (ej. falta transformers), no romperá la app, solo desactivará la función.
try:
    from core.depth_processor import DepthProcessor
except ImportError:
    DepthProcessor = None
    print("⚠️ DepthProcessor no disponible (Falta instalar 'transformers'?)")

class VideoEngine(QThread):
    progress_updated = Signal(int, int, float)
    processing_finished = Signal(dict)

    def __init__(self, config_manager):
        super().__init__()
        self.config = config_manager
        self.running = False
        self.paused = False
        self.video_path = ""
        
        # Inicializamos el procesador principal (YOLO)
        self.processor = YOLOProcessor(config_manager)
        
        # El procesador de profundidad se carga bajo demanda para ahorrar RAM
        self.depth_processor = None 

    def setup_render(self, video_path):
        """Configura el render antes de iniciar el hilo"""
        self.video_path = video_path
        self.running = True
        self.paused = False
        
        # --- CARGA PREVIA DE MODELOS ---
        # Verificamos si podemos cargar el modelo de profundidad ahora
        # para no tener lag en el primer frame.
        if DepthProcessor:
            if self.depth_processor is None:
                try:
                    self.depth_processor = DepthProcessor(self.config)
                    print("✅ DepthProcessor inicializado correctamente.")
                except Exception as e:
                    print(f"❌ Error iniciando DepthProcessor: {e}")

    def run(self):
        # --- 1. GESTIÓN DE RUTAS Y ARCHIVOS ---
        final_path = self.video_path
        # Fix común: Decodificar URL si viene arrastrado del navegador de archivos
        if not os.path.exists(final_path):
            decoded_path = urllib.parse.unquote(self.video_path)
            if os.path.exists(decoded_path): final_path = decoded_path

        if not os.path.exists(final_path):
            self.processing_finished.emit({"error": f"Ruta inválida: {final_path}"})
            return

        self.video_path = final_path
        cap = cv2.VideoCapture(self.video_path)
        
        if not cap.isOpened():
            self.processing_finished.emit({"error": "No se pudo abrir el archivo de video"})
            return
        
        # --- 2. PROPIEDADES DEL VIDEO ---
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames == 0: total_frames = 1

        # --- 3. CONFIGURACIÓN DE SALIDA ---
        out_conf = self.config.get("output")
        filename = out_conf.get("custom_filename") or f"T7MD_{int(time.time())}"
        out_dir = out_conf.get("output_dir", "outputs")
        os.makedirs(out_dir, exist_ok=True)
        
        save_path_json = os.path.join(out_dir, f"{filename}.json")
        save_path_video = os.path.join(out_dir, f"{filename}.mp4")
        save_path_depth = os.path.join(out_dir, f"{filename}_depth.mp4") # Nuevo archivo
        
        skip_video = out_conf.get("skip_video", False)
        
        # --- 4. ACTIVACIÓN DE PROFUNDIDAD ---
        # Leemos la configuración real (si no existe, por defecto es False)
        use_depth = self.config.get("models.use_depth", False)

        writer = None
        writer_depth = None 

        # Codec
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        try:
            if out_conf.get("codec") == "H.265": fourcc = cv2.VideoWriter_fourcc(*'hevc')
        except: pass

        # Inicializar Writers
        if not skip_video:
            # Video Principal (Detecciones)
            writer = cv2.VideoWriter(save_path_video, fourcc, fps, (width, height))
            
            # Video Secundario (Profundidad)
            if use_depth and self.depth_processor:
                print(f"🌊 Creando archivo de profundidad: {save_path_depth}")
                writer_depth = cv2.VideoWriter(save_path_depth, fourcc, fps, (width, height))

        # Estructura JSON
        self.json_data = {
            "metadata": {
                "source": self.video_path, 
                "width": width, 
                "height": height, 
                "fps": fps, 
                "total_frames": total_frames
            },
            "frames": []
        }

        # Configuración de Modelos YOLO
        use_faces = self.config.get("models.use_faces")
        use_persons = self.config.get("models.use_persons")
        use_objects = self.config.get("models.use_objects")
        custom_classes = self.config.get("models.custom_classes")

        frame_idx = 0
        
        # --- 5. BUCLE PRINCIPAL ---
        while self.running and cap.isOpened():
            if self.paused:
                time.sleep(0.1)
                continue

            ret, frame = cap.read()
            if not ret: break

            # A. DETECCIÓN (YOLO)
            raw_detections = self.processor.detect_frame(
                frame, use_faces, use_persons, use_objects, custom_classes
            )

            # B. PROFUNDIDAD (DEPTH ANYTHING V2)
            # Solo procesamos si el writer existe (ahorra recursos si está desactivado)
            if writer_depth is not None:
                try:
                    depth_frame = self.depth_processor.process_frame(frame)
                    writer_depth.write(depth_frame)
                except Exception as e:
                    print(f"Error procesando frame depth: {e}")

            # C. DATOS JSON
            frame_entry = { "index": frame_idx, "timestamp": frame_idx / fps, "detections": [] }
            
            all_dets = []
            if use_faces: all_dets.extend([{"type": "face", **d} for d in raw_detections.get("faces", [])])
            if use_persons: all_dets.extend([{"type": "person", **d} for d in raw_detections.get("persons", [])])
            if use_objects: all_dets.extend([{"type": "object", **d} for d in raw_detections.get("objects", [])])

            for d in all_dets:
                x1, y1, x2, y2 = d['bbox']
                w_box = x2 - x1
                h_box = y2 - y1
                det_entry = {
                    "label": d.get('label', 'unknown'),
                    "type": d['type'],
                    "conf": float(d.get('confidence', 0)),
                    "track_id": d.get('track_id'), # Será None por ahora (modo estabilidad)
                    "rect": { 
                        "w": float(w_box), 
                        "h": float(h_box), 
                        "cx": float(x1 + w_box/2), 
                        "cy": float(y1 + h_box/2) 
                    }
                }
                frame_entry["detections"].append(det_entry)
            
            self.json_data["frames"].append(frame_entry)

            # D. DIBUJAR CAJAS (Video Principal)
            if writer is not None:
                processed_frame = self.processor.draw_detections(frame, raw_detections, frame_idx, fps)
                writer.write(processed_frame)

            frame_idx += 1
            
            # Emitir Progreso
            progress = int((frame_idx / total_frames) * 100)
            self.progress_updated.emit(progress, frame_idx, fps)

        # --- 6. LIMPIEZA ---
        cap.release()
        if writer is not None: writer.release()
        if writer_depth is not None: writer_depth.release()
        
        # Guardar JSON
        try:
            with open(save_path_json, 'w', encoding='utf-8') as f:
                json.dump(self.json_data, f, indent=2)
            
            # Resultado final
            result_data = {
                "output_dir": out_dir, 
                "video_file": save_path_video, 
                "json_file": save_path_json
            }
            if writer_depth:
                result_data["depth_file"] = save_path_depth
                
            self.processing_finished.emit(result_data)
            
        except Exception as e:
            self.processing_finished.emit({"error": str(e)})