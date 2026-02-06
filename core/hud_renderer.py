"""
Renderizador de HUD Profesional T7MD v6.1 (Debug Active)
Fix: Dibuja BBoxes correctamente usando lista plana de objetos.
"""

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import platform
import logging

class HUDRenderer:
    def __init__(self, config_manager):
        self.config = config_manager
        self.font_path = Path("fonts/telegrama.otf")
        self.REF_H = 1080.0 
    
    def _get_font(self, size_px: int) -> ImageFont.FreeTypeFont:
        final_size = max(10, int(size_px))
        if self.font_path.exists():
            try: return ImageFont.truetype(str(self.font_path), final_size)
            except: pass
        try:
            sys_font = "Arial.ttf" if platform.system() == "Windows" else "Arial"
            return ImageFont.truetype(sys_font, final_size)
        except: pass
        return ImageFont.load_default()

    def _get_responsive_size(self, base_px, current_h, scale_pct=100):
        res_factor = current_h / self.REF_H
        user_factor = scale_pct / 100.0
        return int(base_px * res_factor * user_factor)

    def _get_anchor_pos(self, w_screen, h_screen, w_elem, h_elem, pos_name):
        margin_base = self.config.get("style.global_margin", 40)
        margin = self._get_responsive_size(margin_base, h_screen)
        x, y = margin, margin
        try:
            if "left" in pos_name: x = margin
            elif "right" in pos_name: x = w_screen - w_elem - margin
            else: x = (w_screen - w_elem) // 2
            if "top" in pos_name: y = margin
            elif "bottom" in pos_name: y = h_screen - h_elem - margin
            else: y = (h_screen - h_elem) // 2
        except: pass
        return int(x), int(y)

    def _hex_to_rgb(self, hex_color):
        if not hex_color: return (255, 255, 255)
        try:
            hex_color = hex_color.lstrip('#')
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        except: return (255, 255, 255)

    def _draw_bboxes(self, draw, h_screen, detections):
        """Dibuja las cajas delimitadoras (BBoxes)"""
        try:
            cfg = self.config.get("modules.bboxes", {})
            if not cfg.get("enabled", True): return
            
            # Si no hay detecciones, salir
            if not detections: return

            for det in detections:
                t = str(det.type).lower()
                color = "#FFFFFF"
                thickness = 2
                
                # Seleccion de estilo
                if "face" in t: 
                    color = cfg.get("face_color", "#00FFFF")
                    thickness = int(cfg.get("face_thick", 2))
                elif "person" in t: 
                    color = cfg.get("person_color", "#00FF00")
                    thickness = int(cfg.get("person_thick", 2))
                elif "object" in t: 
                    color = cfg.get("object_color", "#FFFF00")
                    thickness = int(cfg.get("object_thick", 2))
                
                c_rgb = self._hex_to_rgb(color)
                
                # Caja
                draw.rectangle(det.bbox, outline=c_rgb + (255,), width=thickness)
                
                # Crosshair
                if cfg.get("show_crosshair", True):
                    cx, cy = det.center
                    ch = 10
                    draw.line([(cx - ch, cy), (cx + ch, cy)], fill=c_rgb + (200,), width=thickness)
                    draw.line([(cx, cy - ch), (cx, cy + ch)], fill=c_rgb + (200,), width=thickness)
                
                # Etiqueta
                label = f"{det.label} {det.confidence:.2f}"
                base_sz = 12
                font_size = self._get_responsive_size(base_sz, h_screen, cfg.get("label_scale", 100))
                font = self._get_font(font_size)
                
                lb = draw.textbbox((det.bbox[0], det.bbox[1]), label, font=font)
                draw.rectangle([(det.bbox[0], lb[1]), (lb[2]+4, lb[3])], fill=c_rgb + (255,))
                
                txt_col = cfg.get("label_text_color", "#000000")
                draw.text((det.bbox[0]+2, lb[1]), label, fill=txt_col, font=font)
                
        except Exception as e:
            # ESTE LOG SALDRA EN TU TERMINAL SI ALGO FALLA AQUI
            logging.error(f"[HUD BBOX ERROR] {e}")

    # --- RESTO DE MODULOS (Sin cambios logicos, solo mantenidos) ---
    def draw_stats_panel(self, draw, w_screen, h_screen, stats):
        try:
            cfg = self.config.get("modules.stats", {})
            if not cfg.get("enabled", True): return
            font_size = self._get_responsive_size(14, h_screen, cfg.get("scale", 100))
            font = self._get_font(font_size); f_size = getattr(font, 'size', 12) 
            header = cfg.get("header_text", "T7MD VISION PRO")
            lines = [header, f"FPS: {stats.get('fps', 0):.1f}", f"F: {stats.get('faces', 0)} | P: {stats.get('persons', 0)} | O: {stats.get('objects', 0)}"]
            line_height = f_size + 6; max_w = 0
            for l in lines: bb = draw.textbbox((0,0), l, font=font); max_w = max(max_w, bb[2]-bb[0])
            panel_h = len(lines) * line_height; panel_w = max_w + 20
            x, y = self._get_anchor_pos(w_screen, h_screen, panel_w, panel_h, cfg.get("position", "top_left"))
            bg_rgb = self._hex_to_rgb(cfg.get("bg_color", "#000000")); bg_alpha = int(cfg.get("bg_opacity", 80) * 2.55)
            if bg_alpha > 0: draw.rectangle([(x, y), (x+panel_w, y+panel_h)], fill=bg_rgb + (bg_alpha,))
            text_y = y + 5; text_x = x + 10; text_col = cfg.get("text_color", "#FFFFFF")
            for i, line in enumerate(lines): draw.text((text_x, text_y), line, font=font, fill=text_col); text_y += line_height
        except Exception: pass

    def draw_minimap(self, draw, w_screen, h_screen, detections):
        try:
            cfg = self.config.get("modules.minimap", {})
            if not cfg.get("enabled", True): return
            base_scale = 0.15; user_scale = cfg.get("scale", 100) / 100.0
            map_w = int(w_screen * base_scale * user_scale); 
            if w_screen == 0: return
            map_h = int(map_w * (h_screen / w_screen))
            x, y = self._get_anchor_pos(w_screen, h_screen, map_w, map_h, cfg.get("position", "top_right"))
            bg_rgb = self._hex_to_rgb(cfg.get("bg_color", "#000000")); bg_alpha = int(cfg.get("bg_opacity", 80) * 2.55)
            border_col = cfg.get("border_color", "#FFFFFF"); border_th = int(cfg.get("border_thick", 1))
            draw.rectangle([(x, y), (x + map_w, y + map_h)], fill=bg_rgb + (bg_alpha,), outline=border_col, width=border_th)
            grid_color = (255, 255, 255, 100); sw, sh = map_w / 3.0, map_h / 3.0
            for i in range(1, 3):
                vx = int(x + i*sw); draw.line([(vx, y), (vx, y + map_h)], fill=grid_color, width=1)
                hy = int(y + i*sh); draw.line([(x, hy), (x + map_w, hy)], fill=grid_color, width=1)
            base_dot = cfg.get("dot_size", 3); pt_sz = self._get_responsive_size(base_dot, h_screen)
            for det in detections:
                mx = x + int((det.center[0] / w_screen) * map_w); my = y + int((det.center[1] / h_screen) * map_h)
                color = "#FFFFFF"; t = str(det.type).lower()
                if "face" in t: color = self.config.get("modules.bboxes.face_color", "#00FFFF")
                elif "person" in t: color = self.config.get("modules.bboxes.person_color", "#00FF00")
                elif "object" in t: color = self.config.get("modules.bboxes.object_color", "#FFFF00")
                draw.rectangle([(mx-pt_sz, my-pt_sz), (mx+pt_sz, my+pt_sz)], fill=color)
        except Exception: pass

    def draw_timecode(self, draw, w_screen, h_screen, frame_number, fps):
        try:
            cfg = self.config.get("modules.timecode", {})
            if not cfg.get("enabled", True): return
            if fps <= 0: fps = 30
            sec = frame_number / fps; fr = int((sec * fps) % fps)
            m, s = divmod(sec, 60); h, m = divmod(m, 60)
            text = f"{int(h):02d}:{int(m):02d}:{int(s):02d}:{fr:02d}"
            font_size = self._get_responsive_size(24, h_screen, cfg.get("scale", 100))
            font = self._get_font(font_size); bb = draw.textbbox((0,0), text, font=font)
            w_txt, h_txt = bb[2]-bb[0], bb[3]-bb[1]; pad = int(getattr(font, 'size', 12) * 0.5)
            x, y = self._get_anchor_pos(w_screen, h_screen, w_txt + pad*2, h_txt + pad, cfg.get("position", "bottom_left"))
            bg_rgb = self._hex_to_rgb(cfg.get("bg_color", "#000000")); bg_alpha = int(cfg.get("bg_opacity", 80) * 2.55)
            draw.rectangle([(x, y), (x + w_txt + pad*2, y + h_txt + pad)], fill=bg_rgb + (bg_alpha,))
            draw.text((x + pad, y + pad//4), text, font=font, fill=cfg.get("text_color", "#FFFFFF"))
        except Exception: pass

    def draw_custom_message(self, draw, w_screen, h_screen):
        try:
            cfg = self.config.get("modules.custom_msg", {})
            if not cfg.get("enabled", False): return
            raw_text = cfg.get("text", ""); 
            if not raw_text: return
            lines = raw_text.split('\n')
            font_size = self._get_responsive_size(24, h_screen, cfg.get("scale", 100))
            font = self._get_font(font_size); f_size = getattr(font, 'size', 12); line_height = f_size + 4
            max_w = 0; total_h = len(lines) * line_height
            for l in lines: bb = draw.textbbox((0,0), l, font=font); max_w = max(max_w, bb[2]-bb[0])
            pad = int(f_size * 0.5); w_box = max_w + pad*2; h_box = total_h + pad
            x, y = self._get_anchor_pos(w_screen, h_screen, w_box, h_box, cfg.get("position", "bottom_center"))
            bg_rgb = self._hex_to_rgb(cfg.get("bg_color", "#000000")); bg_alpha = int(cfg.get("bg_opacity", 0) * 2.55)
            if bg_alpha > 0: draw.rectangle([(x, y), (x + w_box, y + h_box)], fill=bg_rgb + (bg_alpha,))
            curr_y = y + pad//2
            for line in lines:
                if bg_alpha == 0: draw.text((x + pad + 2, curr_y + 2), line, font=font, fill="black")
                draw.text((x + pad, curr_y), line, font=font, fill=cfg.get("text_color", "#FFFFFF"))
                curr_y += line_height
        except Exception: pass

    def draw_collage(self, combined_image, draw_final, w_screen, h_screen, detections, base_image):
        try:
            cfg = self.config.get("modules.collage", {})
            if not cfg.get("enabled", True): return
            faces = [d for d in detections if "face" in str(d.type).lower()]
            if not faces: return
            thumb_size = int(h_screen * (cfg.get("thumb_size_pct", 15) / 100.0))
            gap = int(thumb_size * (cfg.get("gap_pct", 5) / 100.0))
            count = min(len(faces), 5); col_h = count * (thumb_size + gap) - gap
            x, y = self._get_anchor_pos(w_screen, h_screen, thumb_size, col_h, cfg.get("position", "bottom_right"))
            border_col = cfg.get("border_color", "#FFFFFF"); border_th = int(cfg.get("border_thick", 1))
            opac = int(cfg.get("opacity", 100) * 2.55)
            for i, face in enumerate(faces[:count]):
                try:
                    bx1, by1, bx2, by2 = map(int, face.bbox)
                    bx1 = max(0, bx1); by1 = max(0, by1); bx2 = min(w_screen, bx2); by2 = min(h_screen, by2)
                    if bx2 > bx1 and by2 > by1:
                        crop = base_image.crop((bx1, by1, bx2, by2)).resize((thumb_size, thumb_size))
                        if opac < 255: crop.putalpha(opac)
                        curr_y = y + i * (thumb_size + gap)
                        combined_image.paste(crop, (x, curr_y), crop if opac < 255 else None)
                        if border_th > 0: draw_final.rectangle([(x, curr_y), (x+thumb_size, curr_y+thumb_size)], outline=border_col, width=border_th)
                except: pass
        except: pass

    def render_hud(self, frame: np.ndarray, frame_result, video_info: dict) -> np.ndarray:
        if frame is None: return frame
        h, w = frame.shape[:2]
        if w == 0: return frame
        try:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_result.frame_rgb = frame_rgb
            base_image = Image.fromarray(frame_rgb).convert("RGBA")
            overlay = Image.new("RGBA", base_image.size, (0,0,0,0))
            draw = ImageDraw.Draw(overlay)
            
            stats = {
                "frame": frame_result.frame_number,
                "fps": video_info.get("fps", 0),
                "faces": len([d for d in frame_result.detections if "face" in str(d.type).lower()]),
                "persons": len([d for d in frame_result.detections if "person" in str(d.type).lower()]),
                "objects": len([d for d in frame_result.detections if "object" in str(d.type).lower()])
            }

            self._draw_bboxes(draw, h, frame_result.detections)
            self.draw_stats_panel(draw, w, h, stats)
            self.draw_timecode(draw, w, h, frame_result.frame_number, video_info.get("fps", 30))
            self.draw_minimap(draw, w, h, frame_result.detections)
            self.draw_custom_message(draw, w, h)

            combined = Image.alpha_composite(base_image, overlay)
            draw_final = ImageDraw.Draw(combined)
            self.draw_collage(combined, draw_final, w, h, frame_result.detections, base_image)
            
            return cv2.cvtColor(np.array(combined.convert("RGB")), cv2.COLOR_RGB2BGR)
        except Exception as e:
            logging.error(f"[RENDER CRITICAL] {e}")
            return frame

    def render_layer(self, w, h, frame_result, video_info, layer_type="all"):
        base_image = None
        if layer_type in ["hud", "all"] and hasattr(frame_result, 'frame_rgb'):
             base_image = Image.fromarray(frame_result.frame_rgb).convert("RGBA")
        overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        stats = {
            "frame": frame_result.frame_number,
            "fps": video_info.get("fps", 0),
            "faces": len([d for d in frame_result.detections if "face" in str(d.type).lower()]),
            "persons": len([d for d in frame_result.detections if "person" in str(d.type).lower()]),
            "objects": len([d for d in frame_result.detections if "object" in str(d.type).lower()])
        }
        if layer_type == "bbox":
            self._draw_bboxes(draw, h, frame_result.detections)
        elif layer_type == "hud":
            self.draw_stats_panel(draw, w, h, stats)
            self.draw_timecode(draw, w, h, frame_result.frame_number, video_info.get("fps", 30))
            self.draw_minimap(draw, w, h, frame_result.detections)
            self.draw_custom_message(draw, w, h)
            if base_image:
                self.draw_collage(overlay, draw, w, h, frame_result.detections, base_image)
        return cv2.cvtColor(np.array(overlay), cv2.COLOR_RGBA2BGRA)

    def render_collage_layer(self, rgb, w, h, res): return np.zeros((h,w,4), dtype=np.uint8)