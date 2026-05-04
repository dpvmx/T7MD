#!/bin/bash
# ============================================
# MODESYS - Instalador Automático
# ============================================

APP_NAME="MODESYS"
VERSION="8.4.0"
REQUIRED_PYTHON="3.12"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'
BOLD='\033[1m'

clear_screen() {
    printf "\033c"
    echo -e "${CYAN}╔══════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║                                                      ║${NC}"
    echo -e "${CYAN}║   ${BOLD}MODESYS - INSTALADOR DE SISTEMA${NC}${CYAN}                  ║${NC}"
    echo -e "${CYAN}║                                                      ║${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════╝${NC}"
    echo ""
}

show_message() { echo -e "${CYAN}➡ ${NC}$1"; }
show_success() { echo -e "${GREEN}✓ ${NC}$1"; }
show_warning() { echo -e "${YELLOW}⚠ ${NC}$1"; }
show_error() { echo -e "${RED}✗ ${NC}$1"; }

ask_question() {
    while true; do
        echo -e "${BOLD}$1${NC} ${GREEN}[S/n]${NC}"
        read -r -p "Respuesta: " answer
        case "${answer:-S}" in
            [Ss]*|[Yy]* ) return 0;;
            [Nn]* ) return 1;;
        esac
    done
}

main() {
    cd "$SCRIPT_DIR"
    clear_screen
    
    if ! ask_question "¿Iniciar instalación de MODESYS v$VERSION?" "Y"; then
        exit 0
    fi
    
    # 1. Entorno Virtual
    show_message "Configurando entorno virtual..."
    if [ ! -d ".venv" ]; then
        python3 -m venv .venv
        show_success "Entorno virtual creado"
    else
        show_success "Entorno virtual ya existe"
    fi
    source .venv/bin/activate
    
    # 2. Dependencias (Usando nuestro nuevo requirements.txt optimizado)
    show_message "Instalando motor de dependencias optimizado..."
    pip install --upgrade pip --quiet
    pip install -r requirements.txt --quiet
    show_success "Dependencias instaladas correctamente"
    
    # 3. Modelos
    show_message "Verificando redes neuronales (Modelos YOLO)..."
    mkdir -p models
    for model in yolov8m.pt yolov8s-world.pt; do
        if [ ! -f "models/$model" ]; then
            show_warning "Falta: $model"
            if ask_question "¿Descargar automáticamente?" "Y"; then
                curl -L -o "models/$model" "https://github.com/ultralytics/assets/releases/download/v8.2.0/$model"
            fi
        else
            show_success "$model verificado"
        fi
    done
    
    # 4. Crear Lanzador
    show_message "Generando ejecutable..."
    cat > "Launch MODESYS.command" << 'EOF'
#!/bin/bash
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"
if [ ! -d ".venv" ]; then
    echo "❌ Error: Entorno virtual no encontrado. Ejecuta install_modesys.sh primero."
    read -p "Presiona Enter para salir..."
    exit 1
fi
source .venv/bin/activate
python main.py
if [ $? -ne 0 ]; then
    read -p "Presiona Enter para cerrar..."
fi
EOF
    chmod +x "Launch MODESYS.command"
    show_success "Launch MODESYS.command creado"
    
    clear_screen
    show_success "MODESYS está listo para operar."
    echo -e "Haz doble clic en ${BOLD}Launch MODESYS.command${NC} para iniciar."
    echo ""
}

main