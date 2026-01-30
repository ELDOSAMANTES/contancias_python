import sys
import os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
    QFrame, QLabel, QButtonGroup, QStackedWidget, QGraphicsOpacityEffect
)
from PySide6.QtCore import QPropertyAnimation, Qt, QSize
from PySide6.QtGui import QPixmap, QIcon

# Importaciones de nuestros módulos
from database import StudentEngine
from components import AnimButton
from pages.dashboard import DashboardPage
from pages.registro import RegistroPage
from pages.alumnos import AlumnosPage
from pages.talleres import TalleresPage
from pages.constancias import ConstanciaPage
from pages.expediente import ExpedientePage

# --- ESTILOS GLOBALES (Soluciona filtros y ventanas blancas) ---
GLOBAL_STYLES = """
    /* Fondo General */
    QMainWindow { background-color: #f1f5f9; }
    
    /* Fuentes Generales */
    QWidget { font-family: 'Segoe UI', sans-serif; font-size: 14px; color: #1e293b; }

    /* --- ARREGLO PARA FILTROS (QComboBox) --- */
    QComboBox {
        background-color: #ffffff;
        border: 1px solid #cbd5e1;
        border-radius: 6px;
        padding: 5px 10px;
        color: #1e293b; /* Texto oscuro siempre */
        min-width: 100px;
    }
    QComboBox::drop-down {
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 20px;
        border-left: none;
    }
    /* La lista desplegable */
    QComboBox QAbstractItemView {
        background-color: #ffffff;
        color: #1e293b;
        selection-background-color: #eff6ff;
        selection-color: #1e40af;
        border: 1px solid #cbd5e1;
    }

    /* --- ARREGLO PARA VENTANAS EMERGENTES (QDialog y QMessageBox) --- */
    QDialog, QMessageBox {
        background-color: #ffffff; /* Fondo blanco */
    }
    QMessageBox QLabel {
        color: #1e293b; /* Texto oscuro */
    }
    
    /* --- ARREGLO PARA CAMPOS DE TEXTO (QLineEdit) --- */
    QLineEdit {
        background-color: #ffffff;
        border: 1px solid #cbd5e1;
        border-radius: 6px;
        padding: 6px;
        color: #1e293b;
    }
    QLineEdit:focus {
        border: 1px solid #3b82f6;
    }

    /* --- BOTONES --- */
    QPushButton {
        border-radius: 6px;
        padding: 6px 12px;
    }
"""

class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.engine = StudentEngine()
        self.setWindowTitle("Sistema de Gestión TESCH - v1.0")
        self.resize(1280, 800)
        
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        self.layout = QHBoxLayout(main_widget)
        self.layout.setContentsMargins(0,0,0,0)
        self.layout.setSpacing(0)

        self.setup_sidebar()
        self.setup_pages()
        self.switch_page(0)

    def setup_sidebar(self):
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(250)
        self.sidebar.setStyleSheet("background-color: #0f172a; border: none;")
        ly = QVBoxLayout(self.sidebar)
        ly.setSpacing(10)
        ly.setContentsMargins(0, 0, 0, 20) 
        
        # --- LOGO ---
        logo_lbl = QLabel()
        logo_lbl.setAlignment(Qt.AlignCenter)
        logo_lbl.setFixedHeight(100) 
        
        # Busca el archivo 'logo.png' en la misma carpeta que main.py
        base_dir = os.path.dirname(os.path.abspath(__file__))
        image_path = os.path.join(base_dir, "logo.png") 
        
        if os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            # Escalar manteniendo calidad (230px ancho max, 150px alto max)
            scaled_pixmap = pixmap.scaled(230, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_lbl.setPixmap(scaled_pixmap)
        else:
            # Texto de respaldo si no encuentra la imagen
            logo_lbl.setText("TESCH")
            logo_lbl.setStyleSheet("color: white; font-weight: bold; font-size: 30px;")

        ly.addWidget(logo_lbl)
        
        # --- BOTONES MENU ---
        self.group = QButtonGroup()
        self.group.setExclusive(True)
        
        buttons = [
            ("Dashboard", 0), ("Registro", 1), ("Alumnos", 2), 
            ("Talleres", 3), ("Constancia", 4), ("Expediente", 5)
        ]
        
        for text, idx in buttons:
            btn = AnimButton(f" {text}")
            btn.clicked.connect(lambda _, i=idx: self.switch_page(i))
            self.group.addButton(btn)
            ly.addWidget(btn)
            
        ly.addStretch()
        self.layout.addWidget(self.sidebar)

    def setup_pages(self):
        self.stack = QStackedWidget()
        # Fondo base para evitar fantasmas visuales
        self.stack.setStyleSheet("background-color: #f1f5f9;")
        
        self.layout.addWidget(self.stack)
        
        self.opacity_effect = QGraphicsOpacityEffect(self.stack)
        self.stack.setGraphicsEffect(self.opacity_effect)
        self.anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.anim.setDuration(300)

        self.pages = [
            DashboardPage(self.engine),
            RegistroPage(self.engine, self),
            AlumnosPage(self.engine),
            TalleresPage(self.engine),
            ConstanciaPage(self.engine),
            ExpedientePage(self.engine)
        ]
        
        for p in self.pages:
            self.stack.addWidget(p)

    def switch_page(self, index):
        self.anim.setStartValue(0)
        self.anim.setEndValue(1)
        self.stack.setCurrentIndex(index)
        self.anim.start()
        
        page = self.pages[index]
        if hasattr(page, 'refresh'): page.refresh()
        elif hasattr(page, 'refresh_table'): page.refresh_table()
        elif hasattr(page, 'refresh_alumni_table'): page.refresh_alumni_table()
        elif hasattr(page, 'refresh_t_table_general'): page.refresh_t_table_general()
        elif hasattr(page, 'apply_filter'): page.apply_filter()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # APLICAR ESTILOS GLOBALES
    app.setStyleSheet(GLOBAL_STYLES)
    
    window = MainApp()
    window.show()
    sys.exit(app.exec())