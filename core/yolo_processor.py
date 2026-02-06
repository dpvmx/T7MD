"""
YOLO Processor T7MD - V6.5 (Custom Local Models)
Fix: Configurado para usar yolov8m-world.pt y yolov8m-face-lindevs.pt locales.
"""

import cv2
import numpy as np
from ultralytics import YOLO
import logging
import torch
from pathlib import Path
import sys

# Estructuras de datos para pasar al renderer
class Detection:
    def __init__(self, bbox, label, conf, type_id, center):
        self.bbox = bbox
        self.label = label
        self.confidence = conf
        self.type = type_id
        self.center = center

class FrameResult:
    def __init__(self, frame, detections, frame_number):
        self.frame = frame
        self.detections = detections
        self.frame_number = frame_number
        self.frame_rgb = None

class YOLOProcessor:
    def __init__(self, config_manager):
        self.config = config_manager
        self.model_yolo = None
        self.model_face = None
        self.hud = None
        
        # Carpeta de modelos
        self.models_dir = Path("models")
        # No forzamos creación si ya existe, confiamos en que el usuario puso los archivos ahí
        
        try:
            from core.hud_renderer import HUDRenderer
            self.hud = HUDRenderer(config_manager)
        except Exception as e:
            logging.error(f"Error cargando HUD Renderer: {e}")

        self._load_models()

    def update_config(self, config_manager):
        self.config = config_manager
        if self.hud:
            self.hud.config = config_manager

    def _load_models(self):
        """Carga modelos ESPECÍFICOS locales con parche de seguridad"""
        
        # --- PARCHE DE SEGURIDAD PYTORCH 2.6+ ---
        _original_torch_load = torch.load
        def safe_load_patch(*args, **kwargs):
            if 'weights_only' not in kwargs: kwargs['weights_only'] = False
            return _original_torch_load(*args, **kwargs)
        torch.load = safe_load_patch
        # ---------------------------

        try:
            # ==========================================
            # 1. CARGA MODELO YOLO-WORLD (MEDIUM)
            # ==========================================
            # Nombre exacto de tu archivo
            name_world = "yolov8m-world.pt" 
            path_world = self.models_dir / name_world
            
            if path_world.exists():
                logging.info(f"Cargando YOLO-World Local: {name_world}")
                self.model_yolo = YOLO(str(path_world))
            else:
                # Fallback: Intentar buscar en raíz si el usuario olvidó moverlo
                if Path(name_world).exists():
                    logging.info(f"Encontrado {name_world} en raíz, cargando...")
                    self.model_yolo = YOLO(name_world)
                else:
                    logging.error(f"❌ NO SE ENCONTRÓ {name_world} en la carpeta 'models/'. Detección de Objetos/Personas desactivada.")

            # ==========================================
            # 2. CARGA MODELO YOLO-FACE (LINDEVS MEDIUM)
            # ==========================================
            # Nombre exacto de tu archivo
            name_face = "yolov8m-face-lindevs.pt"
            path_face = self.models_dir / name_face

            if path_face.exists():
                logging.info(f"Cargando YOLO-Face Local: {name_face}")
                self.model_face = YOLO(str(path_face))
            else:
                # Fallback: Intentar buscar en raíz
                if Path(name_face).exists():
                    logging.info(f"Encontrado {name_face} en raíz, cargando...")
                    self.model_face = YOLO(name_face)
                else:
                    logging.error(f"❌ NO SE ENCONTRÓ {name_face} en la carpeta 'models/'. Detección de Caras desactivada.")
                    
            logging.info("Inicialización de modelos completada.")
            
        except Exception as e:
            logging.critical(f"Error FATAL cargando modelos: {e}")
        finally:
            torch.load = _original_torch_load

    def detect_frame(self, frame, use_faces, use_persons, use_objects, custom_classes):
        results = {"faces": [], "persons": [], "objects": []}
        if frame is None: return results

        # 1. Detección de Caras (Modelo Lindevs)
        if use_faces and self.model_face:
            try:
                # El modelo lindevs suele ser muy preciso
                res = self.model_face(frame, verbose=False, conf=0.4)[0]
                for box in res.boxes:
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    conf = float(box.conf[0])
                    # Verificamos clase 0 (Face)
                    cls = int(box.cls[0])
                    if cls == 0: 
                        cx, cy = int((x1+x2)/2), int((y1+y2)/2)
                        results["faces"].append({
                            "bbox": [x1, y1, x2, y2], "label": "Face", "confidence": conf, "center": (cx, cy)
                        })
            except Exception as e: logging.error(f"Error deteccion caras: {e}")

        # 2. Detección Personas / Objetos (YOLO World)
        if (use_persons or use_objects) and self.model_yolo:
            try:
                classes_to_detect = []
                if use_persons: classes_to_detect.append("person")
                if use_objects: classes_to_detect.extend(custom_classes)
                
                if classes_to_detect:
                    self.model_yolo.set_classes(classes_to_detect)
                    res = self.model_yolo(frame, verbose=False, conf=0.3)[0]
                    for box in res.boxes:
                        x1, y1, x2, y2 = box.xyxy[0].tolist()
                        conf = float(box.conf[0])
                        label = res.names[int(box.cls[0])]
                        cx, cy = int((x1+x2)/2), int((y1+y2)/2)
                        item = {"bbox": [x1, y1, x2, y2], "label": label, "confidence": conf, "center": (cx, cy)}
                        
                        if label == "person": results["persons"].append(item)
                        else: results["objects"].append(item)
            except Exception as e: logging.error(f"Error deteccion objetos: {e}")

        return results

    def _make_frame_result(self, frame, raw_detections, frame_number):
        flat = []
        for d in raw_detections.get("faces", []): flat.append(Detection(d['bbox'], d['label'], d['confidence'], 'face', d['center']))
        for d in raw_detections.get("persons", []): flat.append(Detection(d['bbox'], d['label'], d['confidence'], 'person', d['center']))
        for d in raw_detections.get("objects", []): flat.append(Detection(d['bbox'], d['label'], d['confidence'], 'object', d['center']))
        return FrameResult(frame, flat, frame_number)

    def draw_detections(self, frame, raw_detections, frame_number, fps):
        if not self.hud: return frame
        frame_result = self._make_frame_result(frame, raw_detections, frame_number)
        return self.hud.render_hud(frame, frame_result, {"fps": fps})