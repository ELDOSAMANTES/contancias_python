from PySide6.QtWidgets import QPushButton, QFrame, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor

class AnimButton(QPushButton):
    """Botón del menú con animación de hover"""
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setCheckable(True)
        self.setFixedHeight(50)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("""
            QPushButton { 
                background: none; 
                color: #94a3b8; 
                text-align: left; 
                padding-left: 20px; 
                border: none; 
                font-family: 'Segoe UI', sans-serif;
                font-size: 14px; 
                border-left: 3px solid transparent; 
            }
            QPushButton:hover { background-color: #1e293b; color: white; }
            QPushButton:checked { background-color: #3b82f6; color: white; font-weight: bold; border-left: 3px solid white; }
        """)

class StatCard(QFrame):
    """Tarjeta de estadística estilo Dashboard Moderno"""
    def __init__(self, title, value, subtitle, icon, color_bg, color_text):
        super().__init__()
        self.setMinimumWidth(220)
        self.setFixedHeight(120)
        self.setStyleSheet(f"""
            QFrame#Card {{ 
                background-color: white; 
                border-radius: 16px; 
                border: 1px solid #f1f5f9; 
            }}
        """)
        self.setObjectName("Card")
        
        # Layout Principal Horizontal
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # --- COLUMNA IZQUIERDA (Textos) ---
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("color: #64748b; font-size: 13px; font-weight: 600; font-family: 'Segoe UI'; border: none;")
        
        lbl_value = QLabel(str(value))
        lbl_value.setStyleSheet("color: #0f172a; font-size: 28px; font-weight: 800; font-family: 'Segoe UI'; border: none;")
        
        lbl_sub = QLabel(subtitle)
        lbl_sub.setStyleSheet("color: #94a3b8; font-size: 11px; font-family: 'Segoe UI'; border: none;")
        
        text_layout.addWidget(lbl_title)
        text_layout.addWidget(lbl_value)
        text_layout.addWidget(lbl_sub)
        
        # --- COLUMNA DERECHA (Icono) ---
        icon_layout = QVBoxLayout()
        icon_layout.setAlignment(Qt.AlignTop | Qt.AlignRight)
        
        lbl_icon = QLabel(icon)
        lbl_icon.setFixedSize(45, 45)
        lbl_icon.setAlignment(Qt.AlignCenter)
        # Estilo del cuadro del icono (Fondo suave y texto de color)
        lbl_icon.setStyleSheet(f"""
            background-color: {color_bg}; 
            color: {color_text}; 
            border-radius: 10px; 
            font-size: 20px;
            border: none;
        """)
        
        icon_layout.addWidget(lbl_icon)
        
        # Agregar al layout principal
        main_layout.addLayout(text_layout)
        main_layout.addStretch() # Empuja el icono a la derecha
        main_layout.addLayout(icon_layout)