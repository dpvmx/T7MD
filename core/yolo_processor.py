"""
MODESYS YOLO Processor - V8.4.1
- Feat: Precision latency tracking (ms)
- Feat: Hardware device reporting for Advanced Stats
- Feat: Dynamic confidence thresholding and max_det increased to 1000 for dense crowds.
"""

import cv2
import numpy as np
from ultralytics import YOLO
import logging
import torch
import os
import time
from pathlib import Path

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
        self.stats_meta = {}

class YOLOProcessor:
    def __init__(self, config_manager):
        self.config = config_manager
        self.model_yolo = None
        self.model_face = None
        self.hud = None
        
        self.device = self._get_optimal_device()

        base_path = os.getcwd()
        self.models_dir = Path(base_path) / "models"
        
        try:
            from core.hud_renderer import HUDRenderer
            self.hud = HUDRenderer(config_manager)
        except Exception as e:
            logging.error(f"Error loading HUD Renderer: {e}")

        self._load_models()

    def _get_optimal_device(self):
        device = 'cpu'
        if torch.backends.mps.is_available():
            device = 'mps'
            print(f"🚀 MODESYS: METAL Acceleration (Mac GPU) Active")
        elif torch.cuda.is_available():
            device = 'cuda'
            print(f"🚀 MODESYS: CUDA Acceleration (Nvidia) Active")
        else:
            print(f"🐢 MODESYS: Running on CPU")
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
            name_world = "yolov8m-world.pt" 
            path_world = self.models_dir / name_world
            final_path_world = path_world if path_world.exists() else (Path(name_world) if Path(name_world).exists() else None)

            if final_path_world:
                self.model_yolo = YOLO(str(final_path_world))
                self.model_yolo.to(self.device)
            
            name_face = "yolov8m-face-lindevs.pt"
            path_face = self.models_dir / name_face
            final_path_face = path_face if path_face.exists() else (Path(name_face) if Path(name_face).exists() else None)

            if final_path_face:
                self.model_face = YOLO(str(final_path_face))
                self.model_face.to(self.device)
                
        except Exception as e:
            logging.critical(f"FATAL Error loading models: {e}")
        finally:
            torch.load = _original_torch_load

    def detect_frame(self, frame, use_faces, use_persons, use_objects, custom_classes):
        start_time = time.time()
        
        results = {"faces": [], "persons": [], "objects": [], "meta": {}}
        if frame is None: return results

        avg_conf = []

        # Get dynamic confidences from config
        face_conf = self.config.get("models.face_confidence", 0.4)
        target_conf = self.config.get("models.person_confidence", 0.25)

        if use_faces and self.model_face:
            try:
                # max_det increased to 1000 for crowds
                res = self.model_face.predict(frame, device=self.device, verbose=False, conf=face_conf, max_det=1000)[0]
                for box in res.boxes:
                    x1, y1, x2, y2 = box.xyxy[0].detach().cpu().numpy().tolist()
                    conf = float(box.conf.item())
                    cx, cy = int((x1+x2)/2), int((y1+y2)/2)
                    avg_conf.append(conf)
                    
                    results["faces"].append({
                        "bbox": [x1, y1, x2, y2], 
                        "label": "face", 
                        "confidence": conf, 
                        "center": (cx, cy),
                        "track_id": None
                    })
            except Exception as e: pass

        active_tags = []
        if (use_persons or use_objects) and self.model_yolo:
            try:
                active_prompts = []
                if use_persons: active_prompts.append("person")
                if use_objects and custom_classes:
                    active_prompts.extend([c.strip().lower() for c in custom_classes if c.strip()])

                final_classes = list(set(active_prompts))
                active_tags = final_classes

                if final_classes:
                    self.model_yolo.set_classes(final_classes)
                    # max_det increased to 1000 for crowds
                    res = self.model_yolo.predict(frame, device=self.device, verbose=False, conf=target_conf, max_det=1000)[0]
                    
                    for box in res.boxes:
                        x1, y1, x2, y2 = box.xyxy[0].detach().cpu().numpy().tolist()
                        conf = float(box.conf.item())
                        avg_conf.append(conf)
                        
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
                        
                        if label == "person":
                            results["persons"].append(item)
                        else:
                            results["objects"].append(item)

            except Exception as e: pass

        latency_ms = (time.time() - start_time) * 1000
        mean_conf = sum(avg_conf) / len(avg_conf) if avg_conf else 0.0
        
        results["meta"] = {
            "latency": latency_ms,
            "device": str(self.device).upper(),
            "avg_conf": mean_conf,
            "tags": active_tags
        }

        return results

    def _make_frame_result(self, frame, raw_detections, frame_number):
        flat = []
        for d in raw_detections.get("faces", []): 
            flat.append(Detection(d['bbox'], d['label'], d['confidence'], 'face', d['center'], d['track_id']))
        for d in raw_detections.get("persons", []): 
            flat.append(Detection(d['bbox'], d['label'], d['confidence'], 'person', d['center'], d['track_id']))
        for d in raw_detections.get("objects", []): 
            flat.append(Detection(d['bbox'], d['label'], d['confidence'], 'object', d['center'], d['track_id']))
            
        fr = FrameResult(frame, flat, frame_number)
        fr.stats_meta = raw_detections.get("meta", {})
        return fr

    def draw_detections(self, frame, raw_detections, frame_number, fps):
        if not self.hud: return frame
        frame_result = self._make_frame_result(frame, raw_detections, frame_number)
        return self.hud.render_hud(frame, frame_result, {"fps": fps})