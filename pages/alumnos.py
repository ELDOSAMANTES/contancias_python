from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox, 
    QTableWidget, QHeaderView, QTableWidgetItem, QFrame, QStackedWidget, QAbstractItemView
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QBrush
# Asegúrate de tener tu archivo config.py o ajusta estas importaciones según tu proyecto
try:
    from config import CAREERS, WORKSHOPS
except ImportError:
    # Valores por defecto si falla la importación
    CAREERS = ["Ingeniería en Sistemas", "Ingeniería Industrial", "Gastronomía", "Energías Renovables"]
    WORKSHOPS = ["Fútbol", "Danza", "Música", "Taekwondo", "Programación", "Robótica"]

class AlumnosPage(QWidget):
    def __init__(self, engine):
        super().__init__()
        self.engine = engine
        # Fondo sólido para evitar transparencias
        self.setStyleSheet("background-color: #f1f5f9;")
        
        self.setup_ui()
        self.refresh_alumni_table()

    def create_line(self):
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #e2e8f0; max-height: 1px; border: none; margin: 10px 0;")
        return line

    def setup_ui(self):
        ly = QVBoxLayout(self)
        ly.setContentsMargins(30, 30, 30, 30)
        ly.setSpacing(15)

        # 1. ENCABEZADO
        header_ly = QHBoxLayout()
        icon_h = QLabel("👥") 
        icon_h.setFixedSize(45, 45)
        icon_h.setAlignment(Qt.AlignCenter)
        icon_h.setStyleSheet("background-color: white; border-radius: 8px; font-size: 20px; border: 1px solid #e2e8f0;")
        
        title_vly = QVBoxLayout()
        title_lbl = QLabel("Alumnos")
        title_lbl.setStyleSheet("font-size: 24px; font-weight: bold; color: #0f172a; border: none; font-family: 'Segoe UI';")
        sub_lbl = QLabel("Consulta y gestión de expedientes académicos (Meta: 5.0 Créditos)")
        sub_lbl.setStyleSheet("color: #64748b; border: none; font-size: 13px; font-family: 'Segoe UI';")
        title_vly.addWidget(title_lbl); title_vly.addWidget(sub_lbl)
        
        header_ly.addWidget(icon_h); header_ly.addLayout(title_vly); header_ly.addStretch()
        ly.addLayout(header_ly)
        ly.addWidget(self.create_line())

        # 2. FILTROS
        filter_card = QFrame()
        filter_card.setStyleSheet("""
            QFrame { background: white; border-radius: 12px; border: 1px solid #e2e8f0; }
            QLineEdit, QComboBox { 
                background: #f8fafc; 
                border: 1px solid #e2e8f0; 
                padding: 8px; 
                border-radius: 6px; 
                color: #1e293b;
                font-family: 'Segoe UI';
            }
            QLineEdit:focus, QComboBox:focus { border: 1px solid #3b82f6; background: white; }
            QComboBox QAbstractItemView {
                background-color: white; 
                color: #1e293b; 
                selection-background-color: #3b82f6; 
                selection-color: white;
            }
        """)
        f_ly = QVBoxLayout(filter_card)
        f_ly.setContentsMargins(20, 20, 20, 20)
        
        search_ly = QHBoxLayout()
        
        self.a_search = QLineEdit()
        self.a_search.setPlaceholderText("🔍 Buscar por matrícula, nombre...")
        self.a_search.textChanged.connect(self.refresh_alumni_table)
        
        self.a_f_car = QComboBox()
        self.a_f_car.addItems(["Todas las carreras"] + CAREERS)
        self.a_f_car.currentIndexChanged.connect(self.refresh_alumni_table)
        
        self.a_f_ws = QComboBox()
        self.a_f_ws.addItems(["Todos los talleres"] + WORKSHOPS)
        self.a_f_ws.currentIndexChanged.connect(self.refresh_alumni_table)
        
        search_ly.addWidget(self.a_search, 4)
        search_ly.addWidget(self.a_f_car, 2)
        search_ly.addWidget(self.a_f_ws, 2)
        f_ly.addLayout(search_ly)

        self.create_line()
        
        self.a_count_lbl = QLabel("Cargando...")
        self.a_count_lbl.setStyleSheet("color: #64748b; font-size: 12px; border: none; margin-top: 5px; background: transparent;")
        f_ly.addWidget(self.a_count_lbl)
        
        ly.addWidget(filter_card)

        # 3. TABLA
        self.a_stack = QStackedWidget()
        self.a_stack.setStyleSheet("background: transparent;")
        
        self.a_table = QTableWidget(0, 6)
        cols = ["MATRÍCULA", "NOMBRE COMPLETO", "CARRERA", "SEMESTRE", "AVANCE (5.0)", "ESTADO"]
        self.a_table.setColumnCount(len(cols))
        self.a_table.setHorizontalHeaderLabels(cols)
        
        self.a_table.verticalHeader().setVisible(False)
        self.a_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.a_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.a_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.a_table.setShowGrid(False)
        self.a_table.setFocusPolicy(Qt.NoFocus)
        
        self.a_table.setStyleSheet("""
            QTableWidget { background: white; border-radius: 10px; border: none; font-family: 'Segoe UI'; }
            QHeaderView::section { 
                background-color: #f8fafc; 
                color: #0f172a; 
                padding: 12px; 
                font-weight: bold; 
                border-bottom: 2px solid #e2e8f0;
                border-top: none; border-left: none; border-right: none;
            }
            QTableWidget::item { padding: 8px; border-bottom: 1px solid #f1f5f9; color: #334155; }
            QTableWidget::item:selected { background-color: #eff6ff; color: #1e40af; }
        """)
        
        self.empty_view = QWidget()
        ev_ly = QVBoxLayout(self.empty_view); ev_ly.setAlignment(Qt.AlignCenter)
        ev_icon = QLabel("🔍"); ev_icon.setStyleSheet("font-size: 40px; color: #cbd5e1; border: none; background: transparent;")
        ev_msg = QLabel("No se encontraron resultados")
        ev_msg.setStyleSheet("color: #94a3b8; font-weight: bold; border: none; font-family: 'Segoe UI'; background: transparent;")
        ev_ly.addWidget(ev_icon); ev_ly.addWidget(ev_msg)

        self.a_stack.addWidget(self.a_table)
        self.a_stack.addWidget(self.empty_view)
        
        ly.addWidget(self.a_stack)

    # --- LÓGICA CORREGIDA (SUMA VALORES REALES / META 5.0) ---
    def refresh_alumni_table(self):
        query = self.a_search.text().lower().strip()
        f_car = self.a_f_car.currentText()
        f_ws = self.a_f_ws.currentText()
        
        self.a_table.setRowCount(0)
        found_count = 0
        
        students = self.engine.students if hasattr(self.engine, 'students') else []

        for s in students:
            # 1. Preparar datos
            mat = str(s.get('matricula', '')).lower()
            full_name = f"{s.get('nombres','')} {s.get('apellidoPaterno','')} {s.get('apellidoMaterno','')}".lower()
            s_car = s.get('career', '') 
            
            workshops = s.get('workshops', [])
            workshop_names = [w.get('name', '').upper() for w in workshops]

            # 2. CALCULAR CRÉDITOS (CORRECCIÓN AQUÍ)
            total_credits = 0.0
            for w in workshops:
                # Sumar solo si está acreditado/entregado
                if w.get('status') in ['Acreditado', 'Entregado']:
                    # Usar .get('value', 1.0) para que si es viejo, valga 1
                    try:
                        total_credits += float(w.get('value', 1.0))
                    except:
                        total_credits += 1.0

            # 3. APLICAR FILTROS
            match_query = True
            if query:
                match_query = (query in mat) or (query in full_name)
            
            match_car = True
            if f_car != "Todas las carreras":
                match_car = (f_car.upper() in s_car.upper())
            
            match_ws = True
            if f_ws != "Todos los talleres":
                match_ws = (f_ws.upper() in workshop_names)

            if match_query and match_car and match_ws:
                found_count += 1
                r = self.a_table.rowCount()
                self.a_table.insertRow(r)
                
                self.a_table.setItem(r, 0, QTableWidgetItem(s.get('matricula', '')))
                self.a_table.setItem(r, 1, QTableWidgetItem(full_name.upper()))
                self.a_table.setItem(r, 2, QTableWidgetItem(s_car.upper()))
                self.a_table.setItem(r, 3, QTableWidgetItem(str(s.get('semestre', '-'))))
                
                # MOSTRAR AVANCE REAL (X / 5.0)
                self.a_table.setItem(r, 4, QTableWidgetItem(f"{total_credits} / 5.0"))
                
                # DEFINIR ESTATUS
                if total_credits >= 5.0:
                    status_text = "✨ Completado"
                    color_hex = "#10b981" # Verde
                elif total_credits > 0:
                    status_text = "En proceso"
                    color_hex = "#f59e0b" # Naranja
                else:
                    status_text = "Sin créditos"
                    color_hex = "#ef4444" # Rojo
                
                status_item = QTableWidgetItem(status_text)
                status_item.setForeground(QBrush(QColor(color_hex)))
                status_item.setFont(self.font()) # Negrita si deseas
                
                self.a_table.setItem(r, 5, status_item)

        self.a_count_lbl.setText(f"Se encontraron {found_count} alumnos")
        self.a_stack.setCurrentIndex(0 if found_count > 0 else 1)