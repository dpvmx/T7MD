"""
Cargador de modelos YOLO compatible con PyTorch 2.6+
"""

import torch
from ultralytics import YOLO, YOLOWorld
import warnings
import os

class ModelLoader:
    """Gestor de modelos YOLO con compatibilidad PyTorch 2.6+"""
    
    def __init__(self, device=None):
        self.device = device or self._get_device()
        self.models = {}
        print(f"🚀 ModelLoader inicializado para: {self.device}")
    
    def _get_device(self):
        """Determinar el mejor dispositivo disponible"""
        if torch.backends.mps.is_available():
            return "mps"
        elif torch.cuda.is_available():
            return "cuda"
        else:
            return "cpu"
    
    def safe_load_model(self, model_path, model_type="yolo"):
        """
        Cargar modelo de forma segura para PyTorch 2.6+
        
        Args:
            model_path: Ruta al archivo .pt
            model_type: "yolo" o "world"
        
        Returns:
            Modelo cargado o None si falla
        """
        if not os.path.exists(model_path):
            print(f"⚠️ Modelo no encontrado: {model_path}")
            return None
        
        try:
            print(f"📦 Cargando modelo: {os.path.basename(model_path)}")
            
            # Primero intentar carga normal
            if model_type == "world":
                model = YOLOWorld(model_path)
            else:
                model = YOLO(model_path)
            
            # Mover al dispositivo
            model.to(self.device)
            print(f"✅ Modelo cargado en {self.device}")
            return model
            
        except Exception as e:
            print(f"⚠️ Error cargando modelo {model_path}: {str(e)[:100]}...")
            
            # Si es error de weights_only, intentar carga alternativa
            if "weights_only" in str(e):
                return self._load_with_weights_only_false(model_path, model_type)
            
            return None
    
    def _load_with_weights_only_false(self, model_path, model_type):
        """Cargar modelo con weights_only=False (menos seguro pero necesario)"""
        print(f"🔄 Intentando carga con weights_only=False...")
        
        try:
            # Importar aquí para evitar problemas circulares
            import torch
            from ultralytics.nn.tasks import DetectionModel
            
            # Agregar las clases necesarias a la lista segura
            torch.serialization.add_safe_globals([DetectionModel])
            
            # Cargar con weights_only=False
            checkpoint = torch.load(model_path, map_location=self.device, weights_only=false)
            
            # Crear modelo y cargar pesos
            if model_type == "world":
                model = YOLOWorld(model_path)
            else:
                model = YOLO(model_path)
            
            # Cargar pesos manualmente
            model.model.load_state_dict(checkpoint, strict=False)
            model.to(self.device)
            
            print(f"✅ Modelo cargado con weights_only=False")
            return model
            
        except Exception as e:
            print(f"❌ Error en carga alternativa: {e}")
            return None
    
    def load_base_model(self):
        """Cargar modelo base YOLOv8m"""
        model_path = "models/yolov8m.pt"
        
        if model_path in self.models:
            return self.models[model_path]
        
        model = self.safe_load_model(model_path, "yolo")
        if model:
            self.models[model_path] = model
        
        return model
    
    def load_face_model(self):
        """Cargar modelo de detección de caras"""
        model_path = "models/yolov8m-face-lindevs.pt"
        
        if not os.path.exists(model_path):
            print("⚠️ Modelo de caras no encontrado. Saltando...")
            return None
        
        if model_path in self.models:
            return self.models[model_path]
        
        model = self.safe_load_model(model_path, "yolo")
        if model:
            self.models[model_path] = model
        
        return model
    
    def load_world_model(self):
        """Cargar modelo YOLO-World"""
        model_path = "models/yolov8s-world.pt"
        
        if not os.path.exists(model_path):
            print("⚠️ Modelo YOLO-World no encontrado. Saltando...")
            return None
        
        if model_path in self.models:
            return self.models[model_path]
        
        model = self.safe_load_model(model_path, "world")
        if model:
            self.models[model_path] = model
        
        return model
    
    def get_available_models(self):
        """Obtener lista de modelos disponibles"""
        available = []
        
        if os.path.exists("models/yolov8m.pt"):
            available.append("base")
        
        if os.path.exists("models/yolov8m-face-lindevs.pt"):
            available.append("face")
        
        if os.path.exists("models/yolov8s-world.pt"):
            available.append("world")
        
        return available
    
    def unload_model(self, model_path):
        """Descargar modelo de memoria"""
        if model_path in self.models:
            del self.models[model_path]
            torch.cuda.empty_cache() if torch.cuda.is_available() else None
            print(f"✅ Modelo descargado: {model_path}")