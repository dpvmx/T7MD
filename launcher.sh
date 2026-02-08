#!/bin/bash

# 1. Obtener la ruta ABSOLUTA donde está este archivo
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# 2. Entrar a la carpeta para encontrar 'models' y 'core'
cd "$DIR"

# 3. Activar el entorno virtual
source "$DIR/.venv/bin/activate"

# 4. Ejecutar Python en modo "Unbuffered" (-u)
# Esto es vital para que AE reciba los datos en tiempo real y no se atasque al final.
python -u headless.py "$@"