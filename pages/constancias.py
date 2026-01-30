import os
import sys
import subprocess # Para abrir PDF sin bloquear Word
import locale
from datetime import datetime

# Configuración regional para fechas en español
try:
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_TIME, 'Spanish')
    except:
        pass

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QListWidget, QListWidgetItem, QFrame, QLineEdit, 
    QDialog, QFormLayout, QDialogButtonBox, QMessageBox, QWidget
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor, QIcon, QFont, QPixmap

# Librerías Word/PDF
try:
    from docxtpl import DocxTemplate
    from docx2pdf import convert
except ImportError:
    pass

# --- DIÁLOGO DE VERIFICACIÓN (DISEÑO LIMPIO) ---
class VerificarDatosDialog(QDialog):
    def __init__(self, student_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Confirmar Datos del Documento")
        self.setFixedSize(500, 450)
        
        # Estilos CSS
        self.setStyleSheet("""
            QDialog { background-color: white; }
            QLabel { color: #1e293b; font-size: 14px; font-family: 'Segoe UI'; }
            QLineEdit { 
                background-color: #f8fafc; border: 1px solid #cbd5e1; 
                border-radius: 6px; padding: 10px; font-size: 14px; 
                color: #0f172a; font-weight: bold;
            }
            QLineEdit:focus { border: 2px solid #3b82f6; background-color: white; }
            QPushButton { padding: 10px 20px; border-radius: 6px; font-weight: bold; font-size: 14px; }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Título
        title = QLabel("📝 Revisión Final")
        title.setStyleSheet("font-size: 20px; font-weight: 800; color: #0f172a;")
        layout.addWidget(title)
        
        sub = QLabel("Estos datos se imprimirán en la constancia oficial.\nVerifícalos antes de continuar.")
        sub.setStyleSheet("color: #64748b; margin-bottom: 15px;")
        layout.addWidget(sub)

        # Formulario
        form = QFormLayout()
        form.setSpacing(15)
        
        self.nombre_edit = QLineEdit(student_data.get('nombre', ''))
        self.matricula_edit = QLineEdit(student_data.get('matricula', ''))
        self.carrera_edit = QLineEdit(student_data.get('carrera', ''))
        
        now = datetime.now()
        self.dia_edit = QLineEdit(str(now.day))
        self.mes_edit = QLineEdit(now.strftime("%B").upper())
        self.anio_edit = QLineEdit(str(now.year))

        form.addRow("🎓 Alumno:", self.nombre_edit)
        form.addRow("🆔 Matrícula:", self.matricula_edit)
        form.addRow("🏫 Carrera:", self.carrera_edit)
        
        sep = QFrame(); sep.setFrameShape(QFrame.HLine); sep.setStyleSheet("color: #e2e8f0; margin: 10px 0;")
        form.addRow(sep)
        
        form.addRow("📅 Día:", self.dia_edit)
        form.addRow("📅 Mes:", self.mes_edit)
        form.addRow("📅 Año:", self.anio_edit)

        layout.addLayout(form)
        layout.addStretch()

        # Botones
        btns_ly = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setCursor(Qt.PointingHandCursor)
        btn_cancel.setStyleSheet("background: white; border: 1px solid #cbd5e1; color: #64748b;")
        btn_cancel.clicked.connect(self.reject)
        
        btn_ok = QPushButton("✅ IMPRIMIR CONSTANCIA")
        btn_ok.setCursor(Qt.PointingHandCursor)
        btn_ok.setStyleSheet("background: #2563eb; color: white; border: none;")
        btn_ok.clicked.connect(self.accept)
        
        btns_ly.addWidget(btn_cancel)
        btns_ly.addWidget(btn_ok)
        layout.addLayout(btns_ly)

    def get_data(self):
        return {
            'NOMBRE_ESTUDIANTE': self.nombre_edit.text().upper(),
            'MATRICULA': self.matricula_edit.text().upper(),
            'CARRERA': self.carrera_edit.text().upper(),
            'DIA': self.dia_edit.text(),
            'MES': self.mes_edit.text().upper(),
            'ANIO': self.anio_edit.text()
        }

# --- PÁGINA PRINCIPAL CONSTANCIAS ---
class ConstanciaPage(QWidget):
    def __init__(self, engine):
        super().__init__()
        self.engine = engine
        self.current_student = None
        
        # Estilos Globales para esta página
        self.setStyleSheet("""
            QWidget { background-color: #f1f5f9; font-family: 'Segoe UI'; }
            
            /* Paneles */
            QFrame#Panel { background: white; border-radius: 12px; border: 1px solid #e2e8f0; }
            
            /* Lista */
            QListWidget { border: none; background: transparent; }
            QListWidget::item { 
                background: white; 
                margin-bottom: 8px; 
                padding: 15px; 
                border-radius: 8px; 
                border: 1px solid #e2e8f0; 
                color: #334155;
            }
            QListWidget::item:selected { 
                background: #eff6ff; 
                border: 1px solid #3b82f6; 
                color: #1e40af; 
            }
            QListWidget::item:hover { border: 1px solid #94a3b8; }
            
            /* Inputs */
            QLineEdit { background: white; border: 1px solid #cbd5e1; padding: 10px; border-radius: 8px; font-size: 14px; }
        """)
        
        self.setup_ui()
        self.refresh_list()

    def create_line(self):
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #e2e8f0; max-height: 1px; border: none; margin: 10px 0;")
        return line

    def setup_ui(self):
        main_ly = QVBoxLayout(self)
        main_ly.setContentsMargins(30, 30, 30, 30)
        
        # HEADER
        header = QHBoxLayout()
        icon = QLabel("🖨️"); icon.setStyleSheet("font-size: 32px;")
        
        title_ly = QVBoxLayout()
        lbl_t = QLabel("Emisión de Constancias")
        lbl_t.setStyleSheet("font-size: 26px; font-weight: 800; color: #1e293b;")
        lbl_s = QLabel("Generación de documentos oficiales para alumnos acreditados (5.0 Créditos)")
        lbl_s.setStyleSheet("color: #64748b; font-size: 14px;")
        title_ly.addWidget(lbl_t); title_ly.addWidget(lbl_s)
        
        header.addWidget(icon); header.addLayout(title_ly); header.addStretch()
        main_ly.addLayout(header)
        main_ly.addWidget(self.create_line())

        # CONTENIDO (2 COLUMNAS)
        content_ly = QHBoxLayout()
        content_ly.setSpacing(20)

        # --- IZQUIERDA: LISTA DE ALUMNOS LISTOS ---
        left_panel = QFrame(); left_panel.setObjectName("Panel")
        left_panel.setFixedWidth(380)
        lp_ly = QVBoxLayout(left_panel)
        lp_ly.setContentsMargins(20, 20, 20, 20)
        
        lp_ly.addWidget(QLabel("<b>✅ Alumnos Acreditados (Listos)</b>"))
        
        # Buscador
        self.search = QLineEdit()
        self.search.setPlaceholderText("🔍 Buscar por matrícula...")
        self.search.textChanged.connect(self.refresh_list)
        lp_ly.addWidget(self.search)
        
        # Lista
        self.list_widget = QListWidget()
        self.list_widget.itemClicked.connect(self.select_student)
        lp_ly.addWidget(self.list_widget)
        
        # Mensaje vacío
        self.lbl_empty = QLabel("🚫 No hay alumnos listos para liberar.\nRevisar módulo Talleres.")
        self.lbl_empty.setAlignment(Qt.AlignCenter)
        self.lbl_empty.setStyleSheet("color: #94a3b8; margin-top: 20px; font-weight: bold;")
        self.lbl_empty.setVisible(False)
        lp_ly.addWidget(self.lbl_empty)
        
        content_ly.addWidget(left_panel)

        # --- DERECHA: TARJETA DE ACCIÓN ---
        right_panel = QFrame(); right_panel.setObjectName("Panel")
        self.rp_ly = QVBoxLayout(right_panel)
        self.rp_ly.setAlignment(Qt.AlignCenter)
        self.rp_ly.setContentsMargins(40, 40, 40, 40)
        
        # Estado Inicial (Nada seleccionado)
        self.lbl_placeholder = QLabel("👈 Selecciona un alumno de la lista")
        self.lbl_placeholder.setStyleSheet("font-size: 20px; color: #cbd5e1; font-weight: bold;")
        self.rp_ly.addWidget(self.lbl_placeholder)
        
        # Contenedor de Detalles (Oculto al inicio)
        self.details_container = QWidget()
        self.details_container.setVisible(False)
        dc_ly = QVBoxLayout(self.details_container)
        dc_ly.setAlignment(Qt.AlignCenter)
        dc_ly.setSpacing(15)
        
        # Icono gigante
        lbl_big_icon = QLabel("🎓"); lbl_big_icon.setStyleSheet("font-size: 80px;")
        lbl_big_icon.setAlignment(Qt.AlignCenter)
        dc_ly.addWidget(lbl_big_icon)
        
        self.lbl_name = QLabel("NOMBRE DEL ALUMNO")
        self.lbl_name.setAlignment(Qt.AlignCenter)
        self.lbl_name.setStyleSheet("font-size: 24px; font-weight: 800; color: #1e293b;")
        self.lbl_name.setWordWrap(True)
        dc_ly.addWidget(self.lbl_name)
        
        self.lbl_career = QLabel("INGENIERÍA EN SISTEMAS")
        self.lbl_career.setAlignment(Qt.AlignCenter)
        self.lbl_career.setStyleSheet("font-size: 16px; color: #64748b; font-weight: bold;")
        dc_ly.addWidget(self.lbl_career)
        
        self.lbl_status = QLabel("✅ 5.0 Créditos Cubiertos")
        self.lbl_status.setStyleSheet("color: #16a34a; font-weight: bold; background: #dcfce7; padding: 5px 10px; border-radius: 15px;")
        dc_ly.addWidget(self.lbl_status, alignment=Qt.AlignCenter)
        
        dc_ly.addSpacing(30)
        
        # Botón Gigante
        self.btn_generate = QPushButton("  GENERAR DOCUMENTO PDF  ")
        self.btn_generate.setCursor(Qt.PointingHandCursor)
        self.btn_generate.setStyleSheet("""
            QPushButton { 
                background-color: #16a34a; color: white; 
                padding: 20px; border-radius: 12px; 
                font-size: 16px; font-weight: 900; border: none;
            }
            QPushButton:hover { background-color: #15803d; transform: scale(1.05); }
        """)
        self.btn_generate.clicked.connect(self.click_generate)
        dc_ly.addWidget(self.btn_generate)
        
        self.rp_ly.addWidget(self.details_container)
        content_ly.addWidget(right_panel)

        main_ly.addLayout(content_ly)

    # --- LÓGICA ---

    def refresh_list(self):
        search = self.search.text().lower().strip()
        self.list_widget.clear()
        
        students = self.engine.students if hasattr(self.engine, 'students') else []
        count = 0
        
        for s in students:
            # 1. CALCULAR CRÉDITOS (Regla: >= 5.0)
            workshops = s.get('workshops', [])
            total = 0.0
            for w in workshops:
                if w.get('status') in ['Acreditado', 'Entregado']:
                    total += float(w.get('value', 1.0))
            
            if total < 5.0: continue
            
            # 2. FILTRO DE BÚSQUEDA
            name = f"{s.get('nombres')} {s.get('apellidoPaterno')}".lower()
            mat = str(s.get('matricula')).lower()
            
            if search and (search not in name and search not in mat): continue
            
            # Crear Item
            item = QListWidgetItem()
            item.setText(f"{s.get('nombres')} {s.get('apellidoPaterno')}\n{s.get('matricula')}")
            item.setData(Qt.UserRole, s)
            self.list_widget.addItem(item)
            count += 1
            
        self.lbl_empty.setVisible(count == 0)
        self.list_widget.setVisible(count > 0)
        
        # Resetear panel derecho
        self.lbl_placeholder.setVisible(True)
        self.details_container.setVisible(False)
        self.current_student = None

    def select_student(self, item):
        self.current_student = item.data(Qt.UserRole)
        s = self.current_student
        
        self.lbl_placeholder.setVisible(False)
        self.details_container.setVisible(True)
        
        self.lbl_name.setText(f"{s.get('nombres')} {s.get('apellidoPaterno')}".upper())
        self.lbl_career.setText(f"{s.get('matricula')}  |  {s.get('career')}")

    def click_generate(self):
        if not self.current_student: return
        
        name = f"{self.current_student.get('nombres','')} {self.current_student.get('apellidoPaterno','')} {self.current_student.get('apellidoMaterno','')}"
        data = {
            'nombre': name.upper(), 
            'matricula': self.current_student.get('matricula'), 
            'carrera': self.current_student.get('career')
        }
        
        d = VerificarDatosDialog(data, self)
        if d.exec():
            self.process_pdf(d.get_data())

    def process_pdf(self, ctx):
        # 1. Validar Rutas
        base = os.path.dirname(os.path.abspath(__file__))
        root = os.path.dirname(base)
        tpl = os.path.join(root, "plantilla_constancia.docx")
        
        if not os.path.exists(tpl):
            QMessageBox.critical(self, "Error", f"No encuentro la plantilla:\n{tpl}")
            return
            
        try:
            out_dir = os.path.join(root, "Constancias_Generadas")
            if not os.path.exists(out_dir): os.makedirs(out_dir)
            
            # 2. Generar Word
            doc = DocxTemplate(tpl)
            doc.render(ctx)
            
            # Timestamp en el nombre para evitar conflictos
            ts = datetime.now().strftime("%H%M%S")
            fname = f"Constancia_{ctx['MATRICULA']}_{ts}"
            docx = os.path.join(out_dir, f"{fname}.docx")
            pdf = os.path.join(out_dir, f"{fname}.pdf")
            
            doc.save(docx)
            
            # 3. Convertir a PDF
            QMessageBox.information(self, "Generando", "Creando PDF... Por favor espera un momento.")
            convert(docx, pdf)
            
            # 4. Guardar Historial
            self.current_student['workshops'].append({
                "name": "CONSTANCIA FINAL OFICIAL",
                "category": "Trámite",
                "value": 0,
                "status": "Entregado",
                "pdf_path": pdf,
                "date": datetime.now().strftime("%Y-%m-%d")
            })
            self.engine.save()
            
            # 5. Abrir en Navegador (Seguro)
            self.force_browser(pdf)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Ocurrió un error:\n{str(e)}\n\nCierra Word si está abierto.")

    def force_browser(self, path):
        """Intenta forzar la apertura en Chrome o Edge"""
        abs_path = os.path.abspath(path)
        try:
            subprocess.run(f'start chrome "{abs_path}"', shell=True)
        except:
            try:
                subprocess.run(f'start msedge "{abs_path}"', shell=True)
            except:
                os.startfile(abs_path)