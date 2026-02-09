"""
Depth Processor T7MD - V8.2 (Anti-Flicker)
Feat: Depth Anything V2 + Temporal Smoothing
"""

import cv2
import torch
import numpy as np
import os
from PIL import Image

class DepthProcessor:
    def __init__(self, config_manager):
        self.config = config_manager
        self.device = self._get_optimal_device()
        self.pipe = None
        
        # --- ANTI-FLICKER VARIABLES ---
        self.prev_depth_map = None # Memoria del frame anterior
        # Alpha: Cuánto confiamos en el nuevo frame (0.0 a 1.0)
        # 1.0 = Sin suavizado (Flicker total)
        # 0.1 = Mucho suavizado (Efecto fantasma/Ghosting extremo)
        # 0.8 = Punto dulce (Quita ruido, mantiene movimiento)
        self.alpha = 0.8
        
        # Cargamos el modelo al iniciar
        self._load_model()

    def _get_optimal_device(self):
        # Detectar Mac MPS para aceleración
        if torch.backends.mps.is_available():
            print(f"🌊 Depth: Aceleración METAL (Mac GPU) Activada")
            return "mps"
        elif torch.cuda.is_available():
            print(f"🌊 Depth: Aceleración CUDA Activada")
            return "cuda"
        return "cpu"

    def _load_model(self):
        try:
            from transformers import pipeline
            print(f"⏳ Cargando Depth Anything V2 (Small)...")
            
            # Usamos el pipeline oficial de Transformers. 
            self.pipe = pipeline(
                task="depth-estimation", 
                model="depth-anything/Depth-Anything-V2-Small-hf", 
                device=self.device
            )
            
            print(f"✅ Modelo de Profundidad cargado en {self.device}")
            
        except Exception as e:
            print(f"❌ Error cargando Depth Model: {e}")
            print("Asegúrate de instalar: pip install transformers")

    def process_frame(self, frame):
        # Si el modelo falló, devolvemos gris plano para no romper el video
        if self.pipe is None: 
            return cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        try:
            # 1. Convertir BGR (OpenCV) a PIL Image (RGB)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(frame_rgb)
            
            # 2. Inferencia (Depth Anything V2)
            result = self.pipe(pil_image)
            raw_depth = result["depth"] # Objeto PIL Image
            
            # 3. Convertir a Array NumPy
            current_depth = np.array(raw_depth)

            # 4. Redimensionar AL TAMAÑO DEL VIDEO (Importante para pixel-perfect)
            # A veces el modelo devuelve un tamaño distinto, lo ajustamos antes de mezclar
            if current_depth.shape[:2] != frame.shape[:2]:
                current_depth = cv2.resize(current_depth, (frame.shape[1], frame.shape[0]))

            # ---------------------------------------------------------
            # 5. LÓGICA ANTI-FLICKER (Temporal Smoothing)
            # ---------------------------------------------------------
            # Convertimos a float32 para precisión matemática
            current_depth_f = current_depth.astype(np.float32)

            if self.prev_depth_map is None:
                # Primer frame: no hay con qué mezclar
                self.prev_depth_map = current_depth_f
            else:
                # Mezcla ponderada: 
                # Nuevo Estado = (Nuevo * Alpha) + (Viejo * (1 - Alpha))
                # cv2.addWeighted es muy rápido y optimizado en C++
                cv2.addWeighted(current_depth_f, self.alpha, self.prev_depth_map, (1 - self.alpha), 0, self.prev_depth_map)

            # ---------------------------------------------------------

            # 6. Convertir resultado final a uint8 (0-255)
            final_depth_uint8 = self.prev_depth_map.astype(np.uint8)

            # 7. Convertir a 3 canales (BGR) para video
            depth_bgr = cv2.cvtColor(final_depth_uint8, cv2.COLOR_GRAY2BGR)
            
            return depth_bgr

        except Exception as e:
            print(f"Error procesando frame depth: {e}")
            # Fallback en caso de error: devuelve original
            return frame