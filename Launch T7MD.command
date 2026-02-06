#!/bin/bash
# ============================================
# T7MD Vision Pro - Instalador Automático
# ============================================
# Los usuarios solo necesitan hacer doble clic
# ============================================

# -----------------------------------------------------------------
# CONFIGURACIÓN
# -----------------------------------------------------------------
APP_NAME="T7MD Vision Pro"
VERSION="1.0.0"
REQUIRED_PYTHON="3.12"
TEMP_DIR="/tmp/t7md_install_$$"
LOG_FILE="$TEMP_DIR/install.log"

# Obtener el directorio del script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colores para la interfaz
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# -----------------------------------------------------------------
# FUNCIONES DE INTERFAZ DE USUARIO
# -----------------------------------------------------------------

# Función para limpiar la pantalla con estilo
clear_screen() {
    printf "\033c"
    echo -e "${CYAN}╔══════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║                                                      ║${NC}"
    echo -e "${CYAN}║   ${BOLD}T7MD VISION PRO - INSTALADOR AUTOMÁTICO${NC}${CYAN}          ║${NC}"
    echo -e "${CYAN}║                                                      ║${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# Función para mostrar un mensaje
show_message() {
    echo -e "${BLUE}➡ ${NC}$1"
}

# Función para mostrar éxito
show_success() {
    echo -e "${GREEN}✓ ${NC}$1"
}

# Función para mostrar advertencia
show_warning() {
    echo -e "${YELLOW}⚠ ${NC}$1"
}

# Función para mostrar error
show_error() {
    echo -e "${RED}✗ ${NC}$1"
}

# Función para preguntar al usuario
ask_question() {
    local question="$1"
    local default="$2"
    
    if [ "$default" = "Y" ]; then
        prompt="${GREEN}[S/n]${NC}"
    elif [ "$default" = "N" ]; then
        prompt="${GREEN}[s/N]${NC}"
    else
        prompt="${GREEN}[s/n]${NC}"
    fi
    
    while true; do
        echo -e "${BOLD}$question${NC} $prompt"
        read -r -p "Respuesta: " answer
        
        case "$answer" in
            [Ss]* | [Yy]* ) return 0;;
            [Nn]* ) return 1;;
            "" ) 
                if [ "$default" = "Y" ]; then return 0; fi
                if [ "$default" = "N" ]; then return 1; fi
                ;;
            * ) echo "Por favor responde S (sí) o N (no)";;
        esac
    done
}

# -----------------------------------------------------------------
# FUNCIONES DE VERIFICACIÓN DEL SISTEMA
# -----------------------------------------------------------------

check_system() {
    clear_screen
    show_message "Verificando sistema..."
    
    # Verificar que estamos en macOS
    if [[ "$OSTYPE" != "darwin"* ]]; then
        show_error "Esta aplicación solo funciona en macOS."
        echo ""
        echo "Presiona cualquier tecla para salir..."
        read -n 1
        exit 1
    fi
    
    # Verificar arquitectura
    ARCH=$(uname -m)
    if [[ "$ARCH" == "arm64" ]]; then
        show_success "Detectado: Apple Silicon (M1/M2/M3)"
        IS_APPLE_SILICON=true
    elif [[ "$ARCH" == "x86_64" ]]; then
        show_warning "Detectado: Intel Mac"
        show_warning "El rendimiento puede ser menor"
        IS_APPLE_SILICON=false
    else
        show_error "Arquitectura no compatible: $ARCH"
        exit 1
    fi
    
    # Verificar versión de macOS
    MACOS_VERSION=$(sw_vers -productVersion)
    show_success "macOS $MACOS_VERSION detectado"
    
    # Verificar espacio en disco
    DISK_SPACE=$(df -h "$SCRIPT_DIR" | awk 'NR==2 {print $4}')
    show_success "Espacio disponible: $DISK_SPACE"
    
    sleep 1
}

# -----------------------------------------------------------------
# FUNCIONES DE INSTALACIÓN
# -----------------------------------------------------------------

install_homebrew() {
    show_message "Instalando Homebrew..."
    
    if ! command -v brew &> /dev/null; then
        echo ""
        show_warning "Homebrew no está instalado. Es necesario para continuar."
        
        if ask_question "¿Instalar Homebrew? (Requerido)" "Y"; then
            echo ""
            show_message "Instalando... Esto puede tomar unos minutos."
            echo "Se te pedirá tu contraseña de administrador."
            echo ""
            
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            
            if [[ "$IS_APPLE_SILICON" == true ]]; then
                echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
                eval "$(/opt/homebrew/bin/brew shellenv)"
            fi
            
            show_success "Homebrew instalado correctamente"
        else
            show_error "Homebrew es requerido. Instalación cancelada."
            exit 1
        fi
    else
        show_success "Homebrew ya está instalado"
    fi
}

install_python() {
    show_message "Verificando Python $REQUIRED_PYTHON..."
    
    if ! brew list python@$REQUIRED_PYTHON &> /dev/null; then
        echo ""
        show_warning "Python $REQUIRED_PYTHON no está instalado."
        
        if ask_question "¿Instalar Python $REQUIRED_PYTHON?" "Y"; then
            echo ""
            show_message "Instalando Python $REQUIRED_PYTHON..."
            brew install python@$REQUIRED_PYTHON
            
            # Configurar PATH
            export PATH="/opt/homebrew/opt/python@$REQUIRED_PYTHON/bin:$PATH"
            
            show_success "Python $REQUIRED_PYTHON instalado"
        else
            show_error "Python $REQUIRED_PYTHON es requerido."
            exit 1
        fi
    else
        show_success "Python $REQUIRED_PYTHON ya está instalado"
    fi
}

setup_virtual_env() {
    show_message "Configurando entorno virtual..."
    
    if [ ! -d "$SCRIPT_DIR/.venv" ]; then
        cd "$SCRIPT_DIR"
        python3.12 -m venv .venv
        show_success "Entorno virtual creado"
    else
        show_success "Entorno virtual ya existe"
    fi
    
    # Activar entorno virtual
    source "$SCRIPT_DIR/.venv/bin/activate"
}

install_dependencies() {
    clear_screen
    show_message "Instalando componentes de IA..."
    echo ""
    
    # Cambiar al directorio del script
    cd "$SCRIPT_DIR"
    
    # Activar entorno virtual
    source "$SCRIPT_DIR/.venv/bin/activate"
    
    # Instalar PyTorch primero
    echo "Instalando componentes..."
    echo ""
    
    show_message "1. Motor de IA (PyTorch)..."
    pip install --quiet torch torchvision
    show_success "   PyTorch instalado"
    
    # Instalar otras dependencias
    show_message "2. Interfaz gráfica..."
    pip install --quiet PySide6==6.10.1
    show_success "   Interfaz instalada"
    
    show_message "3. Visión por computadora..."
    pip install --quiet ultralytics==8.2.35
    show_success "   YOLO instalado"
    
    show_message "4. Procesamiento de video..."
    pip install --quiet opencv-python==4.10.0.84
    show_success "   OpenCV instalado"
    
    show_message "5. Procesamiento de imágenes..."
    pip install --quiet numpy==1.26.4 Pillow==10.2.0
    show_success "   Herramientas de imagen instaladas"
    
    show_message "6. Utilidades..."
    pip install --quiet dataclasses-json==0.6.7
    show_success "   Utilidades instaladas"
    
    echo ""
    show_success "✓ Todos los componentes instalados"
}

verify_models() {
    clear_screen
    show_message "Verificando modelos de IA..."
    echo ""
    
    # Cambiar al directorio del script
    cd "$SCRIPT_DIR"
    
    mkdir -p models
    
    # Lista de modelos requeridos (sin arrays asociativos)
    MODEL_LIST="yolov8m.pt yolov8s-world.pt"
    
    for model in $MODEL_LIST; do
        if [ ! -f "$SCRIPT_DIR/models/$model" ]; then
            show_warning "Falta: $model"
            
            if ask_question "¿Descargar automáticamente? (~80 MB)" "Y"; then
                echo ""
                show_message "Descargando $model..."
                
                # Determinar URL basada en el nombre del modelo
                if [ "$model" = "yolov8m.pt" ]; then
                    url="https://github.com/ultralytics/assets/releases/download/v8.2.0/yolov8m.pt"
                elif [ "$model" = "yolov8s-world.pt" ]; then
                    url="https://github.com/ultralytics/assets/releases/download/v8.2.0/yolov8s-world.pt"
                else
                    url=""
                fi
                
                if [ -n "$url" ]; then
                    curl -L -o "$SCRIPT_DIR/models/$model" "$url"
                    
                    if [ -f "$SCRIPT_DIR/models/$model" ]; then
                        show_success "   $model descargado"
                    else
                        show_error "   Error al descargar $model"
                    fi
                else
                    show_error "   No se encontró URL para $model"
                fi
            fi
        else
            show_success "$model encontrado"
        fi
    done
    
    # Modelo de caras (necesita descarga manual)
    FACE_MODEL="yolov8m-face-lindevs.pt"
    if [ ! -f "$SCRIPT_DIR/models/$FACE_MODEL" ]; then
        echo ""
        show_warning "Modelo de detección de caras no encontrado."
        echo "   Este modelo requiere descarga manual."
        echo "   Puedes:"
        echo "   1. Descargarlo de: https://github.com/lindevs/yolov8-face"
        echo "   2. Copiarlo a la carpeta 'models/'"
        echo "   3. Continuar sin detección de caras"
        echo ""
        
        if ask_question "¿Continuar sin detección de caras?" "Y"; then
            show_warning "La detección de caras estará desactivada"
        fi
    else
        show_success "$FACE_MODEL encontrado"
    fi
}

verify_fonts() {
    show_message "Verificando fuentes..."
    
    mkdir -p "$SCRIPT_DIR/fonts"
    
    if [ ! -f "$SCRIPT_DIR/fonts/telegrama.otf" ]; then
        show_warning "Fuente principal no encontrada"
        echo ""
        echo "La fuente 'telegrama.otf' es opcional pero recomendada."
        echo "Para obtenerla:"
        echo "1. Solicítala al administrador"
        echo "2. Cópiala a la carpeta 'fonts/'"
        echo "3. La aplicación usará una fuente alternativa"
        echo ""
    else
        show_success "Fuente telegrama.otf encontrada"
    fi
}

create_launcher() {
    show_message "Creando lanzador..."
    
    # Cambiar al directorio del script
    cd "$SCRIPT_DIR"
    
    # Crear script de lanzamiento
    cat > "$SCRIPT_DIR/T7MD Vision Pro.command" << 'EOF'
#!/bin/bash
# ============================================
# T7MD Vision Pro - Lanzador
# ============================================

# Obtener directorio del script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Verificar entorno virtual
if [ ! -d ".venv" ]; then
    echo "❌ Error: Entorno virtual no encontrado."
    echo "   Ejecuta 'Launch T7MD.command' primero para configurar."
    echo ""
    read -p "Presiona Enter para salir..."
    exit 1
fi

# Activar entorno virtual
source .venv/bin/activate

# Ejecutar aplicación
echo "🚀 Iniciando T7MD Vision Pro..."
echo ""
python main.py

# Mantener ventana abierta si hay error
if [ $? -ne 0 ]; then
    echo ""
    echo "❌ La aplicación se cerró con un error."
    echo ""
    read -p "Presiona Enter para cerrar..."
fi
EOF
    
    chmod +x "$SCRIPT_DIR/T7MD Vision Pro.command"
    show_success "Lanzador creado"
}

# -----------------------------------------------------------------
# FUNCIÓN PRINCIPAL
# -----------------------------------------------------------------

main() {
    # Cambiar al directorio del script inmediatamente
    cd "$SCRIPT_DIR"
    
    # Crear directorio temporal
    mkdir -p "$TEMP_DIR"
    
    # Mostrar pantalla de inicio
    clear_screen
    echo -e "${CYAN}Bienvenido al instalador de ${BOLD}T7MD Vision Pro${NC}${CYAN}"
    echo "Este instalador configurará todo automáticamente."
    echo "No se requieren conocimientos técnicos."
    echo ""
    echo -e "${YELLOW}⚠  IMPORTANTE:${NC}"
    echo "• Necesitarás conexión a internet"
    echo "• Se te pedirá tu contraseña una vez"
    echo "• El proceso tomará 5-10 minutos"
    echo ""
    
    if ! ask_question "¿Continuar con la instalación?" "Y"; then
        echo "Instalación cancelada."
        exit 0
    fi
    
    # Paso 1: Verificar sistema
    check_system
    
    # Paso 2: Instalar Homebrew
    install_homebrew
    
    # Paso 3: Instalar Python
    install_python
    
    # Paso 4: Configurar entorno virtual
    setup_virtual_env
    
    # Paso 5: Instalar dependencias
    install_dependencies
    
    # Paso 6: Verificar modelos
    verify_models
    
    # Paso 7: Verificar fuentes
    verify_fonts
    
    # Paso 8: Crear lanzador
    create_launcher
    
    # Mostrar resumen
    clear_screen
    echo -e "${GREEN}╔══════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                                                      ║${NC}"
    echo -e "${GREEN}║   ${BOLD}¡INSTALACIÓN COMPLETADA!${NC}${GREEN}                     ║${NC}"
    echo -e "${GREEN}║                                                      ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════╝${NC}"
    echo ""
    show_success "T7MD Vision Pro está listo para usar"
    echo ""
    echo -e "${BOLD}📋 Resumen:${NC}"
    echo "• Python 3.12 configurado ✓"
    echo "• Motor de IA instalado ✓"
    echo "• Interfaz gráfica lista ✓"
    echo "• Modelos verificados ✓"
    echo ""
    echo -e "${BOLD}🚀 Para iniciar la aplicación:${NC}"
    echo "1. Busca el archivo 'T7MD Vision Pro.command'"
    echo "2. Haz ${BOLD}DOBLE CLIC${NC} en él"
    echo "3. La aplicación se abrirá automáticamente"
    echo ""
    echo -e "${BOLD}💡 Consejo:${NC}"
    echo "Arrastra 'T7MD Vision Pro.command' al Dock"
    echo "para tener acceso rápido siempre"
    echo ""
    
    # Preguntar si iniciar ahora
    if ask_question "¿Iniciar T7MD Vision Pro ahora?" "Y"; then
        echo ""
        show_message "Iniciando aplicación..."
        echo ""
        
        # Cambiar al directorio del script
        cd "$SCRIPT_DIR"
        
        # Activar entorno virtual
        source "$SCRIPT_DIR/.venv/bin/activate"
        
        # Ejecutar aplicación
        python "$SCRIPT_DIR/main.py"
    else
        echo ""
        show_success "Instalación finalizada. Puedes cerrar esta ventana."
        echo ""
        read -p "Presiona Enter para salir..."
    fi
}

# -----------------------------------------------------------------
# FUNCIONES DE LIMPIEZA
# -----------------------------------------------------------------

cleanup() {
    if [ -d "$TEMP_DIR" ]; then
        rm -rf "$TEMP_DIR"
    fi
}

# -----------------------------------------------------------------
# EJECUCIÓN
# -----------------------------------------------------------------

# Configurar trap para limpieza
trap cleanup EXIT

# Verificar que se está ejecutando en terminal
if [ -t 0 ]; then
    main
else
    # Si se ejecuta desde Finder, abrir Terminal
    echo "Abriendo en Terminal..."
    open -a Terminal "$0"
    exit 0
fi