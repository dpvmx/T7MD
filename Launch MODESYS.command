#!/bin/bash

# ============================================
# Launch MODESYS - Lanzador Directo
# ============================================

# 1. Obtener la ruta ABSOLUTA del script
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

# 2. Verificar que el entorno virtual existe
if [ ! -d ".venv" ]; then
    echo "=================================================="
    echo "❌ Error: Entorno virtual no encontrado."
    echo "   Por favor, ejecuta 'install_modesys.sh' primero"
    echo "   para configurar las dependencias."
    echo "=================================================="
    echo ""
    read -p "Presiona Enter para salir..."
    exit 1
fi

# 3. Activar el entorno virtual
source .venv/bin/activate

# 4. Ejecutar la aplicación
python main.py

# 5. Mantener la terminal abierta SOLO si ocurre un error
if [ $? -ne 0 ]; then
    echo ""
    echo "=================================================="
    echo "❌ La aplicación se detuvo inesperadamente."
    echo "=================================================="
    read -p "Presiona Enter para cerrar..."
fi