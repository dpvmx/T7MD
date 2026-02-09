"""
YOLO Processor T7MD - V8.1
- Fix: Indentation Error
- Feat: Unified Prompt Logic (Person/Object conflict resolved)
- Feat: MPS Acceleration Enabled
"""

import cv2
import numpy as np
from ultralytics import YOLO
import logging
import torch
import os
import sys
from pathlib import Path

# Estructuras de datos 
class Detection:
    def __init__(self, bbox, label, conf, type_id, center, track_id=None):
        self.bbox = bbox
        self.label = label
        self.confidence = conf
        self.type = type_id
        self.center = center
        self.track_id = track_id

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
        
        # 1. Device Auto-detect
        self.device = self._get_optimal_device()

        # 2. Paths
        base_path = os.getcwd()
        self.models_dir = Path(base_path) / "models"
        
        # 3. HUD
        try:
            from core.hud_renderer import HUDRenderer
            self.hud = HUDRenderer(config_manager)
        except Exception as e:
            logging.error(f"Error cargando HUD Renderer: {e}")

        # 4. Load Models
        self._load_models()

    def _get_optimal_device(self):
        device = 'cpu'
        if torch.backends.mps.is_available():
            device = 'mps'
            print(f"🚀 T7MD: Aceleración METAL (Mac GPU) Activada")
        elif torch.cuda.is_available():
            device = 'cuda'
            print(f"🚀 T7MD: Aceleración CUDA (Nvidia) Activada")
        else:
            print(f"🐢 T7MD: Corriendo en CPU")
        return device

    def update_config(self, config_manager):
        self.config = config_manager
        if self.hud:
            self.hud.config = config_manager

    def _load_models(self):
        _original_torch_load = torch.load
        def safe_load_patch(*args, **kwargs):
            if 'weights_only' not in kwargs: kwargs['weights_only'] = False
            return _original_torch_load(*args, **kwargs)
        torch.load = safe_load_patch

        try:
            # YOLO-WORLD
            name_world = "yolov8m-world.pt" 
            path_world = self.models_dir / name_world
            final_path_world = path_world if path_world.exists() else (Path(name_world) if Path(name_world).exists() else None)

            if final_path_world:
                logging.info(f"Cargando YOLO-World: {final_path_world}")
                self.model_yolo = YOLO(str(final_path_world))
                self.model_yolo.to(self.device)
            else:
                logging.error(f"❌ NO SE ENCONTRÓ {name_world}")

            # YOLO-FACE
            name_face = "yolov8m-face-lindevs.pt"
            path_face = self.models_dir / name_face
            final_path_face = path_face if path_face.exists() else (Path(name_face) if Path(name_face).exists() else None)

            if final_path_face:
                logging.info(f"Cargando YOLO-Face: {final_path_face}")
                self.model_face = YOLO(str(final_path_face))
                self.model_face.to(self.device)
            else:
                logging.error(f"❌ NO SE ENCONTRÓ {name_face}")
                
        except Exception as e:
            logging.critical(f"Error FATAL cargando modelos: {e}")
        finally:
            torch.load = _original_torch_load

    def detect_frame(self, frame, use_faces, use_persons, use_objects, custom_classes):
        results = {"faces": [], "persons": [], "objects": []}
        if frame is None: return results

        # 1. Detección de Caras (Modelo Independiente)
        if use_faces and self.model_face:
            try:
                res = self.model_face.predict(frame, device=self.device, verbose=False, conf=0.4)[0]
                for box in res.boxes:
                    x1, y1, x2, y2 = box.xyxy[0].detach().cpu().numpy().tolist()
                    conf = float(box.conf.item())
                    cx, cy = int((x1+x2)/2), int((y1+y2)/2)
                    
                    results["faces"].append({
                        "bbox": [x1, y1, x2, y2], 
                        "label": "face", 
                        "confidence": conf, 
                        "center": (cx, cy),
                        "track_id": None
                    })
            except Exception as e: logging.error(f"Error caras: {e}")

        # 2. Detección Unificada (Personas + Objetos)
        if (use_persons or use_objects) and self.model_yolo:
            try:
                # Recopilar todos los prompts en una sola lista para evitar conflictos
                active_prompts = []

                # A. Prompt de Personas (Checkbox)
                if use_persons:
                    active_prompts.append("person")

                # B. Prompt de Objetos (Texto Usuario)
                if use_objects and custom_classes:
                    cleaned_text = [c.strip().lower() for c in custom_classes if c.strip()]
                    active_prompts.extend(cleaned_text)

                # C. Eliminar duplicados (Set)
                final_classes = list(set(active_prompts))

                if final_classes:
                    self.model_yolo.set_classes(final_classes)
                    
                    # Usamos .predict (Modo Estabilidad sin 'lap')
                    res = self.model_yolo.predict(frame, device=self.device, verbose=False, conf=0.25)[0]
                    
                    for box in res.boxes:
                        x1, y1, x2, y2 = box.xyxy[0].detach().cpu().numpy().tolist()
                        conf = float(box.conf.item())
                        
                        cls_id = int(box.cls.item())
                        label = self.model_yolo.names[cls_id] if (self.model_yolo.names and cls_id in self.model_yolo.names) else "unknown"
                        cx, cy = int((x1+x2)/2), int((y1+y2)/2)
                        
                        item = {
                            "bbox": [x1, y1, x2, y2], 
                            "label": label, 
                            "confidence": conf, 
                            "center": (cx, cy),
                            "track_id": None
                        }
                        
                        # Clasificación de Salida:
                        # Si es "person", va a la lista de personas (AZUL).
                        # Cualquier otra cosa, a objetos (VERDE).
                        if label == "person":
                            results["persons"].append(item)
                        else:
                            results["objects"].append(item)

            except Exception as e: 
                logging.error(f"Error YOLO-World: {e}")

        return results

    def _make_frame_result(self, frame, raw_detections, frame_number):
        flat = []
        for d in raw_detections.get("faces", []): 
            flat.append(Detection(d['bbox'], d['label'], d['confidence'], 'face', d['center'], d['track_id']))
        for d in raw_detections.get("persons", []): 
            flat.append(Detection(d['bbox'], d['label'], d['confidence'], 'person', d['center'], d['track_id']))
        for d in raw_detections.get("objects", []): 
            flat.append(Detection(d['bbox'], d['label'], d['confidence'], 'object', d['center'], d['track_id']))
        return FrameResult(frame, flat, frame_number)

    def draw_detections(self, frame, raw_detections, frame_number, fps):
        if not self.hud: return frame
        frame_result = self._make_frame_result(frame, raw_detections, frame_number)
        return self.hud.render_hud(frame, frame_result, {"fps": fps})