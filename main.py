import sys
import logging
import os
import signal

# --- SILENCIAR ADVERTENCIAS DE HUGGING FACE ---
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
# ----------------------------------------------

from PySide6.QtWidgets import QApplication
from gui.main_window import MainWindow

# --- ARTE ASCII (Backup por si se ejecuta directo con python) ---
ASCII_HEADER = r"""
 ▄▄▄▄▄▄▄▄▄▄▄  ▄▄▄▄▄▄▄▄▄▄▄  ▄▄▄▄▄▄▄▄▄▄▄  ▄▄▄▄▄▄▄▄▄▄▄  ▄▄       ▄▄  ▄▄▄▄▄▄▄▄▄▄  
▐░░░░░░░░░░░▌▐░░░░░░░░░░░▌▐░░░░░░░░░░░▌▐░░░░░░░░░░░▌▐░░▌     ▐░░▌▐░░░░░░░░░░▌ 
 ▀▀▀▀█░█▀▀▀▀  ▀▀▀▀▀▀▀▀▀█░▌ ▀▀▀▀▀▀▀▀▀█░▌ ▀▀▀▀▀▀▀▀▀█░▌▐░▌░▌   ▐░▐░▌▐░█▀▀▀▀▀▀▀█░▌
     ▐░▌              ▐░▌          ▐░▌          ▐░▌ ▐░▌▐░▌ ▐░▌▐░▌▐░▌       ▐░▌
     ▐░▌             ▐░▌          ▐░▌          ▐░▌  ▐░▌ ▐░▐░▌ ▐░▌▐░▌       ▐░▌
     ▐░▌            ▐░▌          ▐░▌          ▐░▌   ▐░▌  ▐░▌  ▐░▌▐░▌       ▐░▌
     ▐░▌           ▐░▌          ▐░▌          ▐░▌    ▐░▌   ▀   ▐░▌▐░▌       ▐░▌
     ▐░▌          ▐░▌          ▐░▌          ▐░▌     ▐░▌       ▐░▌▐░▌       ▐░▌
     ▐░▌         ▐░▌          ▐░▌          ▐░▌      ▐░▌       ▐░▌▐░█▄▄▄▄▄▄▄█░▌
     ▐░▌        ▐░▌          ▐░▌          ▐░▌       ▐░▌       ▐░▌▐░░░░░░░░░░▌ 
      ▀          ▀            ▀            ▀         ▀         ▀  ▀▀▀▀▀▀▀▀▀▀  
________________________________________________________________________________
|                                                                               |
|                  MOTION DETECTTION SYSTEM BY DPVMX                            |
|                  Version: 8.3.0                                               |
|                  code by: @dpvmx                                              |
|_______________________________________________________________________________|                                                                              
"""

def setup_logging():
    """Configura el sistema de logs para que se vea 'Verbose' en la terminal"""
    # Excluimos los logs de requests y urllib3 que hacen ruido
    logging.getLogger("urllib3").setLevel(logging.ERROR)
    logging.getLogger("httpx").setLevel(logging.ERROR)
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] > %(message)s",
        datefmt="%H:%M:%S"
    )

def main():
    # 1. Limpiar terminal (Cross-platform)
    os.system('cls' if os.name == 'nt' else 'clear')
    
    # 2. Imprimir Cabecera
    print("\033[92m") # Color Verde Terminal
    print(ASCII_HEADER)
    print("\033[0m") # Reset Color
    
    # 3. Iniciar Logs
    setup_logging()
    logging.info("Inicializando Sistema T7MD Vision Pro...")
    logging.info(f"Directorio de trabajo: {os.getcwd()}")
    
    # Manejo de señal para cerrar con Ctrl+C limpio
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    try:
        app = QApplication(sys.argv)
        logging.info("Qt Framework inicializado correctamente.")
        
        # Cargar Ventana
        logging.info("Cargando interfaz gráfica (MainWindow)...")
        window = MainWindow()
        window.show()
        
        logging.info("Sistema listo. Esperando interacción del usuario.")
        sys.exit(app.exec())
        
    except Exception as e:
        logging.critical(f"ERROR CRÍTICO DEL SISTEMA: {e}", exc_info=True)

if __name__ == "__main__":
    main()