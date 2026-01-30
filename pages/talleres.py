import sys
import os
import shutil
import webbrowser
from datetime import datetime
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QListWidget, QListWidgetItem, QFrame, QFileDialog, QMessageBox, 
    QTableWidget, QHeaderView, QTableWidgetItem, QAbstractItemView,
    QComboBox, QProgressBar, QRadioButton, QButtonGroup, QStackedWidget
)
from PySide6.QtCore import Qt, QUrl, QSize
from PySide6.QtGui import QColor, QBrush, QIcon, QFont

# --- IMPORTAMOS MÓDULOS PDF ---
try:
    from PySide6.QtPdf import QPdfDocument
    from PySide6.QtPdfWidgets import QPdfView
except ImportError:
    class QPdfDocument(QWidget): 
        def load(self, p): pass
        def close(self): pass
    class QPdfView(QWidget): 
        class ZoomMode: FitToWidth = 0
        def setDocument(self, d): pass
        def setPageMode(self, m): pass
        def setZoomMode(self, m): pass

class TalleresPage(QWidget):
    def __init__(self, engine):
        super().__init__()
        self.engine = engine
        self.current_student = None
        self.temp_pdf_path = None
        
        # Estilos modernos
        self.setStyleSheet("""
            QWidget { background-color: #f8fafc; font-family: 'Segoe UI'; font-size: 14px; }
            QFrame#Panel { background: white; border-radius: 12px; border: 1px solid #e2e8f0; }
            QLineEdit { background: #f1f5f9; border: 1px solid #cbd5e1; padding: 10px; border-radius: 8px; }
            QLineEdit:focus { border: 2px solid #3b82f6; background: white; }
            QListWidget { border: none; background: transparent; }
            QListWidget::item { padding: 12px; border-bottom: 1px solid #f1f5f9; color: #334155; margin-bottom: 4px; border-radius: 6px;}
            QListWidget::item:selected { background: #eff6ff; color: #1e40af; border-left: 4px solid #3b82f6; }
            QListWidget::item:hover { background: #f8fafc; }
            QRadioButton { spacing: 8px; color: #475569; }
        """)
        
        self.setup_ui()
        self.refresh_student_list()

    def setup_ui(self):
        main_ly = QVBoxLayout(self)
        main_ly.setContentsMargins(20, 20, 20, 20)
        
        # HEADER
        header = QHBoxLayout()
        title = QLabel("Gestión de Créditos Complementarios")
        title.setStyleSheet("font-size: 24px; font-weight: 800; color: #1e293b;")
        header.addWidget(title)
        header.addStretch()
        main_ly.addLayout(header)
        main_ly.addSpacing(15)

        # 3 COLUMNAS
        h_layout = QHBoxLayout()
        h_layout.setSpacing(20)
        
        # --- COL 1: LISTA (PENDIENTES) ---
        col1 = QFrame(); col1.setObjectName("Panel"); col1.setFixedWidth(320)
        c1_ly = QVBoxLayout(col1); c1_ly.setContentsMargins(15, 20, 15, 20)
        
        c1_ly.addWidget(QLabel("<b>🔍 Alumnos Pendientes (&lt; 5 Créditos)</b>"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar matrícula o nombre...")
        self.search_input.textChanged.connect(self.refresh_student_list)
        c1_ly.addWidget(self.search_input)
        
        self.student_list = QListWidget()
        self.student_list.itemClicked.connect(self.load_student_details)
        c1_ly.addWidget(self.student_list)
        
        h_layout.addWidget(col1)

        # --- COL 2: FORMULARIO ---
        self.center_stack = QStackedWidget()
        
        # Vista Vacía
        self.empty_view = QFrame(); self.empty_view.setObjectName("Panel")
        ev_ly = QVBoxLayout(self.empty_view); ev_ly.setAlignment(Qt.AlignCenter)
        lbl_inst = QLabel("Selecciona un alumno\npara gestionar sus créditos")
        lbl_inst.setAlignment(Qt.AlignCenter)
        lbl_inst.setStyleSheet("font-size: 18px; color: #94a3b8; font-weight: bold;")
        ev_ly.addWidget(lbl_inst)
        
        # Vista Formulario
        self.form_view = QFrame(); self.form_view.setObjectName("Panel"); self.form_view.setFixedWidth(380)
        c2_ly = QVBoxLayout(self.form_view); c2_ly.setContentsMargins(25, 25, 25, 25); c2_ly.setSpacing(15)
        
        self.lbl_student_name = QLabel("Nombre"); self.lbl_student_name.setStyleSheet("font-size: 18px; font-weight: bold; color: #1e293b;")
        self.lbl_student_mat = QLabel("Matrícula"); self.lbl_student_mat.setStyleSheet("color: #64748b;")
        c2_ly.addWidget(self.lbl_student_name); c2_ly.addWidget(self.lbl_student_mat)
        
        c2_ly.addWidget(QLabel("Progreso:"))
        self.prog_bar = QProgressBar(); self.prog_bar.setRange(0, 50); self.prog_bar.setFixedHeight(20)
        self.prog_bar.setStyleSheet("QProgressBar { border: none; background: #e2e8f0; border-radius: 10px; text-align: center; } QProgressBar::chunk { border-radius: 10px; }")
        c2_ly.addWidget(self.prog_bar)
        
        line = QFrame(); line.setFrameShape(QFrame.HLine); line.setStyleSheet("color:#e2e8f0;"); c2_ly.addWidget(line)
        
        c2_ly.addWidget(QLabel("<b>Nueva Actividad:</b>"))
        self.txt_act_name = QLineEdit(); self.txt_act_name.setPlaceholderText("Nombre del Taller / Actividad...")
        c2_ly.addWidget(self.txt_act_name)
        
        # Opciones de Valor
        self.rb_full = QRadioButton("Crédito Completo (1.0)"); self.rb_full.setChecked(True)
        self.rb_half = QRadioButton("Constancia / Participación (0.5)")
        bg = QButtonGroup(self); bg.addButton(self.rb_full); bg.addButton(self.rb_half)
        c2_ly.addWidget(self.rb_full); c2_ly.addWidget(self.rb_half)
        
        self.combo_cat = QComboBox(); self.combo_cat.addItems(["Cultural", "Deportivo", "Académico", "Otro"]); self.combo_cat.setStyleSheet("background: white; padding: 5px;")
        c2_ly.addWidget(self.combo_cat)
        
        c2_ly.addSpacing(10)
        self.btn_upload = QPushButton("  📂 Seleccionar PDF  "); self.btn_upload.setCursor(Qt.PointingHandCursor)
        self.btn_upload.setStyleSheet("QPushButton { background-color: #f1f5f9; color: #334155; border: 2px dashed #cbd5e1; border-radius: 10px; padding: 15px; font-weight: bold; } QPushButton:hover { background-color: #e2e8f0; border: 2px dashed #3b82f6; }")
        self.btn_upload.clicked.connect(self.select_pdf)
        c2_ly.addWidget(self.btn_upload)
        
        c2_ly.addStretch()
        c2_ly.addWidget(QLabel("<small>Historial:</small>"))
        self.history_list = QListWidget(); self.history_list.setFixedHeight(100); self.history_list.setStyleSheet("background: #f8fafc; border: 1px solid #e2e8f0; font-size: 12px;")
        c2_ly.addWidget(self.history_list)
        
        self.center_stack.addWidget(self.empty_view); self.center_stack.addWidget(self.form_view)
        h_layout.addWidget(self.center_stack)

        # --- COL 3: VISOR ---
        col3 = QFrame(); col3.setObjectName("Panel"); col3.setStyleSheet("QFrame#Panel { background: #334155; border: none; }")
        c3_ly = QVBoxLayout(col3)
        
        self.pdf_viewer = QPdfView()
        self.pdf_document = QPdfDocument(self)
        self.pdf_viewer.setDocument(self.pdf_document)
        self.pdf_viewer.setPageMode(QPdfView.PageMode.MultiPage)
        self.pdf_viewer.setZoomMode(QPdfView.ZoomMode.FitToWidth)
        self.pdf_viewer.setStyleSheet("border: none; background: #475569;")
        c3_ly.addWidget(self.pdf_viewer)
        
        self.btn_save = QPushButton("✅ GUARDAR Y SUMAR"); self.btn_save.setVisible(False); self.btn_save.setCursor(Qt.PointingHandCursor)
        self.btn_save.setStyleSheet("QPushButton { background: #10b981; color: white; padding: 15px; border-radius: 8px; font-weight: bold; font-size: 16px; border: none; } QPushButton:hover { background: #059669; }")
        self.btn_save.clicked.connect(self.save_credit)
        c3_ly.addWidget(self.btn_save)
        
        h_layout.addWidget(col3, stretch=1)
        main_ly.addLayout(h_layout)

    # --- LÓGICA CORREGIDA ---

    def refresh_student_list(self):
        """Muestra alumnos que tengan menos de 5.0 créditos"""
        search = self.search_input.text().lower().strip()
        self.student_list.clear()
        
        students = self.engine.students if hasattr(self.engine, 'students') else []
        if not students: return

        for s in students:
            # 1. Calcular Créditos ACUMULADOS
            workshops = s.get('workshops', [])
            total_creds = 0.0
            
            for w in workshops:
                # Sumamos si está acreditado
                if w.get('status') == 'Acreditado':
                    try:
                        total_creds += float(w.get('value', 1.0))
                    except:
                        total_creds += 1.0
            
            # --- FILTRO CLAVE: Si ya tiene 5.0 o más, NO LO MUESTRES AQUÍ ---
            # (Porque ya pasó al módulo de Constancias)
            if total_creds >= 5.0: continue

            # Filtro de búsqueda
            name = f"{s.get('nombres','')} {s.get('apellidoPaterno','')}".lower()
            mat = str(s.get('matricula','')).lower()
            if search and (search not in mat and search not in name): continue
            
            # Item de la lista
            item = QListWidgetItem(f"{s.get('matricula')} - {name.upper()}")
            item.setData(Qt.UserRole, s)
            
            # Mostrar avance en la lista
            if total_creds > 0:
                item.setText(f"{item.text()} ({total_creds}/5.0)")
                item.setForeground(QBrush(QColor("#2563eb")))
                
            self.student_list.addItem(item)

    def load_student_details(self, item):
        # Limpiar para evitar errores de memoria
        if self.pdf_document: self.pdf_document.close()
        self.current_student = None
        self.btn_save.setVisible(False)
        self.txt_act_name.clear()
        self.history_list.clear()
        QApplication.processEvents() 
        
        # Cargar nuevo
        self.current_student = item.data(Qt.UserRole)
        self.center_stack.setCurrentIndex(1)
        
        s = self.current_student
        self.lbl_student_name.setText(f"{s.get('nombres')} {s.get('apellidoPaterno')}")
        self.lbl_student_mat.setText(f"Matrícula: {s.get('matricula')} | {s.get('career')}")
        self.update_progress_visuals()

    def update_progress_visuals(self):
        workshops = self.current_student.get('workshops', [])
        total = 0.0
        self.history_list.clear()
        
        for w in workshops:
            if w.get('status') == 'Acreditado':
                val = float(w.get('value', 1.0))
                total += val
                self.history_list.addItem(f"✅ {w.get('name')} ({val})")
        
        self.prog_bar.setValue(int(total * 10))
        color = "#ef4444" if total < 3.0 else "#f59e0b"
        self.prog_bar.setStyleSheet(f"QProgressBar {{ border: none; background: #e2e8f0; border-radius: 10px; text-align: center; color: black; font-weight: bold; }} QProgressBar::chunk {{ background-color: {color}; border-radius: 10px; }}")
        self.prog_bar.setFormat(f"{total} / 5.0 Créditos")

    def select_pdf(self):
        name = self.txt_act_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Nombre Requerido", "Primero escribe el nombre de la actividad.")
            return

        path, _ = QFileDialog.getOpenFileName(self, "Seleccionar PDF", "", "PDF (*.pdf)")
        if path:
            self.temp_pdf_path = path
            
            # Cerrar anterior antes de abrir nuevo
            self.pdf_document.close()
            try:
                self.pdf_document.load(path)
                self.btn_save.setVisible(True)
                self.btn_save.setText(f"GUARDAR: {name.upper()}")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"No se pudo cargar el visor.\n{e}")

    def save_credit(self):
        if not self.current_student or not self.temp_pdf_path: return
        
        try:
            # 1. Copiar archivo
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            ev_dir = os.path.join(base_dir, "Evidencias_Creditos")
            if not os.path.exists(ev_dir): os.makedirs(ev_dir)
            
            mat = self.current_student['matricula']
            ts = datetime.now().strftime('%Y%m%d%H%M%S')
            dest_path = os.path.join(ev_dir, f"{mat}_{ts}.pdf")
            
            # Liberar PDF antes de copiar
            self.pdf_document.close()
            QApplication.processEvents()
            
            shutil.copy(self.temp_pdf_path, dest_path)
            
            # 2. Guardar datos
            val = 1.0 if self.rb_full.isChecked() else 0.5
            new_credit = {
                "name": self.txt_act_name.text().strip().upper(),
                "category": self.combo_cat.currentText(),
                "value": val,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "status": "Acreditado",
                "pdf_path": dest_path
            }
            
            if 'workshops' not in self.current_student: 
                self.current_student['workshops'] = []
                
            self.current_student['workshops'].append(new_credit)
            self.engine.save()
            
            # 3. VERIFICAR META DE 5 CRÉDITOS
            new_total = sum(float(w.get('value', 1.0)) for w in self.current_student['workshops'] if w.get('status') == 'Acreditado')
            
            if new_total >= 5.0:
                QMessageBox.information(self, "¡META ALCANZADA! 🎓", 
                    f"El alumno {self.current_student['nombres']} completó los 5.0 créditos.\n\n"
                    "Desaparecerá de esta lista y ya está disponible en el módulo de CONSTANCIAS.")
                
                # Regresar a inicio y recargar lista (el alumno desaparecerá)
                self.center_stack.setCurrentIndex(0)
                self.current_student = None
                self.refresh_student_list()
            else:
                QMessageBox.information(self, "Guardado", "Actividad registrada correctamente.")
                self.txt_act_name.clear()
                self.btn_save.setVisible(False)
                self.update_progress_visuals()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al guardar: {e}")