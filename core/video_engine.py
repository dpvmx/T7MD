import cv2
import time
import json
import os
import urllib.parse # <--- NUEVO: Para limpiar rutas raras
from PySide6.QtCore import QThread, Signal
from core.yolo_processor import YOLOProcessor

class VideoEngine(QThread):
    progress_updated = Signal(int, int, float)
    processing_finished = Signal(dict)

    def __init__(self, config_manager):
        super().__init__()
        self.config = config_manager
        self.running = False
        self.paused = False
        self.video_path = ""
        self.processor = YOLOProcessor(config_manager)
        
        self.json_data = { "metadata": {}, "frames": [] }

    def setup_render(self, video_path):
        self.video_path = video_path
        self.running = True
        self.paused = False

    def run(self):
        # --- FIX DE RUTAS (Modo Detectivesco) ---
        # 1. Intentamos la ruta tal cual
        final_path = self.video_path
        
        # 2. Si no existe, intentamos decodificarla (quitar %20)
        if not os.path.exists(final_path):
            decoded_path = urllib.parse.unquote(self.video_path)
            if os.path.exists(decoded_path):
                final_path = decoded_path

        # 3. Si sigue sin existir, lanzamos error CON LA RUTA para verla
        if not os.path.exists(final_path):
            self.processing_finished.emit({"error": f"Ruta inválda: {final_path}"})
            return

        self.video_path = final_path # Usamos la ruta corregida

        # --- INICIO DEL PROCESO ---
        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            self.processing_finished.emit({"error": "No se pudo leer el archivo de video (Codec/Permisos)"})
            return

        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames == 0: total_frames = 1

        # Configuración de Salida
        out_conf = self.config.get("output")
        filename = out_conf.get("custom_filename") or f"T7MD_{int(time.time())}"
        out_dir = out_conf.get("output_dir", "outputs")
        os.makedirs(out_dir, exist_ok=True)
        
        save_path_json = os.path.join(out_dir, f"{filename}.json")
        
        # Check para saltar video (Optimización)
        skip_video = out_conf.get("skip_video", False)
        writer = None
        save_path_video = None

        if not skip_video:
            save_path_video = os.path.join(out_dir, f"{filename}.mp4")
            fourcc = cv2.VideoWriter_fourcc(*'mp4v') 
            try:
                if out_conf.get("codec") == "H.265":
                    fourcc = cv2.VideoWriter_fourcc(*'hevc')
            except: pass
            writer = cv2.VideoWriter(save_path_video, fourcc, fps, (width, height))

        # Reset JSON
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

        use_faces = self.config.get("models.use_faces")
        use_persons = self.config.get("models.use_persons")
        use_objects = self.config.get("models.use_objects")
        custom_classes = self.config.get("models.custom_classes")

        frame_idx = 0
        
        while self.running and cap.isOpened():
            if self.paused:
                time.sleep(0.1)
                continue

            ret, frame = cap.read()
            if not ret:
                break

            # 1. DETECCION
            raw_detections = self.processor.detect_frame(
                frame, use_faces, use_persons, use_objects, custom_classes
            )

            # 2. DATA JSON
            frame_entry = { "index": frame_idx, "timestamp": frame_idx / fps, "detections": [] }
            
            all_dets = []
            if use_faces: all_dets.extend([{"type": "face", **d} for d in raw_detections.get("faces", [])])
            if use_persons: all_dets.extend([{"type": "person", **d} for d in raw_detections.get("persons", [])])
            if use_objects: all_dets.extend([{"type": "object", **d} for d in raw_detections.get("objects", [])])

            for d in all_dets:
                x1, y1, x2, y2 = d['bbox']
                w_box = x2 - x1
                h_box = y2 - y1
                frame_entry["detections"].append({
                    "label": d.get('label', 'unknown'),
                    "type": d['type'],
                    "conf": float(d.get('confidence', 0)),
                    "rect": { 
                        "w": float(w_box), "h": float(h_box),
                        "cx": float(x1 + w_box/2), "cy": float(y1 + h_box/2)
                    }
                })
            
            self.json_data["frames"].append(frame_entry)

            # 3. VIDEO (Solo si no está skippeado)
            if writer is not None:
                processed_frame = self.processor.draw_detections(frame, raw_detections, frame_idx, fps)
                writer.write(processed_frame)

            # Progreso
            frame_idx += 1
            progress = int((frame_idx / total_frames) * 100)
            self.progress_updated.emit(progress, frame_idx, fps)

        cap.release()
        if writer is not None:
            writer.release()
        
        # GUARDAR JSON
        try:
            with open(save_path_json, 'w', encoding='utf-8') as f:
                json.dump(self.json_data, f, indent=2)
                
            self.processing_finished.emit({
                "output_dir": out_dir,
                "video_file": save_path_video,
                "json_file": save_path_json
            })
            
        except Exception as e:
            self.processing_finished.emit({"error": str(e)})