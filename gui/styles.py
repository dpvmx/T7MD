"""
Estilos Globales T7MD Vision Pro
Tema: Dark Mode + Accent Cyber Lime (#BCFF4E)
Fix: Fuentes compatibles con macOS para evitar warnings.
"""

ACCENT_COLOR = "#BCFF4E"
BG_DARK = "#151515"
BG_PANEL = "#1a1a1a"

# Pila de fuentes optimizada para Mac > Windows > Linux
FONT_STACK = "'-apple-system', 'Helvetica Neue', 'Segoe UI', 'Roboto', sans-serif"

MAIN_STYLESHEET = f"""
/* --- GENERICO --- */
QMainWindow {{
    background-color: #000000;
}}
QWidget {{
    color: #e0e0e0;
    font-family: {FONT_STACK};
    font-size: 12px;
}}

/* --- GRUPOS --- */
QGroupBox {{
    border: 1px solid #333;
    border-radius: 4px;
    margin-top: 20px;
    font-weight: bold;
    color: #888;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 5px;
    left: 10px;
}}

/* --- BOTONES --- */
QPushButton {{
    background-color: #333;
    border: 1px solid #444;
    border-radius: 4px;
    padding: 5px;
    color: #fff;
}}
QPushButton:hover {{
    background-color: #444;
    border-color: #555;
}}
QPushButton:pressed {{
    background-color: #222;
}}

/* --- CHECKBOX (Accent) --- */
QCheckBox {{
    spacing: 5px;
}}
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 1px solid #555;
    border-radius: 3px;
    background: #222;
}}
QCheckBox::indicator:checked {{
    background-color: {ACCENT_COLOR};
    border-color: {ACCENT_COLOR};
    image: url(none); /* Truco para cuadro solido */
}}

/* --- SLIDER (Accent) --- */
QSlider::groove:horizontal {{
    border: 1px solid #333;
    height: 4px;
    background: #222;
    margin: 2px 0;
    border-radius: 2px;
}}
QSlider::handle:horizontal {{
    background: {ACCENT_COLOR};
    border: 1px solid {ACCENT_COLOR};
    width: 12px;
    height: 12px;
    margin: -5px 0;
    border-radius: 6px;
}}
QSlider::sub-page:horizontal {{
    background: #444;
    border-radius: 2px;
}}

/* --- INPUTS --- */
QLineEdit, QPlainTextEdit {{
    background-color: #111;
    border: 1px solid #333;
    border-radius: 3px;
    padding: 3px;
    color: #fff;
    selection-background-color: {ACCENT_COLOR};
    selection-color: #000;
}}
QLineEdit:focus, QPlainTextEdit:focus {{
    border: 1px solid {ACCENT_COLOR};
}}

/* --- COMBOBOX --- */
QComboBox {{
    background-color: #111;
    border: 1px solid #333;
    border-radius: 3px;
    padding: 3px;
}}
QComboBox::drop-down {{
    border: none;
    width: 20px;
}}
QComboBox QAbstractItemView {{
    background-color: #222;
    border: 1px solid #444;
    selection-background-color: {ACCENT_COLOR};
    selection-color: #000;
}}

/* --- SCROLLBAR --- */
QScrollBar:vertical {{
    border: none;
    background: #111;
    width: 8px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: #444;
    min-height: 20px;
    border-radius: 4px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
"""