"""
Motor de Video T7MD - V6.0 (Verbose Mode)
Feature: Logs detallados en terminal durante el renderizado.
"""

import cv2
import time
import os
import json
import logging
from pathlib import Path
from PySide6.QtCore import QThread, Signal
from core.yolo_processor import YOLOProcessor

class VideoEngine(QThread):
    progress_updated = Signal(int, int, int) 
    processing_finished = Signal(dict)
    error_occurred = Signal(str)

    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        self.video_path = ""
        self.output_dir = Path("output")
        self.is_paused = False
        self.should_stop = False
        self.processor = YOLOProcessor(config_manager)
        
    def setup_render(self, video_path):
        self.video_path = video_path
        out_conf = self.config_manager.get("output.output_dir")
        self.output_dir = Path(out_conf) if out_conf else Path(os.path.dirname(video_path)) / "T7MD_Output"
        custom_name = self.config_manager.get("output.custom_filename")
        if not custom_name: custom_name = Path(video_path).stem + "_processed"
        self.output_dir = self.output_dir / custom_name
        self.is_paused = False
        self.should_stop = False

    def update_config(self, config):
        self.config_manager = config
        self.processor.update_config(config)

    def pause(self): self.is_paused = not self.is_paused
    def stop(self): self.should_stop = True

    def _save_crop(self, frame, bbox, out_dir, label, frame_id, conf):
        try:
            x1, y1, x2, y2 = map(int, bbox)
            h, w = frame.shape[:2]
            x1=max(0,x1); y1=max(0,y1); x2=min(w,x2); y2=min(h,y2)
            if x2>x1 and y2>y1:
                crop = frame[y1:y2, x1:x2]
                fn = f"{label}_{frame_id:05d}_{int(conf*100)}.jpg"
                cv2.imwrite(str(out_dir / fn), crop)
        except: pass

    def run(self):
        logging.info(f"Iniciando motor de renderizado para: {self.video_path}")
        try:
            cap = cv2.VideoCapture(self.video_path)
            if not cap.isOpened(): raise Exception(f"No se pudo abrir: {self.video_path}")
            
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
            w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            profile = self.config_manager.get("output.profile", "Final Render")
            codec_name = self.config_manager.get("output.codec", "H.264")
            
            logging.info(f"Perfil: {profile} | Codec: {codec_name} | Resolución: {w}x{h} | Frames: {total_frames}")
            
            os.makedirs(self.output_dir, exist_ok=True)
            
            # --- Lógica de Perfiles ---
            save_crops_active = False
            path_layer_hud = None
            path_layer_bbox = None
            path_crops_faces = None
            
            if profile == "Compositing":
                save_crops_active = True
                path_layer_hud = self.output_dir / "seq_hud"
                path_layer_bbox = self.output_dir / "seq_bbox"
                path_crops_faces = self.output_dir / "crops_faces"
                
                os.makedirs(path_layer_hud, exist_ok=True)
                os.makedirs(path_layer_bbox, exist_ok=True)
                os.makedirs(path_crops_faces, exist_ok=True)
            
            if profile == "Final Render":
                save_crops_active = False

            # Video Writer
            out_video = None
            if profile != "JSON Only":
                ext = "mp4"
                fourcc = cv2.VideoWriter_fourcc(*'hvc1') if codec_name == "H.265" else cv2.VideoWriter_fourcc(*'avc1')
                out_path = self.output_dir / f"render_final.{ext}"
                out_video = cv2.VideoWriter(str(out_path), fourcc, fps, (w, h))

            json_data = {"video": self.video_path, "fps": fps, "frames": []}
            curr = 0
            
            while True:
                if self.should_stop: 
                    logging.warning("Renderizado detenido por el usuario.")
                    break
                while self.is_paused: time.sleep(0.1)
                
                ret, frame = cap.read()
                if not ret: break
                
                # Detectar
                detections = self.processor.detect_frame(
                    frame, 
                    self.config_manager.get("models.use_faces", True),
                    self.config_manager.get("models.use_persons", True),
                    self.config_manager.get("models.use_objects", True),
                    self.config_manager.get("models.custom_classes", [])
                )
                
                # --- VERBOSE LOGGING (DETALLADO) ---
                n_faces = len(detections.get("faces", []))
                n_persons = len(detections.get("persons", []))
                n_objects = len(detections.get("objects", []))
                pct = int((curr / total_frames) * 100)
                
                # Solo imprimir cada frame (muy verbose) o cada X frames si es demasiado rápido
                logging.info(f"[RENDER] Frame {curr:05d}/{total_frames} ({pct}%) | "
                             f"Detecciones: Caras={n_faces}, Personas={n_persons}, Objetos={n_objects}")
                # -----------------------------------

                # Renderizar
                if profile == "Final Render":
                    final_frame = self.processor.draw_detections(frame.copy(), detections, curr, fps)
                    out_video.write(final_frame)
                    
                elif profile == "Compositing":
                    final_frame = self.processor.draw_detections(frame.copy(), detections, curr, fps)
                    out_video.write(final_frame)
                    
                    if self.processor.hud:
                        res = self.processor._make_frame_result(frame, detections, curr)
                        res.frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        
                        img_bbox = self.processor.hud.render_layer(w, h, res, {"fps": fps}, "bbox")
                        cv2.imwrite(str(path_layer_bbox / f"bbox_{curr:05d}.png"), img_bbox)
                        
                        img_hud = self.processor.hud.render_layer(w, h, res, {"fps": fps}, "hud")
                        cv2.imwrite(str(path_layer_hud / f"hud_{curr:05d}.png"), img_hud)
                    
                    if save_crops_active:
                        for d in detections.get("faces", []):
                            self._save_crop(frame, d['bbox'], path_crops_faces, "face", curr, d['confidence'])

                json_data["frames"].append({"id": curr, "time": curr/fps, "data": detections})
                curr += 1
                self.progress_updated.emit(pct, curr, total_frames)

            cap.release()
            if out_video: out_video.release()
            
            with open(self.output_dir / "analysis.json", "w") as f:
                json.dump(json_data, f, indent=4)
            
            logging.info(f"Renderizado finalizado. Guardado en: {self.output_dir}")
            self.processing_finished.emit({"output_dir": str(self.output_dir)})
            
        except Exception as e:
            logging.error(f"Error Crítico en Render: {e}")
            self.error_occurred.emit(str(e))
        finally:
            self.should_stop = False