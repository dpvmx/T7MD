"""
Gestor de configuración JSON para T7MD Vision Pro
V5.9: Header Stats Custom + Ajustes de Texto.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional

class ConfigManager:
    def __init__(self, config_dir: Optional[str] = None):
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            self.config_dir = Path.home() / ".t7md_vision"
        
        self.config_dir.mkdir(exist_ok=True)
        self.config_file = self.config_dir / "config.json"
        
        self.default_config = {
            "version": "5.9.0",
            "models": {
                "use_faces": True,
                "use_persons": True,
                "use_objects": False,
                "custom_classes": ["cell phone", "laptop"],
                "face_confidence": 0.4,
                "person_confidence": 0.5,
                "object_confidence": 0.3
            },
            "modules": {
                "bboxes": {
                    "enabled": True,
                    "person_color": "#00FF00",
                    "person_thick": 2,
                    "face_color": "#00FFFF",
                    "face_thick": 2,
                    "object_color": "#FFFF00",
                    "object_thick": 2,
                    "label_scale": 100,
                    "label_text_color": "#000000",
                    "show_crosshair": True
                },
                "stats": {
                    "enabled": True,
                    "header_text": "T7MD VISION PRO", # NUEVO
                    "position": "top_left",
                    "scale": 100,
                    "text_color": "#FFFFFF",
                    "bg_color": "#000000",
                    "bg_opacity": 80
                },
                "minimap": {
                    "enabled": True,
                    "position": "top_right",
                    "scale": 100,
                    "border_thick": 1,
                    "border_color": "#FFFFFF",
                    "bg_color": "#000000",
                    "bg_opacity": 80,
                    "dot_size": 3
                },
                "collage": {
                    "enabled": True,
                    "position": "bottom_right",
                    "thumb_size_pct": 15,
                    "border_thick": 1,
                    "border_color": "#FFFFFF",
                    "gap_pct": 5,
                    "opacity": 80
                },
                "timecode": {
                    "enabled": True,
                    "position": "bottom_left",
                    "scale": 100,
                    "text_color": "#FFFFFF",
                    "bg_color": "#000000",
                    "bg_opacity": 80
                },
                "custom_msg": {
                    "enabled": False,
                    "text": "TRIPLESIETE\nPRODUCCIONES", # Multilinea default
                    "position": "bottom_center",
                    "scale": 100,
                    "text_color": "#FFFFFF",
                    "bg_color": "#000000",
                    "bg_opacity": 0
                }
            },
            "output": {
                "save_crops": True,
                "output_dir": "",
                "custom_filename": "",
                "profile": "Final Render",
                "codec": "H.264"
            },
            "style": { "global_margin": 40 }
        }
        
        self.config = self.default_config.copy()
        self.load_config()
    
    def load_config(self) -> bool:
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                self._merge_configs(loaded_config)
                return True
            except Exception: return False
        return False
    
    def save_config(self) -> bool:
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            return True
        except Exception: return False
    
    def _merge_configs(self, new_config: Dict[str, Any]) -> None:
        self._merge_configs_recursive(self.config, new_config)

    def _merge_configs_recursive(self, current_dict, new_dict):
        for key, value in new_dict.items():
            if key in current_dict and isinstance(current_dict[key], dict) and isinstance(value, dict):
                self._merge_configs_recursive(current_dict[key], value)
            else:
                current_dict[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        keys = key.split('.')
        value = self.config
        try:
            for k in keys: value = value[k]
            return value
        except (KeyError, TypeError): return default
    
    def set(self, key: str, value: Any) -> bool:
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]: config = config.setdefault(k, {})
        config[keys[-1]] = value
        return True
    
    def save_current_config(self): self.save_config()