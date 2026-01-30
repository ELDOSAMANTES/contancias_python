import sys
import json
import os
import uuid
from datetime import datetime
import fitz

# --- PySide6 / GUI Imports ---
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QTableWidget, QTableWidgetItem, QHeaderView, 
    QMessageBox, QDialog, QLineEdit, QComboBox, QStackedWidget,
    QButtonGroup, QGridLayout, QInputDialog, QCheckBox, QScrollArea, QRadioButton
, QFileDialog, QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QBrush
from PySide6.QtCharts import QChart, QChartView, QPieSeries
from PySide6.QtGui import QImage, QPixmap, QColor
from PySide6.QtPdf import QPdfDocument
from PySide6.QtPdfWidgets import QPdfView


# --- CONFIGURACIÓN DE DATOS ---
DB_PATH = 'database.json'
CAREERS = ['Ingeniería en Sistemas', 'Ingeniería Industrial', 'Ingeniería Electromecánica', 'Ingeniería en Gestión', 'Licenciatura en Administración', 'Contador Público']
WORKSHOPS = ['Fútbol', 'Ajedrez', 'Música', 'Danza', 'Robótica', 'Teatro', 'Programación']
CYCLES = ['2024-1', '2024-2', '2025-1', '2025-2']

# --- MOTOR DE DATOS (StudentEngine) ---
class StudentEngine:
    def __init__(self):
        self.students = self._load()

    def _load(self):
        if os.path.exists(DB_PATH):
            try:
                with open(DB_PATH, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except: return []
        return []

    def save(self):
        with open(DB_PATH, 'w', encoding='utf-8') as f:
            json.dump(self.students, f, indent=4, ensure_ascii=False)

    def add_student(self, student_data):
        if any(s['matricula'] == student_data['matricula'] for s in self.students):
            return False
        self.students.append(student_data)
        self.save()
        return True

    def get_stats(self):
        """Calcula estadísticas para el Dashboard"""
        stats = {
            "total": len(self.students), 
            "cursando": 0, 
            "accredited": 0, 
            "ready": 0, 
            "byCareer": {}, 
            "byWorkshop": {}
        }
        for s in self.students:
            stats['byCareer'][s['career']] = stats['byCareer'].get(s['career'], 0) + 1
            # Contamos alumnos con créditos completos (2 de 2)
            acc_count = len([w for w in s.get('workshops', []) if w.get('status') == 'Acreditado'])
            if acc_count >= 2: stats['ready'] += 1
            
            for w in s.get('workshops', []):
                stats['byWorkshop'][w['name']] = stats['byWorkshop'].get(w['name'], 0) + 1
                if w['status'] == 'Acreditado': stats['accredited'] += 1
                elif w['status'] == 'Cursando': stats['cursando'] += 1
        return stats
# --- WIDGET: TARJETA DE ESTADÍSTICA ---
class StatCard(QFrame):
    def __init__(self, title, value, desc, color_bg, icon_char):
        super().__init__()
        self.setObjectName("StatCard")
        self.setMinimumWidth(240); self.setFixedHeight(120)
        self.setStyleSheet(f"#StatCard {{ background-color: {color_bg}; border-radius: 12px; border: 1px solid rgba(0,0,0,0.05); }}")
        layout = QHBoxLayout(self)
        text_ly = QVBoxLayout()
        v_lbl = QLabel(str(value)); v_lbl.setStyleSheet("font-size: 28px; font-weight: 800; color: #0f172a; background: transparent;")
        t_lbl = QLabel(title); t_lbl.setStyleSheet("font-size: 13px; font-weight: 600; color: #64748b; background: transparent;")
        d_lbl = QLabel(desc); d_lbl.setStyleSheet("font-size: 11px; color: #94a3b8; background: transparent;")
        text_ly.addWidget(t_lbl); text_ly.addWidget(v_lbl); text_ly.addWidget(d_lbl)
        icon_lbl = QLabel(icon_char); icon_lbl.setStyleSheet("font-size: 24px; background: rgba(0,0,0,0.04); border-radius: 10px; padding: 8px;")
        layout.addLayout(text_ly); layout.addWidget(icon_lbl, alignment=Qt.AlignTop | Qt.AlignRight)

# --- APLICACIÓN PRINCIPAL ---
class TeschApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.engine = StudentEngine()
        self.setWindowTitle("TESCH - Gestión Académica")
        self.resize(1300, 950)
        self.current_student = None
        self.engine = StudentEngine()
        self.setup_ui()

    def setup_ui(self):
        self.central = QWidget(); self.setCentralWidget(self.central)
        self.layout = QHBoxLayout(self.central); self.layout.setContentsMargins(0, 0, 0, 0); self.layout.setSpacing(0)

        # Sidebar
        self.sidebar = QFrame(); self.sidebar.setFixedWidth(260); self.sidebar.setStyleSheet("background-color: #0f172a;")
        sidebar_ly = QVBoxLayout(self.sidebar)
        logo = QLabel("🎓 TESCH"); logo.setStyleSheet("font-size: 22px; font-weight: bold; color: white; margin: 20px;")
        sidebar_ly.addWidget(logo)

        self.nav_group = QButtonGroup(self)
        menu = [("Dashboard", 0), ("Registro", 1), ("Alumnos", 2), ("Talleres", 3), ("Documentos", 4)]
        for text, idx in menu:
            btn = QPushButton(f"  {text}"); btn.setCheckable(True); btn.setFixedHeight(50)
            btn.setStyleSheet("QPushButton { background: none; color: #94a3b8; text-align: left; padding-left: 20px; border: none; font-size: 14px; } QPushButton:checked { background-color: #3b82f6; color: white; font-weight: bold; }")
            btn.clicked.connect(lambda _, i=idx: self.switch_page(i))
            self.nav_group.addButton(btn); sidebar_ly.addWidget(btn)
        sidebar_ly.addStretch(); self.layout.addWidget(self.sidebar)

        self.pages = QStackedWidget(); self.layout.addWidget(self.pages)
        
        # Inicialización de Ventanas
        self.init_dashboard(); self.init_registro(); self.init_alumnos(); self.init_talleres(); self.init_documentos()
        
        self.apply_styles()
        self.switch_page(0)

    def apply_styles(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #f1f5f9; }
            QFrame#WhiteCard { background-color: white; border-radius: 12px; border: 1px solid #e2e8f0; }
            QLabel { color: #1e293b; font-family: 'Inter'; }
            QLineEdit, QComboBox { background-color: #f8fafc; border: 1px solid #e2e8f0; padding: 10px; border-radius: 6px; color: #0f172a; }
            QPushButton#SaveBtn { background-color: #0f172a; color: white; font-weight: bold; padding: 12px 25px; border-radius: 8px; border: none; }
            QPushButton#ActionBtn { background-color: #3b82f6; color: white; font-weight: bold; border-radius: 6px; padding: 8px; border: none; }
            QTableWidget { background-color: white; color: #1e293b; border: none; gridline-color: #f1f5f9; border-radius: 8px; }
            QHeaderView::section { background-color: #f8fafc; color: #64748b; padding: 10px; border: none; font-weight: bold; }
        """)

    def switch_page(self, i):
        self.pages.setCurrentIndex(i)
        if i == 0: self.refresh_dashboard()
        elif i == 2: self.refresh_alumni_table()
        elif i == 4: self.refresh_docs_table()

    def create_line(self):
        line = QFrame(); line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #e2e8f0; max-height: 1px; border: none; margin-top: 5px; margin-bottom: 10px;")
        return line

    # =================================================================
    # VENTANA 1: DASHBOARD
    # =================================================================
    def init_dashboard(self):
        page = QWidget(); ly = QVBoxLayout(page); ly.setContentsMargins(30, 30, 30, 30)
        ly.addWidget(QLabel("<h2 style='font-size: 24px;'>Dashboard</h2>"))
        ly.addWidget(self.create_line())
        self.stats_ly = QHBoxLayout(); ly.addLayout(self.stats_ly)

        charts_ly = QHBoxLayout()
        self.c1_view = QChartView(); self.c1_view.setRenderHint(QPainter.Antialiasing); self.c1_view.setStyleSheet("background: transparent;")
        c1_card = QFrame(); c1_card.setObjectName("WhiteCard"); c1_v = QVBoxLayout(c1_card)
        c1_v.addWidget(QLabel("<b>Distribución por Carrera</b>")); c1_v.addWidget(self.c1_view)
        charts_ly.addWidget(c1_card)

        self.c2_view = QChartView(); self.c2_view.setRenderHint(QPainter.Antialiasing); self.c2_view.setStyleSheet("background: transparent;")
        c2_card = QFrame(); c2_card.setObjectName("WhiteCard"); c2_v = QVBoxLayout(c2_card)
        c2_v.addWidget(QLabel("<b>Talleres Populares</b>")); c2_v.addWidget(self.c2_view)
        charts_ly.addWidget(c2_card)
        ly.addLayout(charts_ly)
        self.pages.insertWidget(0, page)

    def refresh_dashboard(self):
        stats = self.engine.get_stats()
        for i in reversed(range(self.stats_ly.count())): self.stats_ly.itemAt(i).widget().setParent(None)
        self.stats_ly.addWidget(StatCard("Total Alumnos", stats['total'], "Registrados", "white", "👥"))
        self.stats_ly.addWidget(StatCard("Talleres Cursando", stats['cursando'], "En proceso", "white", "📖"))
        self.stats_ly.addWidget(StatCard("Talleres Acreditados", stats['accredited'], "Completados", "white", "🏅"))
        self.stats_ly.addWidget(StatCard("Listos p/ Constancia", stats['ready'], "Con 2+ créditos", "white", "📄"))

        def setup_pie(view, data):
            series = QPieSeries(); series.setHoleSize(0.35)
            for n, v in data.items(): series.append(n, v)
            chart = QChart(); chart.addSeries(series); chart.setBackgroundVisible(False); view.setChart(chart)
        setup_pie(self.c1_view, stats['byCareer'])
        setup_pie(self.c2_view, dict(list(stats['byWorkshop'].items())[:5]))

   # =================================================================
    # VENTANA: REGISTRO (DISEÑO PROPORCIONAL Y VISIBILIDAD CORREGIDA)
    # =================================================================
    def init_registro(self):
        page = QWidget()
        ly = QVBoxLayout(page)
        ly.setContentsMargins(40, 40, 40, 40)
        ly.setSpacing(10)

        # Encabezado principal sin recuadros en el título
        header = QLabel("Registro de Alumnos")
        header.setStyleSheet("font-size: 26px; font-weight: bold; color: #0f172a; border: none;")
        ly.addWidget(header)
        
        sub_header = QLabel("Capture los datos del nuevo expediente académico")
        sub_header.setStyleSheet("color: #64748b; border: none; margin-bottom: 5px;")
        ly.addWidget(sub_header)
        ly.addWidget(self.create_line())

        # Área de desplazamiento para evitar que el contenido se amontone hacia abajo
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")
        
        container = QWidget()
        form_ly = QVBoxLayout(container)
        form_ly.setSpacing(25)
        
        # --- ESTILO UNIFICADO Y CORRECCIÓN DE VISIBILIDAD ---
        # Este CSS asegura que las opciones de los desplegables no se vean en blanco
        style_fields = """
            QFrame { background: white; border-radius: 12px; border: 1px solid #e2e8f0; }
            QLabel { border: none; background: transparent; color: #1e293b; }
            
            QLineEdit, QComboBox { 
                background: #f8fafc; 
                border: 1px solid #e2e8f0; 
                padding: 10px; 
                border-radius: 8px; 
                color: #1e293b;
            }
            
            /* Corrección para que el texto de las opciones sea visible (Negro sobre Blanco) */
            QComboBox QAbstractItemView {
                background-color: white;
                color: #1e293b;
                selection-background-color: #3b82f6;
                selection-color: white;
                border: 1px solid #e2e8f0;
            }

            QRadioButton { border: none; background: transparent; spacing: 8px; color: #1e293b; }
        """

        # --- SECCIÓN 1: DATOS PERSONALES ---
        p_card = QFrame()
        p_card.setStyleSheet(style_fields)
        p_ly = QVBoxLayout(p_card)
        p_ly.setContentsMargins(25, 25, 25, 25)
        
        p_ly.addWidget(QLabel("<b style='font-size: 16px;'>Datos Personales</b>"))
        p_ly.addWidget(QLabel("<span style='color: #94a3b8; font-size: 11px;'>Información básica del alumno</span>"))
        p_ly.addWidget(self.create_line())
        
        grid_p = QGridLayout()
        grid_p.setVerticalSpacing(12)
        grid_p.setHorizontalSpacing(20)

        # Fila 1: Matrícula, Género y Teléfono (Distribución Horizontal Proporcional)
        grid_p.addWidget(QLabel("Matrícula *"), 0, 0)
        self.r_mat = QLineEdit(); self.r_mat.setPlaceholderText("Ej: 20230001")
        grid_p.addWidget(self.r_mat, 1, 0)
        
        # Corrección: Texto "Masculino" y "Femenino" añadido a los RadioButtons
        grid_p.addWidget(QLabel("Género *"), 0, 1)
        gen_ly = QHBoxLayout()
        self.r_gen_m = QRadioButton("Masculino") 
        self.r_gen_f = QRadioButton("Femenino")
        self.r_gen_m.setChecked(True)
        gen_ly.addWidget(self.r_gen_m); gen_ly.addWidget(self.r_gen_f); gen_ly.addStretch()
        grid_p.addLayout(gen_ly, 1, 1)
        
        grid_p.addWidget(QLabel("Teléfono *"), 0, 2)
        self.r_tel = QLineEdit(); self.r_tel.setPlaceholderText("10 dígitos")
        grid_p.addWidget(self.r_tel, 1, 2)
        
        # Fila 2: Apellidos y Nombre
        grid_p.addWidget(QLabel("Apellido Paterno *"), 2, 0)
        self.r_pat = QLineEdit(); self.r_pat.setPlaceholderText("Apellido paterno")
        grid_p.addWidget(self.r_pat, 3, 0)

        grid_p.addWidget(QLabel("Apellido Materno *"), 2, 1)
        self.r_mat_ap = QLineEdit(); self.r_mat_ap.setPlaceholderText("Apellido materno")
        grid_p.addWidget(self.r_mat_ap, 3, 1)

        grid_p.addWidget(QLabel("Nombre(s) *"), 2, 2)
        self.r_nom = QLineEdit(); self.r_nom.setPlaceholderText("Nombre(s)")
        grid_p.addWidget(self.r_nom, 3, 2)
        
        p_ly.addLayout(grid_p)
        form_ly.addWidget(p_card)

        # --- SECCIÓN 2: DATOS ACADÉMICOS ---
        a_card = QFrame()
        a_card.setStyleSheet(style_fields)
        a_ly = QVBoxLayout(a_card)
        a_ly.setContentsMargins(25, 25, 25, 25)
        
        a_ly.addWidget(QLabel("<b style='font-size: 16px;'>Datos Académicos</b>"))
        a_ly.addWidget(QLabel("<span style='color: #94a3b8; font-size: 11px;'>Información de la inscripción</span>"))
        a_ly.addWidget(self.create_line())
        
        grid_a = QGridLayout()
        grid_a.setSpacing(15)

        # Los desplegables ahora comparten el diseño visual de los campos de texto
        grid_a.addWidget(QLabel("Carrera *"), 0, 0)
        self.r_car = QComboBox(); self.r_car.addItems(CAREERS)
        grid_a.addWidget(self.r_car, 1, 0)
        
        grid_a.addWidget(QLabel("Ciclo Escolar *"), 0, 1)
        self.r_cyc = QComboBox(); self.r_cyc.addItems(["2026-1", "2026-2"])
        grid_a.addWidget(self.r_cyc, 1, 1)
        
        grid_a.addWidget(QLabel("Semestre *"), 0, 2)
        self.r_sem = QComboBox(); self.r_sem.addItems([str(i) for i in range(1, 13)])
        grid_a.addWidget(self.r_sem, 1, 2)
        
        grid_a.addWidget(QLabel("Taller Inicial *"), 2, 0)
        self.r_tal = QComboBox(); self.r_tal.addItems(WORKSHOPS)
        grid_a.addWidget(self.r_tal, 3, 0)
        
        a_ly.addLayout(grid_a)
        form_ly.addWidget(a_card)

        # --- BOTONES DE ACCIÓN ---
        btn_ly = QHBoxLayout()
        btn_save = QPushButton("💾 Guardar Registro")
        btn_save.setStyleSheet("background: #1e3a8a; color: white; padding: 12px 25px; border-radius: 8px; font-weight: bold; border: none;")
        btn_save.clicked.connect(self.handle_save)
        
        btn_clear = QPushButton("🔄 Limpiar Formulario")
        btn_clear.setStyleSheet("background: white; border: 1px solid #e2e8f0; padding: 12px 25px; border-radius: 8px; color: #1e293b;")
        
        btn_ly.addWidget(btn_save); btn_ly.addWidget(btn_clear); btn_ly.addStretch()
        form_ly.addLayout(btn_ly)
        
        scroll.setWidget(container)
        ly.addWidget(scroll)
        self.pages.insertWidget(1, page)

    # =================================================================
    # MÉTODO LÓGICO PARA PROCESAR EL REGISTRO
    # =================================================================
    def handle_save(self):
        if not self.r_mat.text().strip() or not self.r_nom.text().strip():
            return QMessageBox.warning(self, "Campos Vacíos", "La matrícula y el nombre son obligatorios.")
        
        gen_txt = "Masculino" if self.r_gen_m.isChecked() else "Femenino"
        data = {
            "id": str(uuid.uuid4()), 
            "matricula": self.r_mat.text().strip(), 
            "nombres": self.r_nom.text().strip(),
            "apellidoPaterno": self.r_pat.text().strip(),
            "apellidoMaterno": self.r_mat_ap.text().strip(),
            "genero": gen_txt,
            "career": self.r_car.currentText(), 
            "workshops": [{"name": self.r_tal.currentText(), "status": "Cursando"}],
            "documents": {"identificacion": False, "curp": False, "solicitud": False}
        }
        
        if self.engine.add_student(data):
            QMessageBox.information(self, "Éxito", "Alumno registrado correctamente.")
            self.r_mat.clear(); self.r_nom.clear(); self.r_pat.clear(); self.r_mat_ap.clear(); self.r_tel.clear()
            self.switch_page(0)
    # =================================================================
    # VENTANA: ALUMNOS (DISEÑO FINAL SIN ERRORES Y SIN FRANJA NEGRA)
    # =================================================================
    def init_alumnos(self):
        page = QWidget()
        ly = QVBoxLayout(page)
        ly.setContentsMargins(30, 30, 30, 30)
        ly.setSpacing(15)

        # --- ENCABEZADO ---
        header_ly = QHBoxLayout()
        icon_h = QLabel("👥") 
        icon_h.setFixedSize(45, 45)
        icon_h.setAlignment(Qt.AlignCenter)
        icon_h.setStyleSheet("background-color: #f1f5f9; border-radius: 8px; font-size: 20px; border: none;")
        
        title_vly = QVBoxLayout()
        title_lbl = QLabel("Alumnos")
        title_lbl.setStyleSheet("font-size: 24px; font-weight: bold; color: #0f172a; border: none;")
        sub_lbl = QLabel("Consulta y gestión de expedientes académicos")
        sub_lbl.setStyleSheet("color: #64748b; border: none; font-size: 13px;")
        title_vly.addWidget(title_lbl); title_vly.addWidget(sub_lbl)
        
        header_ly.addWidget(icon_h); header_ly.addLayout(title_vly); header_ly.addStretch()
        ly.addLayout(header_ly)
        ly.addWidget(self.create_line())

        # --- FILTROS CON VISIBILIDAD CORREGIDA ---
        filter_card = QFrame()
        filter_card.setStyleSheet("""
            QFrame { background: white; border-radius: 12px; border: 1px solid #e2e8f0; }
            QLineEdit, QComboBox { 
                background: #f8fafc; border: 1px solid #e2e8f0; padding: 10px; border-radius: 8px; color: #1e293b; 
            }
            /* Evita opciones en blanco en los desplegables */
            QComboBox QAbstractItemView {
                background-color: white; color: #1e293b; selection-background-color: #3b82f6; selection-color: white;
            }
        """)
        f_ly = QVBoxLayout(filter_card); f_ly.setContentsMargins(20, 20, 20, 20)
        
        search_ly = QHBoxLayout()
        self.a_search = QLineEdit(); self.a_search.setPlaceholderText("🔍 Buscar por matrícula, nombre...")
        self.a_search.textChanged.connect(self.refresh_alumni_table) # Conexión al método que faltaba
        
        self.a_f_car = QComboBox(); self.a_f_car.addItems(["Todas las carreras"] + CAREERS)
        self.a_f_car.currentIndexChanged.connect(self.refresh_alumni_table)
        
        self.a_f_ws = QComboBox(); self.a_f_ws.addItems(["Todos los talleres"] + WORKSHOPS)
        self.a_f_ws.currentIndexChanged.connect(self.refresh_alumni_table)
        
        search_ly.addWidget(self.a_search, 4); search_ly.addWidget(self.a_f_car, 2); search_ly.addWidget(self.a_f_ws, 2)
        f_ly.addLayout(search_ly)

        f_ly.addWidget(self.create_line())
        self.a_count_lbl = QLabel("Se encontraron 0 alumnos")
        self.a_count_lbl.setStyleSheet("color: #64748b; font-size: 13px; border: none;")
        f_ly.addWidget(self.a_count_lbl)
        ly.addWidget(filter_card)

        # --- TABLA (ELIMINACIÓN DE FRANJA NEGRA) ---
        self.a_stack = QStackedWidget()
        self.a_table = QTableWidget(0, 6)
        self.a_table.setHorizontalHeaderLabels(["MATRÍCULA", "NOMBRE COMPLETO", "CARRERA", "SEMESTRE", "CRÉDITOS", "ESTADO"])
        
        # OCULTA LA FRANJA NEGRA (Encabezado vertical)
        self.a_table.verticalHeader().setVisible(False) 
        self.a_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.a_table.setShowGrid(False) 
        self.a_table.setStyleSheet("""
            QTableWidget { background: white; border-radius: 10px; border: 1px solid #e2e8f0; }
            QHeaderView::section { background: #f8fafc; padding: 12px; font-weight: bold; color: #64748b; border: none; }
        """)
        
        # Vista Vacía
        self.empty_view = QWidget()
        ev_ly = QVBoxLayout(self.empty_view); ev_ly.setAlignment(Qt.AlignCenter)
        ev_icon = QLabel("👥"); ev_icon.setStyleSheet("font-size: 50px; color: #cbd5e1; border: none;")
        ev_msg = QLabel("No se encontraron alumnos\n<span style='font-size: 12px; color: #94a3b8;'>Intente ajustar los filtros de búsqueda</span>")
        ev_msg.setAlignment(Qt.AlignCenter); ev_msg.setStyleSheet("color: #64748b; font-weight: bold; border: none;")
        ev_ly.addWidget(ev_icon); ev_ly.addWidget(ev_msg)

        self.a_stack.addWidget(self.a_table); self.a_stack.addWidget(self.empty_view)
        ly.addWidget(self.a_stack)
        self.pages.insertWidget(2, page)

    # =================================================================
    # MÉTODO DE FILTRADO (EL QUE RESOLVERÁ EL ERROR)
    # =================================================================
    def refresh_alumni_table(self):
        query = self.a_search.text().lower()
        f_car = self.a_f_car.currentText()
        f_ws = self.a_f_ws.currentText()
        
        self.a_table.setRowCount(0)
        found_count = 0
        
        for s in self.engine.students:
            name_full = f"{s.get('apellidoPaterno','')} {s.get('apellidoMaterno','')} {s.get('nombres','')}".strip()
            
            # Lógica de filtros
            match_query = query in s['matricula'].lower() or query in name_full.lower()
            match_car = f_car == "Todas las carreras" or s['career'] == f_car
            match_ws = f_ws == "Todos los talleres" or any(w['name'] == f_ws for w in s['workshops'])

            if match_query and match_car and match_ws:
                found_count += 1
                r = self.a_table.rowCount()
                self.a_table.insertRow(r)
                
                acc = len([w for w in s['workshops'] if w['status'] == 'Acreditado'])
                
                self.a_table.setItem(r, 0, QTableWidgetItem(s['matricula']))
                self.a_table.setItem(r, 1, QTableWidgetItem(name_full))
                self.a_table.setItem(r, 2, QTableWidgetItem(s['career']))
                self.a_table.setItem(r, 3, QTableWidgetItem("1")) # Semestre
                self.a_table.setItem(r, 4, QTableWidgetItem(f"{acc}/2"))
                
                status_item = QTableWidgetItem("Acreditado" if acc >= 2 else "En proceso")
                status_item.setForeground(QColor("#10b981") if acc >= 2 else QColor("#f59e0b"))
                self.a_table.setItem(r, 5, status_item)

        # Actualizar contador y cambiar vista
        self.a_count_lbl.setText(f"Se encontraron {found_count} alumnos")
        self.a_stack.setCurrentIndex(0 if found_count > 0 else 1)
   # =================================================================
    # VENTANA 4: TALLERES (CON VISOR NATIVO QPfdView)
    # =================================================================
    def init_talleres(self):
        page = QWidget(); ly = QVBoxLayout(page); ly.setContentsMargins(20, 20, 20, 20)
        ly.addWidget(QLabel("<b style='font-size: 24px; color: #1e293b;'>Gestión de Talleres y Verificación</b>"))
        ly.addWidget(self.create_line())

        main_hly = QHBoxLayout()
        
        # --- COLUMNA 1: TABLA (IZQUIERDA) ---
        table_container = QVBoxLayout()
        self.t_search_input = QLineEdit()
        self.t_search_input.setPlaceholderText("🔍 Buscar por matrícula o nombre...")
        # Esta conexión causaba tu error, ahora la función existe abajo
        self.t_search_input.textChanged.connect(self.refresh_t_table_general)
        
        self.t_table_gen = QTableWidget(0, 3)
        self.t_table_gen.setHorizontalHeaderLabels(["MATRÍCULA", "ALUMNO", "CRÉDITOS"])
        self.t_table_gen.verticalHeader().setVisible(False)
        self.t_table_gen.setSelectionBehavior(QTableWidget.SelectRows)
        self.t_table_gen.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.t_table_gen.itemSelectionChanged.connect(self.show_student_details)
        
        table_container.addWidget(self.t_search_input); table_container.addWidget(self.t_table_gen)
        main_hly.addLayout(table_container, 2) 

        # --- COLUMNA 2: EXPEDIENTE DETALLADO (CENTRO) ---
        self.detail_card = QFrame(); self.detail_card.setFixedWidth(280)
        self.detail_card.setStyleSheet("background: white; border-radius: 8px; border: 1px solid #e2e8f0;")
        self.dl = QVBoxLayout(self.detail_card)
        
        self.det_title = QLabel("<b>EXPEDIENTE</b>")
        self.det_info = QLabel("Seleccione un alumno para gestionar su información.")
        self.det_info.setWordWrap(True)
        self.det_info.setAlignment(Qt.AlignTop)
        
        self.btn_select_file = QPushButton("📁 Seleccionar Constancia")
        self.btn_select_file.setEnabled(False)
        self.btn_select_file.setStyleSheet("background: #3b82f6; color: white; font-weight: bold; padding: 10px; border-radius: 5px;")
        self.btn_select_file.clicked.connect(self.handle_upload_pdf)
        
        self.dl.addWidget(self.det_title); self.dl.addWidget(self.create_line())
        self.dl.addWidget(self.det_info); self.dl.addStretch(); self.dl.addWidget(self.btn_select_file)
        main_hly.addWidget(self.detail_card)

        # --- COLUMNA 3: VISOR NATIVO (DERECHA - EL RECUADRO GRIS) ---
        self.preview_container = QFrame()
        self.preview_container.setMinimumWidth(450)
        self.preview_container.setStyleSheet("background: #475569; border-radius: 12px; border: 2px dashed #94a3b8;")
        pv_ly = QVBoxLayout(self.preview_container)
        
        # Componente de visualización nativo de PySide6
        self.pdf_view = QPdfView()
        self.pdf_document = QPdfDocument(self)
        self.pdf_view.setDocument(self.pdf_document)
        self.pdf_view.setZoomMode(QPdfView.ZoomMode.FitToWidth)
        self.pdf_view.setPageMode(QPdfView.PageMode.MultiPage)
        
        pv_ly.addWidget(self.pdf_view)
        
        # Botón verde de validación
        self.btn_aprobar = QPushButton("✅ Es Correcto - Guardar")
        self.btn_aprobar.setVisible(False)
        self.btn_aprobar.setStyleSheet("background: #10b981; color: white; font-weight: bold; padding: 12px; border-radius: 8px;")
        self.btn_aprobar.clicked.connect(self.confirm_save_doc)
        pv_ly.addWidget(self.btn_aprobar)
        
        main_hly.addWidget(self.preview_container, 3)
        ly.addLayout(main_hly)
        
        self.refresh_t_table_general()
        self.pages.insertWidget(3, page)

    def refresh_t_table_general(self):
        """Actualiza la tabla filtrando por el texto de búsqueda"""
        query = self.t_search_input.text().lower()
        self.t_table_gen.setRowCount(0)
        for s in self.engine.students:
            full_name = f"{s.get('apellidoPaterno','')} {s.get('nombres','')}".lower()
            if query in s['matricula'].lower() or query in full_name:
                r = self.t_table_gen.rowCount(); self.t_table_gen.insertRow(r)
                acc = len([w for w in s.get('workshops', []) if w.get('status') == 'Acreditado'])
                self.t_table_gen.setItem(r, 0, QTableWidgetItem(s['matricula']))
                self.t_table_gen.setItem(r, 1, QTableWidgetItem(full_name.upper()))
                self.t_table_gen.setItem(r, 2, QTableWidgetItem(f"{acc}/2"))

    def show_student_details(self):
        """Muestra el expediente completo al seleccionar una fila"""
        row = self.t_table_gen.currentRow()
        if row < 0: return
        mat = self.t_table_gen.item(row, 0).text()
        self.current_selected_student = next((s for s in self.engine.students if s['matricula'] == mat), None)
        
        if self.current_selected_student:
            s = self.current_selected_student
            acc = len([w for w in s.get('workshops', []) if w.get('status') == 'Acreditado'])
            info_html = f"""
                <div style='line-height: 140%;'>
                    <p><b>Matrícula:</b> {s['matricula']}</p>
                    <p><b>Género:</b> {s.get('genero', 'N/A')}</p>
                    <p><b>Teléfono:</b> {s.get('telefono', 'S/N')}</p>
                    <p><b>Carrera:</b><br>{s['career']}</p>
                    <p><b>Semestre:</b> {s.get('semestre', '1')}</p>
                    <p><b>Ciclo:</b> {s.get('schoolCycle', '2026-1')}</p>
                    <hr>
                    <p style='color: #2563eb;'><b>Créditos Totales: {acc}/2</b></p>
                </div>
            """
            self.det_info.setText(info_html)
            self.btn_select_file.setEnabled(True)

    def handle_upload_pdf(self):
        """Carga el PDF en el visor nativo y muestra el nombre del archivo"""
        path, _ = QFileDialog.getOpenFileName(self, "Seleccionar PDF", "", "Archivos PDF (*.pdf)")
        
        if path:
            self.temp_pdf_path = path
            import os
            # Extraer solo el nombre del archivo para mostrarlo al usuario
            nombre_archivo = os.path.basename(path)
            
            # Cargar el documento en el visor nativo
            self.pdf_document.load(path)
            
            # Actualizar el expediente con el nombre del archivo seleccionado
            info_actual = self.det_info.text()
            if "ARCHIVO SELECCIONADO:" not in info_actual:
                self.det_info.setText(info_actual + f"<br><br><b style='color: #059669;'>📂 ARCHIVO LISTO:</b><br>{nombre_archivo}")
            
            # Configurar el botón de confirmación
            self.btn_aprobar.setText(f"✅ Guardar {nombre_archivo}")
            self.btn_aprobar.setVisible(True)

    def confirm_save_doc(self):
        """Valida el documento y actualiza el contador de créditos en el sistema"""
        if not hasattr(self, 'current_selected_student') or not self.current_selected_student:
            return

        student = self.current_selected_student
        taller_acreditado = False
        
        # Buscar el taller activo para registrar el PDF y acreditarlo
        for ws in student.get('workshops', []):
            if ws['status'] == 'Cursando':
                ws['status'] = 'Acreditado'
                ws['pdf_path'] = self.temp_pdf_path
                taller_acreditado = True
                break
        
        if taller_acreditado:
            # Guardar cambios en el motor de datos (JSON)
            self.engine.save()
            QMessageBox.information(self, "Éxito", f"Constancia de {student['nombres']} guardada correctamente.")
            
            # Limpiar el visor y el botón de validación
            self.btn_aprobar.setVisible(False)
            self.btn_aprobar.setText("✅ Es Correcto - Guardar")
            
            # Refrescar la tabla y el expediente para mostrar el nuevo crédito (ej. 1/2)
            self.refresh_t_table_general()
            self.show_student_details()
        else:
            QMessageBox.warning(self, "Aviso", "El alumno no tiene talleres en curso para acreditar.")
    # =================================================================
    # VENTANA 5: DOCUMENTOS (GENERACIÓN DE CERTIFICADO)
    # =================================================================
    def init_documentos(self):
        page = QWidget(); ly = QVBoxLayout(page); ly.setContentsMargins(30, 30, 30, 30)
        ly.addWidget(QLabel("<b style='font-size: 24px;'>Certificación de Actividades</b>"))
        ly.addWidget(self.create_line())
        self.doc_stats_ly = QHBoxLayout(); ly.addLayout(self.doc_stats_ly)
        self.d_table = QTableWidget(0, 5); self.d_table.setHorizontalHeaderLabels(["MATRÍCULA", "NOMBRE", "CARRERA", "CRÉDITOS", "ACCIONES"])
        self.d_table.verticalHeader().setVisible(False); self.d_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        ly.addWidget(self.d_table); self.pages.insertWidget(4, page)

    def refresh_docs_table(self):
        stats = self.engine.get_stats()
        for i in reversed(range(self.doc_stats_ly.count())): self.doc_stats_ly.itemAt(i).widget().setParent(None)
        self.doc_stats_ly.addWidget(StatCard("Alumnos en Sistema", stats['total'], "", "white", "👥"))
        self.doc_stats_ly.addWidget(StatCard("Listos para Certificar", stats['ready'], "Cumplen 2/2", "#f0fdf4", "📜"))
        
        self.d_table.setRowCount(0)
        for s in self.engine.students:
            acc = len([w for w in s['workshops'] if w['status'] == 'Acreditado'])
            if acc >= 2: # SOLO SE MUESTRAN LOS QUE TIENEN 2 CURSOS
                r = self.d_table.rowCount(); self.d_table.insertRow(r)
                self.d_table.setItem(r, 0, QTableWidgetItem(s['matricula']))
                self.d_table.setItem(r, 1, QTableWidgetItem(s['nombres'].upper()))
                self.d_table.setItem(r, 2, QTableWidgetItem(s['career']))
                self.d_table.setItem(r, 3, QTableWidgetItem("✅ 2/2"))
                btn_print = QPushButton("🖨️ Generar Certificado")
                btn_print.setStyleSheet("background: #0f172a; color: white; padding: 5px; border-radius: 4px;")
                btn_print.clicked.connect(lambda _, x=s: QMessageBox.information(self, "Éxito", f"Imprimiendo Certificado Final de {x['nombres']}"))
                self.d_table.setCellWidget(r, 4, btn_print)
    # =================================================================
    # VENTANA 5: DOCUMENTOS (VISUALIZACIÓN DE ARCHIVOS GUARDADOS)
    # =================================================================
    def init_documentos(self):
        page = QWidget(); ly = QVBoxLayout(page); ly.setContentsMargins(20, 20, 20, 20)
        ly.addWidget(QLabel("<b style='font-size: 24px; color: #1e293b;'>Expediente de Documentos Acreditados</b>"))
        ly.addWidget(self.create_line())

        main_hly = QHBoxLayout()

        # --- COLUMNA 1: LISTA DE ALUMNOS CON DOCUMENTOS ---
        left_panel = QVBoxLayout()
        self.d_table = QTableWidget(0, 3)
        self.d_table.setHorizontalHeaderLabels(["MATRÍCULA", "ALUMNO", "DOCS"])
        self.d_table.verticalHeader().setVisible(False)
        self.d_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.d_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.d_table.itemSelectionChanged.connect(self.show_saved_documents)
        left_panel.addWidget(self.d_table)
        main_hly.addLayout(left_panel, 2)

        # --- COLUMNA 2: LISTA DE ARCHIVOS DEL ALUMNO ---
        self.files_card = QFrame(); self.files_card.setFixedWidth(250)
        self.files_card.setStyleSheet("background: white; border-radius: 8px; border: 1px solid #e2e8f0;")
        self.fl = QVBoxLayout(self.files_card)
        self.fl.addWidget(QLabel("<b>ARCHIVOS DISPONIBLES</b>"))
        self.files_list_widget = QListWidget() # Lista para mostrar los PDFs guardados
        self.files_list_widget.itemClicked.connect(self.load_pdf_to_view)
        self.fl.addWidget(self.files_list_widget)
        
        # Botón para generar el certificado final (solo si tiene 2/2)
        self.btn_print_final = QPushButton("🖨️ Certificado Final")
        self.btn_print_final.setEnabled(False)
        self.btn_print_final.setStyleSheet("background: #0f172a; color: white; padding: 10px;")
        self.fl.addWidget(self.btn_print_final)
        
        main_hly.addWidget(self.files_card)

        # --- COLUMNA 3: VISOR NATIVO REUTILIZADO ---
        self.doc_preview_container = QFrame()
        self.doc_preview_container.setMinimumWidth(400)
        self.doc_preview_container.setStyleSheet("background: #475569; border-radius: 12px;")
        dp_ly = QVBoxLayout(self.doc_preview_container)
        
        self.doc_pdf_view = QPdfView()
        self.doc_pdf_document = QPdfDocument(self)
        self.doc_pdf_view.setDocument(self.doc_pdf_document)
        self.doc_pdf_view.setZoomMode(QPdfView.ZoomMode.FitToWidth)
        
        dp_ly.addWidget(self.doc_pdf_view)
        main_hly.addWidget(self.doc_preview_container, 3)

        ly.addLayout(main_hly)
        self.pages.insertWidget(4, page)

    def refresh_docs_table(self):
        """Llena la tabla con personas que tienen al menos 1 documento subido"""
        self.d_table.setRowCount(0)
        for s in self.engine.students:
            # Filtramos solo los que tienen archivos guardados
            docs_acreditados = [w for w in s.get('workshops', []) if w.get('status') == 'Acreditado' and 'pdf_path' in w]
            
            if len(docs_acreditados) > 0:
                r = self.d_table.rowCount(); self.d_table.insertRow(r)
                self.d_table.setItem(r, 0, QTableWidgetItem(s['matricula']))
                self.d_table.setItem(r, 1, QTableWidgetItem(f"{s.get('nombres', '')} {s.get('apellidoPaterno', '')}".upper()))
                self.d_table.setItem(r, 2, QTableWidgetItem(f"{len(docs_acreditados)}/2"))

    def show_saved_documents(self):
        """Al seleccionar un alumno, lista sus archivos PDF en la columna central"""
        self.files_list_widget.clear()
        row = self.d_table.currentRow()
        if row < 0: return
        
        mat = self.d_table.item(row, 0).text()
        student = next((s for s in self.engine.students if s['matricula'] == mat), None)
        
        if student:
            docs = [w for w in student.get('workshops', []) if w.get('status') == 'Acreditado' and 'pdf_path' in w]
            for d in docs:
                item = QListWidgetItem(f"📄 {d['name']}")
                item.setData(Qt.UserRole, d['pdf_path']) # Guardamos la ruta oculta en el item
                self.files_list_widget.addItem(item)
            
            # Habilitar botón de certificado si ya tiene los 2 créditos
            self.btn_print_final.setEnabled(len(docs) >= 2)

    def load_pdf_to_view(self, item):
        """Carga el PDF seleccionado de la lista en el visor nativo"""
        pdf_path = item.data(Qt.UserRole)
        if pdf_path and os.path.exists(pdf_path):
            self.doc_pdf_document.load(pdf_path)
        else:
            QMessageBox.warning(self, "Error", "No se encuentra el archivo físico en la ruta guardada.")
if __name__ == "__main__":
    app = QApplication(sys.argv); window = TeschApp(); window.show(); sys.exit(app.exec())