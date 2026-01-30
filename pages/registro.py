import uuid
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame, QGridLayout, QLineEdit, 
    QComboBox, QPushButton, QMessageBox, QScrollArea, QHBoxLayout, 
    QRadioButton
)
from PySide6.QtCore import Qt
from config import CAREERS, WORKSHOPS

class RegistroPage(QWidget):
    def __init__(self, engine, main_app):
        super().__init__()
        self.engine = engine
        self.main_app = main_app
        self.setup_ui()

    def create_line(self):
        """Crea una línea divisoria sutil"""
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #e2e8f0; max-height: 1px; border: none; margin-top: 5px; margin-bottom: 20px;")
        return line

    def setup_ui(self):
        # Layout principal de la página
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(10)

        # 1. ENCABEZADO
        header = QLabel("Registro de Alumnos")
        header.setStyleSheet("font-size: 26px; font-weight: bold; color: #0f172a; font-family: 'Segoe UI';")
        main_layout.addWidget(header)
        
        sub_header = QLabel("Capture los datos del nuevo expediente académico")
        sub_header.setStyleSheet("color: #64748b; font-size: 14px; font-family: 'Segoe UI'; margin-bottom: 10px;")
        main_layout.addWidget(sub_header)
        main_layout.addWidget(self.create_line())

        # 2. ÁREA DE SCROLL (Para que quepa en pantallas pequeñas)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")
        
        container = QWidget()
        form_ly = QVBoxLayout(container)
        form_ly.setSpacing(25)
        form_ly.setContentsMargins(0, 0, 10, 0) # Margen derecho para la barra de scroll

        # --- ESTILOS CSS ---
        style_card = """
            QFrame { background: white; border-radius: 12px; border: 1px solid #e2e8f0; }
            QLabel { border: none; background: transparent; color: #1e293b; font-weight: 600; font-family: 'Segoe UI'; }
        """
        
        style_inputs = """
            QLineEdit, QComboBox { 
                background: #f8fafc; 
                border: 1px solid #e2e8f0; 
                padding: 10px; 
                border-radius: 6px; 
                color: #334155;
                font-family: 'Segoe UI';
            }
            QLineEdit:focus, QComboBox:focus { border: 1px solid #3b82f6; background: white; }
            QRadioButton { color: #334155; font-family: 'Segoe UI'; spacing: 8px; }
            
            /* Arreglo para desplegables */
            QComboBox QAbstractItemView {
                background-color: white; color: #334155; selection-background-color: #3b82f6; selection-color: white; border: 1px solid #e2e8f0;
            }
        """

        # --- TARJETA 1: DATOS PERSONALES ---
        card_personal = QFrame()
        card_personal.setStyleSheet(style_card)
        p_ly = QVBoxLayout(card_personal)
        p_ly.setContentsMargins(30, 30, 30, 30)
        
        p_ly.addWidget(QLabel("<span style='font-size: 16px; color:#0f172a;'>Datos Personales</span>"))
        p_ly.addWidget(QLabel("<span style='color: #94a3b8; font-size: 12px; font-weight:normal;'>Información básica del alumno</span>"))
        p_ly.addWidget(self.create_line())

        grid_p = QGridLayout()
        grid_p.setVerticalSpacing(15); grid_p.setHorizontalSpacing(20)

        # Matrícula
        grid_p.addWidget(QLabel("Matrícula *"), 0, 0)
        self.r_mat = QLineEdit(); self.r_mat.setPlaceholderText("Ej: 20230001"); self.r_mat.setStyleSheet(style_inputs)
        grid_p.addWidget(self.r_mat, 1, 0)

        # Género (Radio Buttons)
        grid_p.addWidget(QLabel("Género *"), 0, 1)
        gen_ly = QHBoxLayout()
        self.r_gen_m = QRadioButton("Masculino"); self.r_gen_m.setChecked(True); self.r_gen_m.setStyleSheet(style_inputs)
        self.r_gen_f = QRadioButton("Femenino"); self.r_gen_f.setStyleSheet(style_inputs)
        gen_ly.addWidget(self.r_gen_m); gen_ly.addWidget(self.r_gen_f); gen_ly.addStretch()
        grid_p.addLayout(gen_ly, 1, 1)

        # Teléfono
        grid_p.addWidget(QLabel("Teléfono *"), 0, 2)
        self.r_tel = QLineEdit(); self.r_tel.setPlaceholderText("10 dígitos"); self.r_tel.setStyleSheet(style_inputs)
        grid_p.addWidget(self.r_tel, 1, 2)

        # Apellidos y Nombre
        grid_p.addWidget(QLabel("Apellido Paterno *"), 2, 0)
        self.r_pat = QLineEdit(); self.r_pat.setPlaceholderText("Apellido paterno"); self.r_pat.setStyleSheet(style_inputs)
        grid_p.addWidget(self.r_pat, 3, 0)

        grid_p.addWidget(QLabel("Apellido Materno *"), 2, 1)
        self.r_mat_ap = QLineEdit(); self.r_mat_ap.setPlaceholderText("Apellido materno"); self.r_mat_ap.setStyleSheet(style_inputs)
        grid_p.addWidget(self.r_mat_ap, 3, 1)

        grid_p.addWidget(QLabel("Nombre(s) *"), 2, 2)
        self.r_nom = QLineEdit(); self.r_nom.setPlaceholderText("Nombre(s)"); self.r_nom.setStyleSheet(style_inputs)
        grid_p.addWidget(self.r_nom, 3, 2)

        p_ly.addLayout(grid_p)
        form_ly.addWidget(card_personal)

        # --- TARJETA 2: DATOS ACADÉMICOS ---
        card_academic = QFrame()
        card_academic.setStyleSheet(style_card)
        a_ly = QVBoxLayout(card_academic)
        a_ly.setContentsMargins(30, 30, 30, 30)

        a_ly.addWidget(QLabel("<span style='font-size: 16px; color:#0f172a;'>Datos Académicos</span>"))
        a_ly.addWidget(QLabel("<span style='color: #94a3b8; font-size: 12px; font-weight:normal;'>Información de la inscripción</span>"))
        a_ly.addWidget(self.create_line())

        grid_a = QGridLayout()
        grid_a.setVerticalSpacing(15); grid_a.setHorizontalSpacing(20)

        # Carrera
        grid_a.addWidget(QLabel("Carrera *"), 0, 0)
        self.r_car = QComboBox(); self.r_car.addItems(CAREERS); self.r_car.setStyleSheet(style_inputs)
        grid_a.addWidget(self.r_car, 1, 0)

        # Ciclo Escolar
        grid_a.addWidget(QLabel("Ciclo Escolar *"), 0, 1)
        self.r_cyc = QComboBox(); self.r_cyc.addItems(["2026-1", "2026-2"]); self.r_cyc.setStyleSheet(style_inputs)
        grid_a.addWidget(self.r_cyc, 1, 1)

        # Semestre
        grid_a.addWidget(QLabel("Semestre *"), 0, 2)
        self.r_sem = QComboBox(); self.r_sem.addItems([str(i) for i in range(1, 13)]); self.r_sem.setStyleSheet(style_inputs)
        grid_a.addWidget(self.r_sem, 1, 2)

        # Taller
        grid_a.addWidget(QLabel("Taller Inicial *"), 2, 0)
        self.r_tal = QComboBox(); self.r_tal.addItems(WORKSHOPS); self.r_tal.setStyleSheet(style_inputs)
        grid_a.addWidget(self.r_tal, 3, 0)

        a_ly.addLayout(grid_a)
        form_ly.addWidget(card_academic)

        # --- BOTONES DE ACCIÓN ---
        btn_ly = QHBoxLayout()
        
        btn_save = QPushButton("💾 Guardar Registro")
        btn_save.setCursor(Qt.PointingHandCursor)
        btn_save.setStyleSheet("""
            QPushButton { background-color: #1e3a8a; color: white; padding: 12px 25px; border-radius: 8px; font-weight: bold; font-family: 'Segoe UI'; border: none; }
            QPushButton:hover { background-color: #172554; }
        """)
        btn_save.clicked.connect(self.handle_save)

        btn_clear = QPushButton("🔄 Limpiar Formulario")
        btn_clear.setCursor(Qt.PointingHandCursor)
        btn_clear.setStyleSheet("""
            QPushButton { background-color: white; border: 1px solid #cbd5e1; padding: 12px 25px; border-radius: 8px; color: #475569; font-family: 'Segoe UI'; font-weight: 600; }
            QPushButton:hover { background-color: #f1f5f9; }
        """)
        btn_clear.clicked.connect(self.clear_form)

        btn_ly.addWidget(btn_save)
        btn_ly.addWidget(btn_clear)
        btn_ly.addStretch()
        
        form_ly.addLayout(btn_ly)
        
        scroll.setWidget(container)
        main_layout.addWidget(scroll)

    def handle_save(self):
        """Valida y guarda los datos en el sistema"""
        if not self.r_mat.text().strip() or not self.r_nom.text().strip() or not self.r_pat.text().strip():
            return QMessageBox.warning(self, "Campos Incompletos", "Por favor llene Matrícula, Nombre y Apellido Paterno.")
        
        gen_txt = "Masculino" if self.r_gen_m.isChecked() else "Femenino"
        
        data = {
            "id": str(uuid.uuid4()), 
            "matricula": self.r_mat.text().strip(), 
            "nombres": self.r_nom.text().strip(),
            "apellidoPaterno": self.r_pat.text().strip(),
            "apellidoMaterno": self.r_mat_ap.text().strip(),
            "genero": gen_txt,
            "telefono": self.r_tel.text().strip(),
            "career": self.r_car.currentText(),
            "schoolCycle": self.r_cyc.currentText(),
            "semestre": self.r_sem.currentText(),
            "workshops": [{"name": self.r_tal.currentText(), "status": "Cursando"}],
            "documents": {"identificacion": False, "curp": False, "solicitud": False}
        }
        
        if self.engine.add_student(data):
            QMessageBox.information(self, "Éxito", "Alumno registrado correctamente.")
            self.clear_form()
            # Navegar al Dashboard después de guardar
            if self.main_app:
                self.main_app.switch_page(0) 
        else:
            QMessageBox.warning(self, "Error", "La matrícula ya está registrada.")

    def clear_form(self):
        """Limpia todos los campos"""
        self.r_mat.clear()
        self.r_nom.clear()
        self.r_pat.clear()
        self.r_mat_ap.clear()
        self.r_tel.clear()
        self.r_gen_m.setChecked(True)
        self.r_car.setCurrentIndex(0)
        self.r_tal.setCurrentIndex(0)