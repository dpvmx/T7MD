"""
Procesador de video para T7MD Vision Pro
Maneja la detección de objetos, personas y caras usando YOLO.
"""

import cv2
import torch
import numpy as np
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any
from dataclasses import dataclass
from enum import Enum

from ultralytics import YOLO, YOLOWorld

class DetectionType(Enum):
    """Tipos de detección disponibles"""
    FACES = "faces"
    PERSONS = "persons"
    OBJECTS = "objects"

@dataclass
class Detection:
    """Datos de una detección individual"""
    type: DetectionType
    label: str
    confidence: float
    bbox: Tuple[int, int, int, int]  # x1, y1, x2, y2
    center: Tuple[int, int]
    dimensions: Tuple[int, int]

@dataclass
class FrameResult:
    """Resultados de procesamiento de un frame"""
    frame_number: int
    frame_rgb: np.ndarray
    detections: List[Detection]
    processing_time: float

class VideoProcessor:
    """Procesador de video con soporte para múltiples modelos YOLO"""
    
    def __init__(self, config_manager):
        self.config = config_manager
        self.device = self._get_device()
        self.models = {}
        self.current_video_path = None
        self.cap = None
        self.video_info = {}
        
        print(f"✅ VideoProcessor inicializado en dispositivo: {self.device}")
    
    def _get_device(self) -> str:
        """Determinar el dispositivo a utilizar (MPS, CUDA o CPU)"""
        if torch.backends.mps.is_available():
            return "mps"
        elif torch.cuda.is_available():
            return "cuda"
        else:
            return "cpu"
    
    def load_models(self) -> bool:
        """Cargar modelos según configuración actual"""
        try:
            models_loaded = 0
            
            # Modelo base (personas y objetos COCO)
            if self.config.get("models.use_base", True):
                print("📦 Cargando modelo base (yolov8m.pt)...")
                self.models["base"] = YOLO("models/yolov8m.pt").to(self.device)
                models_loaded += 1
                print("   ✅ Modelo base cargado")
            
            # Modelo de caras
            if self.config.get("models.use_faces", True):
                face_model_path = Path("models/yolov8m-face-lindevs.pt")
                if face_model_path.exists():
                    print("📦 Cargando modelo de caras...")
                    self.models["faces"] = YOLO(str(face_model_path)).to(self.device)
                    models_loaded += 1
                    print("   ✅ Modelo de caras cargado")
                else:
                    print("   ⚠️  Modelo de caras no encontrado, desactivado")
            
            # Modelo YOLO-World (objetos personalizados)
            if self.config.get("models.use_world", False):
                print("📦 Cargando modelo YOLO-World...")
                self.models["world"] = YOLOWorld("models/yolov8s-world.pt").to(self.device)
                
                # Configurar clases personalizadas
                custom_classes = ["person", "car", "dog", "backpack", "phone", "firearm", "knife", "drone"]
                self.models["world"].set_classes(custom_classes)
                models_loaded += 1
                print("   ✅ Modelo YOLO-World cargado")
            
            print(f"✅ {models_loaded} modelos cargados exitosamente")
            return True
            
        except Exception as e:
            print(f"❌ Error al cargar modelos: {e}")
            return False
    
    def load_video(self, video_path: str) -> Optional[Dict[str, Any]]:
        """Cargar video para procesamiento"""
        try:
            self.current_video_path = video_path
            self.cap = cv2.VideoCapture(video_path)
            
            if not self.cap.isOpened():
                print(f"❌ No se pudo abrir el video: {video_path}")
                return None
            
            # Obtener información del video
            self.video_info = {
                "width": int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                "height": int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                "fps": self.cap.get(cv2.CAP_PROP_FPS),
                "total_frames": int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT)),
                "duration": int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT) / self.cap.get(cv2.CAP_PROP_FPS)),
                "codec": int(self.cap.get(cv2.CAP_PROP_FOURCC))
            }
            
            print(f"✅ Video cargado: {Path(video_path).name}")
            print(f"   Resolución: {self.video_info['width']}x{self.video_info['height']}")
            print(f"   FPS: {self.video_info['fps']:.2f}")
            print(f"   Duración: {self.video_info['duration']:.2f}s")
            print(f"   Frames: {self.video_info['total_frames']}")
            
            # Asegurar que los modelos están cargados
            if not self.models:
                self.load_models()
            
            return self.video_info
            
        except Exception as e:
            print(f"❌ Error al cargar video: {e}")
            return None
    
    def get_frame(self, frame_number: int = 0) -> Optional[np.ndarray]:
        """Obtener un frame específico del video"""
        if not self.cap or not self.cap.isOpened():
            return None
        
        # Establecer posición de frame
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = self.cap.read()
        
        if ret:
            # Convertir BGR a RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            return frame_rgb
        
        return None
    
    def process_frame(self, frame_rgb: np.ndarray, frame_number: int = 0) -> FrameResult:
        """Procesar un solo frame con detecciones"""
        import time
        start_time = time.time()
        
        frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
        all_detections = []
        
        # Umbrales de confianza
        face_conf = self.config.get("models.face_confidence", 0.4)
        person_conf = self.config.get("models.person_confidence", 0.3)
        object_conf = self.config.get("models.object_confidence", 0.25)
        
        # 1. Detectar caras (si el modelo está cargado)
        if "faces" in self.models and self.config.get("models.use_faces", True):
            face_results = self.models["faces"](frame_bgr, verbose=False, conf=face_conf)[0]
            
            for box in face_results.boxes:
                conf = box.conf.item()
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                w, h = x2 - x1, y2 - y1
                
                detection = Detection(
                    type=DetectionType.FACES,
                    label="Face",
                    confidence=conf,
                    bbox=(x1, y1, x2, y2),
                    center=(cx, cy),
                    dimensions=(w, h)
                )
                all_detections.append(detection)
        
        # 2. Detectar personas y objetos COCO (modelo base)
        if "base" in self.models and self.config.get("models.use_base", True):
            base_results = self.models["base"](frame_bgr, verbose=False, conf=person_conf)[0]
            
            for box in base_results.boxes:
                conf = box.conf.item()
                cls_id = int(box.cls.item())
                cls_name = self.models["base"].names[cls_id]
                
                # Filtrar solo personas o todos los objetos según configuración
                if cls_name == "person" or self.config.get("models.use_objects", True):
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                    w, h = x2 - x1, y2 - y1
                    
                    detection_type = DetectionType.PERSONS if cls_name == "person" else DetectionType.OBJECTS
                    
                    detection = Detection(
                        type=detection_type,
                        label=cls_name,
                        confidence=conf,
                        bbox=(x1, y1, x2, y2),
                        center=(cx, cy),
                        dimensions=(w, h)
                    )
                    all_detections.append(detection)
        
        # 3. Detectar objetos con YOLO-World (si está habilitado)
        if "world" in self.models and self.config.get("models.use_world", False):
            world_results = self.models["world"](frame_bgr, verbose=False, conf=object_conf)[0]
            
            for box in world_results.boxes:
                conf = box.conf.item()
                cls_id = int(box.cls.item())
                cls_name = self.models["world"].names[cls_id]
                
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                w, h = x2 - x1, y2 - y1
                
                detection = Detection(
                    type=DetectionType.OBJECTS,
                    label=cls_name,
                    confidence=conf,
                    bbox=(x1, y1, x2, y2),
                    center=(cx, cy),
                    dimensions=(w, h)
                )
                all_detections.append(detection)
        
        processing_time = time.time() - start_time
        
        return FrameResult(
            frame_number=frame_number,
            frame_rgb=frame_rgb,
            detections=all_detections,
            processing_time=processing_time
        )
    
    def draw_detections(self, frame_result: FrameResult, hud_config: Dict[str, Any]) -> np.ndarray:
        """Dibujar detecciones en un frame según configuración del HUD"""
        frame = frame_result.frame_rgb.copy()
        
        # Si no mostrar bboxes, retornar frame original
        if not hud_config.get("show_bboxes", True):
            return frame
        
        # Configuración de colores
        colors = {
            DetectionType.FACES: self._hex_to_rgb(hud_config.get("bbox_color", "#00FF00")),
            DetectionType.PERSONS: (255, 255, 255),  # Blanco para personas
            DetectionType.OBJECTS: (255, 255, 0)     # Amarillo para objetos
        }
        
        # Dibujar cada detección
        for detection in frame_result.detections:
            # Verificar si mostrar este tipo de detección
            det_type = detection.type.value
            if not hud_config.get(f"show_{det_type}", True):
                continue
            
            # Obtener color
            color = colors.get(detection.type, (0, 255, 0))
            
            # Dibujar bounding box
            x1, y1, x2, y2 = detection.bbox
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            
            # Dibujar etiqueta
            label = f"{detection.label}: {detection.confidence:.2f}"
            label_size, baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            
            # Fondo para la etiqueta
            cv2.rectangle(
                frame,
                (x1, y1 - label_size[1] - 5),
                (x1 + label_size[0], y1),
                color,
                -1
            )
            
            # Texto de la etiqueta
            cv2.putText(
                frame,
                label,
                (x1, y1 - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 0, 0) if detection.type == DetectionType.PERSONS else (255, 255, 255),
                1
            )
        
        return frame
    
    def process_preview(self, frame_number: int = 0) -> Optional[Tuple[np.ndarray, FrameResult]]:
        """Procesar un frame para vista previa"""
        if not self.cap or not self.cap.isOpened():
            return None
        
        # Obtener frame
        frame_rgb = self.get_frame(frame_number)
        if frame_rgb is None:
            return None
        
        # Procesar detecciones
        frame_result = self.process_frame(frame_rgb, frame_number)
        
        # Obtener configuración del HUD
        hud_config = {
            "show_bboxes": self.config.get("hud.show_bboxes", True),
            "show_faces": self.config.get("hud.show_faces", True),
            "show_persons": self.config.get("hud.show_persons", True),
            "show_objects": self.config.get("hud.show_objects", True),
            "bbox_color": self.config.get("hud.bbox_color", "#00FF00")
        }
        
        # Dibujar detecciones
        frame_with_detections = self.draw_detections(frame_result, hud_config)
        
        return frame_with_detections, frame_result
    
    def release(self):
        """Liberar recursos"""
        if self.cap:
            self.cap.release()
        self.models.clear()
        print("✅ Recursos del VideoProcessor liberados")
    
    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """Convertir color hex a RGB"""
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 6:
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        else:
            return (0, 255, 0)  # Verde por defecto