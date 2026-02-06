#!/bin/bash

# ============================================
# T7MD Vision Pro - Launcher V2.1 (ASCII Splash)
# ============================================

# 1. Moverse al directorio del script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# 2. Limpiar pantalla e imprimir Arte ASCII (Color Verde Hacker)
clear
echo -e "\033[92m" # Inicia color verde
cat << "EOF"
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
|                  MOTION DETECTTION SYSTEM BY TRIPLESIETE                      |
|                  Version: 0.1                                                 |
|                  code by: @dpvmx                                              |
|_______________________________________________________________________________|
EOF
echo -e "\033[0m" # Reset color

# 3. Verificar y Activar entorno virtual
if [ -d ".venv" ]; then
    source .venv/bin/activate
else
    echo "⚠️  Advertencia: carpeta .venv no encontrada."
    echo "   Intentando ejecutar con Python del sistema..."
fi

# 4. Ejecutar aplicación
python main.py

# 5. Mantener ventana abierta solo si hubo error
if [ $? -ne 0 ]; then
    echo ""
    echo "=================================================="
    echo "❌ La aplicación se cerró con un error."
    echo "=================================================="
    read -p "Presiona Enter para cerrar..."
fi