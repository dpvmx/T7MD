import cv2
import time
import json
import os
import urllib.parse
from PySide6.QtCore import QThread, Signal
from core.yolo_processor import YOLOProcessor

# Intentamos importar el procesador de profundidad
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
        self.processor = YOLOProcessor(config_manager)
        self.depth_processor = None 

    def setup_render(self, video_path):
        self.video_path = video_path
        self.running = True
        self.paused = False
        
        if DepthProcessor:
            if self.depth_processor is None:
                try:
                    self.depth_processor = DepthProcessor(self.config)
                    print("✅ DepthProcessor inicializado correctamente.")
                except Exception as e:
                    print(f"❌ Error iniciando DepthProcessor: {e}")

    def run(self):
        final_path = self.video_path
        if not os.path.exists(final_path):
            decoded_path = urllib.parse.unquote(self.video_path)
            if os.path.exists(decoded_path): final_path = decoded_path

        if not os.path.exists(final_path):
            self.processing_finished.emit({"error": f"Invalid path: {final_path}"})
            return

        self.video_path = final_path
        cap = cv2.VideoCapture(self.video_path)
        
        if not cap.isOpened():
            self.processing_finished.emit({"error": "Could not open video file"})
            return
        
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames == 0: total_frames = 1

        out_conf = self.config.get("output")
        filename = out_conf.get("custom_filename") or f"T7MD_{int(time.time())}"
        out_dir = out_conf.get("output_dir", "outputs")
        
        project_dir = os.path.join(out_dir, filename)
        os.makedirs(project_dir, exist_ok=True)
        
        save_path_json = os.path.join(project_dir, f"{filename}.json")
        save_path_video = os.path.join(project_dir, f"{filename}.mp4")
        save_path_depth = os.path.join(project_dir, f"{filename}_depth.mp4")
        
        profile = out_conf.get("profile", "Final Render")
        is_compositing = (profile == "Compositing Ready")
        is_json_only = (profile == "JSON Only")
        save_crops = out_conf.get("save_crops", True)

        # Estructura de subcarpetas profesional para Compositing
        comp_dirs = {}
        if is_compositing:
            bbox_base = os.path.join(project_dir, "BBoxes")
            hud_base = os.path.join(project_dir, "HUD_Elements")
            
            comp_dirs = {
                "bbox_faces": os.path.join(bbox_base, "seq_faces"),
                "bbox_persons": os.path.join(bbox_base, "seq_persons"),
                "bbox_objects": os.path.join(bbox_base, "seq_objects"),
                "constellation": os.path.join(hud_base, "seq_constellation"),
                "minimap": os.path.join(hud_base, "seq_minimap"),
                "stats": os.path.join(hud_base, "seq_stats"),
                "timecode": os.path.join(hud_base, "seq_timecode"),
                "custom_msg": os.path.join(hud_base, "seq_custom_msg"),
                "collage": os.path.join(hud_base, "seq_collage"),
                "crops_faces": os.path.join(project_dir, "crops_faces")
            }
            for d in comp_dirs.values():
                os.makedirs(d, exist_ok=True)
        
        use_depth = self.config.get("models.use_depth", False)

        writer = None
        writer_depth = None 

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        try:
            if out_conf.get("codec") == "H.265": fourcc = cv2.VideoWriter_fourcc(*'hevc')
        except: pass

        if not is_json_only:
            writer = cv2.VideoWriter(save_path_video, fourcc, fps, (width, height))
            
        if use_depth and self.depth_processor and not is_json_only:
            writer_depth = cv2.VideoWriter(save_path_depth, fourcc, fps, (width, height))

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
            if not ret: break

            raw_detections = self.processor.detect_frame(
                frame, use_faces, use_persons, use_objects, custom_classes
            )

            if writer_depth is not None:
                try:
                    depth_frame = self.depth_processor.process_frame(frame)
                    writer_depth.write(depth_frame)
                except Exception: pass

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
                    "track_id": d.get('track_id'),
                    "rect": { "w": float(w_box), "h": float(h_box), "cx": float(x1 + w_box/2), "cy": float(y1 + h_box/2) }
                }
                frame_entry["detections"].append(det_entry)
            
            self.json_data["frames"].append(frame_entry)

            if not is_json_only:
                if is_compositing and self.processor.hud:
                    frame_result = self.processor._make_frame_result(frame, raw_detections, frame_idx)
                    frame_result.frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    video_info = {"fps": fps}
                    
                    # 1. Exportación BBox Separada
                    if self.config.get("modules.bboxes.enabled", True):
                        img_f = self.processor.hud.render_layer(width, height, frame_result, video_info, "bbox_faces")
                        cv2.imwrite(os.path.join(comp_dirs["bbox_faces"], f"faces_{frame_idx:05d}.png"), img_f)
                        
                        img_p = self.processor.hud.render_layer(width, height, frame_result, video_info, "bbox_persons")
                        cv2.imwrite(os.path.join(comp_dirs["bbox_persons"], f"persons_{frame_idx:05d}.png"), img_p)
                        
                        img_o = self.processor.hud.render_layer(width, height, frame_result, video_info, "bbox_objects")
                        cv2.imwrite(os.path.join(comp_dirs["bbox_objects"], f"objects_{frame_idx:05d}.png"), img_o)
                    
                    # 2. Exportación Constellation
                    if self.config.get("modules.constellation.enabled", False):
                        img_c = self.processor.hud.render_layer(width, height, frame_result, video_info, "constellation")
                        cv2.imwrite(os.path.join(comp_dirs["constellation"], f"const_{frame_idx:05d}.png"), img_c)
                    
                    # 3. Exportación HUD Individual
                    hud_modules = ["minimap", "stats", "timecode", "custom_msg", "collage"]
                    for mod in hud_modules:
                        if self.config.get(f"modules.{mod}.enabled", False):
                            img_h = self.processor.hud.render_layer(width, height, frame_result, video_info, mod)
                            cv2.imwrite(os.path.join(comp_dirs[mod], f"{mod}_{frame_idx:05d}.png"), img_h)
                    
                    # 4. Crops
                    if save_crops:
                        for i, face_det in enumerate(raw_detections.get("faces", [])):
                            fx1, fy1, fx2, fy2 = map(int, face_det["bbox"])
                            fx1, fy1 = max(0, fx1), max(0, fy1)
                            fx2, fy2 = min(width, fx2), min(height, fy2)
                            if fx2 > fx1 and fy2 > fy1:
                                crop = frame[fy1:fy2, fx1:fx2]
                                cv2.imwrite(os.path.join(comp_dirs["crops_faces"], f"frame_{frame_idx:05d}_face_{i}.jpg"), crop)
                                
                if writer is not None:
                    processed_frame = self.processor.draw_detections(frame, raw_detections, frame_idx, fps)
                    writer.write(processed_frame)

            frame_idx += 1
            progress = int((frame_idx / total_frames) * 100)
            self.progress_updated.emit(progress, frame_idx, fps)

        cap.release()
        if writer is not None: writer.release()
        if writer_depth is not None: writer_depth.release()
        
        try:
            with open(save_path_json, 'w', encoding='utf-8') as f:
                json.dump(self.json_data, f, indent=2)
            
            result_data = {
                "output_dir": project_dir, 
                "json_file": save_path_json
            }
            if not is_json_only: 
                result_data["video_file"] = save_path_video
            if writer_depth:
                result_data["depth_file"] = save_path_depth
                
            self.processing_finished.emit(result_data)
        except Exception as e:
            self.processing_finished.emit({"error": str(e)})