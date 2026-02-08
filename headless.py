"""
T7MD Headless Runner - v1.6 (Diagnostic Mode)
"""
import sys
import argparse
import os
import signal
import time
from PySide6.QtCore import QCoreApplication

# Forzar ruta absoluta
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(CURRENT_DIR)
sys.path.append(CURRENT_DIR)

from core.video_engine import VideoEngine
from core.config_manager import ConfigManager

signal.signal(signal.SIGINT, signal.SIG_DFL)

def run_headless():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output_dir", required=True)
    parser.add_argument("--faces", action="store_true")
    parser.add_argument("--persons", action="store_true")
    parser.add_argument("--objects", action="store_true")
    
    args = parser.parse_args()
    
    app = QCoreApplication(sys.argv)
    
    config = ConfigManager()
    config.set("models.use_faces", args.faces)
    config.set("models.use_persons", args.persons)
    config.set("models.use_objects", args.objects)
    config.set("output.output_dir", args.output_dir)
    config.set("output.skip_video", True) # Seguimos saltando el video para velocidad

    base_name = os.path.splitext(os.path.basename(args.input))[0]
    config.set("output.custom_filename", f"{base_name}_t7md_data")

    engine = VideoEngine(config)

    last_pct = -1

    def on_progress(pct, frame, fps):
        nonlocal last_pct
        if pct > last_pct:
            sys.stdout.write(f"PROGRESS|{pct}\n")
            sys.stdout.flush()
            last_pct = pct

    def on_finished(result):
        # AQUÍ ESTÁ EL CAMBIO CLAVE:
        if result and 'json_file' in result:
            sys.stdout.write(f"SUCCESS|{result['json_file']}\n")
        else:
            # Extraer el mensaje real del error
            error_msg = "Error desconocido"
            if result and 'error' in result:
                error_msg = result['error']
            elif result is None:
                error_msg = "El motor devolvió un resultado vacío (None)"
            
            # Enviarlo a After Effects
            sys.stdout.write(f"ERROR|{error_msg}\n")
            
        sys.stdout.flush()
        time.sleep(1.0)
        os._exit(0)

    engine.progress_updated.connect(on_progress)
    engine.processing_finished.connect(on_finished)

    engine.setup_render(args.input)
    engine.start()

    sys.exit(app.exec())

if __name__ == "__main__":
    run_headless()