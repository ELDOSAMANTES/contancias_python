import os
import sys
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QHBoxLayout, QComboBox, QPushButton, 
    QTableWidget, QHeaderView, QTableWidgetItem, QFrame, QAbstractItemView, 
    QStackedWidget, QDialog, QFileDialog, QScrollArea, QGridLayout, QMessageBox,
    QSizePolicy, QLineEdit
)
from PySide6.QtCore import Qt, QSize, QUrl, QRect
from PySide6.QtGui import QColor, QBrush, QPixmap, QIcon, QPainter, QPainterPath, QImage

# --- MÓDULOS DE PDF ---
try:
    from PySide6.QtPdf import QPdfDocument
    from PySide6.QtPdfWidgets import QPdfView
except ImportError:
    class QPdfDocument(QWidget): 
        def load(self, p): pass
    class QPdfView(QWidget): 
        class ZoomMode: FitToWidth = 0 
        def setDocument(self, d): pass
        def setPageMode(self, m): pass
        def setZoomMode(self, m): pass

# --- DIÁLOGO EXPEDIENTE (Igual que antes, con el visor y fotos redondas) ---
class StudentDetailDialog(QDialog):
    def __init__(self, student, engine, parent=None):
        super().__init__(parent)
        self.student = student
        self.engine = engine
        self.setWindowTitle(f"Expediente: {student.get('nombres', 'Alumno')}")
        self.setFixedSize(1150, 750)
        
        # Confiamos en los estilos globales de main.py, pero forzamos base blanca
        self.setStyleSheet("QDialog { background-color: #ffffff; }")
        
        self.setup_ui()

    def setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. PANEL IZQUIERDO
        left_panel = QWidget()
        left_panel.setFixedWidth(380)
        left_panel.setStyleSheet("background-color: white; border-right: 1px solid #e2e8f0;")
        
        left_ly = QVBoxLayout(left_panel)
        left_ly.setContentsMargins(20, 20, 20, 20)
        left_ly.setSpacing(15)

        # Foto y Datos
        profile_ly = QHBoxLayout()
        self.photo_lbl = QLabel()
        self.photo_lbl.setFixedSize(90, 90)
        self.load_photo()
        
        info_ly = QVBoxLayout()
        full_name = f"{self.student.get('nombres','')} {self.student.get('apellidoPaterno','')}"
        lbl_name = QLabel(full_name.upper())
        lbl_name.setStyleSheet("font-weight: bold; font-size: 14px; border: none;")
        lbl_name.setWordWrap(True)
        
        lbl_mat = QLabel(f"Mat: {self.student.get('matricula')}\n{self.student.get('career')}")
        lbl_mat.setStyleSheet("color: #64748b; font-size: 12px; border: none;")
        
        info_ly.addWidget(lbl_name); info_ly.addWidget(lbl_mat)
        profile_ly.addWidget(self.photo_lbl); profile_ly.addLayout(info_ly)
        left_ly.addLayout(profile_ly)
        
        btn_upload = QPushButton("📷 Cambiar Foto")
        btn_upload.setCursor(Qt.PointingHandCursor)
        btn_upload.setStyleSheet("background: #f1f5f9; color: #334155; border: 1px solid #cbd5e1;")
        btn_upload.clicked.connect(self.upload_photo)
        left_ly.addWidget(btn_upload)

        line = QFrame(); line.setFrameShape(QFrame.HLine); line.setStyleSheet("color: #e2e8f0;")
        left_ly.addWidget(line)

        # Documentos
        left_ly.addWidget(QLabel("<b>📄 Documentos Disponibles</b>"))
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")
        content_w = QWidget(); content_w.setStyleSheet("background: white;")
        self.docs_ly = QVBoxLayout(content_w)
        self.docs_ly.setSpacing(8)
        self.docs_ly.setContentsMargins(0,0,5,0)
        
        workshops = self.student.get('workshops', [])
        has_files = False
        
        for w in workshops:
            pdf_path = w.get('pdf_path')
            btn_doc = QPushButton()
            btn_doc.setCheckable(True)
            btn_doc.setCursor(Qt.PointingHandCursor)
            
            btn_doc.setStyleSheet("""
                QPushButton { background-color: #f8fafc; border: 1px solid #e2e8f0; text-align: left; padding: 10px; color: #1e293b; }
                QPushButton:checked { background-color: #eff6ff; border: 1px solid #3b82f6; }
                QPushButton:hover { background-color: #e2e8f0; }
            """)
            
            row = QHBoxLayout(btn_doc)
            st = w.get('status', '-')
            col = "#10b981" if st in ['Acreditado', 'Entregado'] else "#f59e0b"
            
            txt_ly = QVBoxLayout()
            t1 = QLabel(w.get('name', 'Actividad'))
            t1.setStyleSheet("font-weight: bold; border:none; background:transparent;")
            t2 = QLabel(st)
            t2.setStyleSheet(f"font-size: 11px; color: {col}; border:none; background:transparent;")
            txt_ly.addWidget(t1); txt_ly.addWidget(t2)
            
            row.addLayout(txt_ly); row.addStretch()
            
            if pdf_path and os.path.exists(pdf_path):
                row.addWidget(QLabel("👁️"))
                btn_doc.clicked.connect(lambda checked=False, b=btn_doc, p=pdf_path: self.preview_pdf(b, p))
                self.docs_ly.addWidget(btn_doc)
                has_files = True
            else:
                btn_doc.setEnabled(False)
                t2.setText("Sin archivo"); self.docs_ly.addWidget(btn_doc)

        if not has_files: self.docs_ly.addWidget(QLabel("No hay documentos."))
        self.docs_ly.addStretch(); scroll.setWidget(content_w); left_ly.addWidget(scroll)

        btn_close = QPushButton("Cerrar")
        btn_close.clicked.connect(self.accept)
        btn_close.setStyleSheet("background: #cbd5e1; color: #334155;")
        left_ly.addWidget(btn_close)

        # 2. PANEL DERECHO
        right_panel = QWidget()
        right_panel.setStyleSheet("background-color: #475569;")
        right_ly = QVBoxLayout(right_panel); right_ly.setContentsMargins(10, 10, 10, 10)
        
        self.pdf_document = QPdfDocument(self)
        self.pdf_viewer = QPdfView(self)
        self.pdf_viewer.setDocument(self.pdf_document)
        self.pdf_viewer.setPageMode(QPdfView.PageMode.MultiPage)
        self.pdf_viewer.setZoomMode(QPdfView.ZoomMode.FitToWidth)
        self.pdf_viewer.setStyleSheet("border: none;")
        
        self.right_stack = QStackedWidget()
        self.lbl_msg = QLabel("Selecciona un documento de la lista\npara visualizarlo aquí.")
        self.lbl_msg.setAlignment(Qt.AlignCenter)
        self.lbl_msg.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
        
        self.right_stack.addWidget(self.lbl_msg); self.right_stack.addWidget(self.pdf_viewer)
        right_ly.addWidget(self.right_stack)
        
        main_layout.addWidget(left_panel); main_layout.addWidget(right_panel)

    def set_rounded_image(self, path):
        if not os.path.exists(path): return
        src_img = QImage(path)
        if src_img.isNull(): return
        size = 90; target_size = QSize(size, size)
        scaled_img = src_img.scaled(target_size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        x = (scaled_img.width() - size) // 2; y = (scaled_img.height() - size) // 2
        cropped_img = scaled_img.copy(x, y, size, size)
        final_pixmap = QPixmap(target_size); final_pixmap.fill(Qt.transparent)
        painter = QPainter(final_pixmap); painter.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath(); path.addEllipse(0, 0, size, size); painter.setClipPath(path)
        painter.drawPixmap(0, 0, QPixmap.fromImage(cropped_img)); painter.end()
        self.photo_lbl.setPixmap(final_pixmap)
        self.photo_lbl.setStyleSheet("border: none; background: transparent;")

    def load_photo(self):
        path = self.student.get('photo_path')
        if path and os.path.exists(path): self.set_rounded_image(path)
        else:
            self.photo_lbl.setText("👤")
            self.photo_lbl.setStyleSheet("background-color: #f1f5f9; border-radius: 45px; border: 2px solid #e2e8f0; font-size: 40px; color: #cbd5e1;")
            self.photo_lbl.setAlignment(Qt.AlignCenter)

    def upload_photo(self):
        path, _ = QFileDialog.getOpenFileName(self, "Seleccionar Foto", "", "Imágenes (*.png *.jpg *.jpeg)")
        if path: self.student['photo_path'] = path; self.engine.save(); self.load_photo()

    def preview_pdf(self, btn_sender, path):
        for i in range(self.docs_ly.count()):
            w = self.docs_ly.itemAt(i).widget()
            if isinstance(w, QPushButton): w.setChecked(False)
        btn_sender.setChecked(True)
        try: self.pdf_document.load(path); self.right_stack.setCurrentIndex(1)
        except Exception as e: QMessageBox.warning(self, "Error", f"No se pudo cargar el PDF.\n{e}")

# --- PÁGINA EXPEDIENTE (AQUÍ ESTÁ LA NUEVA LÓGICA DE FILTROS) ---
class ExpedientePage(QWidget):
    def __init__(self, engine):
        super().__init__()
        self.engine = engine
        self.setStyleSheet("background-color: #f1f5f9;") 
        self.setup_ui()
        self.apply_filter()

    def create_line(self):
        line = QFrame(); line.setFrameShape(QFrame.HLine); line.setStyleSheet("background-color: #e2e8f0; max-height: 1px; border: none; margin: 10px 0;")
        return line

    def setup_ui(self):
        ly = QVBoxLayout(self); ly.setContentsMargins(30, 30, 30, 30); ly.setSpacing(15)

        h_ly = QHBoxLayout()
        icon_h = QLabel("📂"); icon_h.setFixedSize(45, 45); icon_h.setAlignment(Qt.AlignCenter); icon_h.setStyleSheet("background-color: white; border: 1px solid #e2e8f0; border-radius: 8px; font-size: 20px;")
        t_ly = QVBoxLayout(); t = QLabel("Expediente General"); t.setStyleSheet("font-size: 24px; font-weight: bold; color: #0f172a; border: none;"); s = QLabel("Consulta de documentos"); s.setStyleSheet("color: #64748b; border: none;")
        t_ly.addWidget(t); t_ly.addWidget(s)
        h_ly.addWidget(icon_h); h_ly.addLayout(t_ly); h_ly.addStretch(); ly.addLayout(h_ly); ly.addWidget(self.create_line())

        # --- TARJETA DE FILTROS (RENOVADA) ---
        f_card = QFrame(); f_card.setStyleSheet("QFrame { background: white; border-radius: 12px; border: 1px solid #e2e8f0; } QLabel { color: #64748b; font-weight: bold; border: none; }")
        card_ly = QVBoxLayout(f_card); card_ly.setContentsMargins(15, 15, 15, 15); card_ly.setSpacing(10)
        
        # FILA 1: Búsqueda por Texto
        row1 = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Buscar alumno por nombre o matrícula...")
        self.search_input.setStyleSheet("font-size: 14px; padding: 6px;")
        self.search_input.textChanged.connect(self.apply_filter) # Búsqueda en tiempo real
        row1.addWidget(self.search_input)
        
        # FILA 2: Filtros Desplegables
        row2 = QHBoxLayout()
        self.f_sem = QComboBox(); self.f_sem.addItems(["Todos los Semestres"] + [str(i) for i in range(1,10)])
        
        # Poblar Carreras dinámicamente
        self.f_career = QComboBox()
        self.f_career.addItem("Todas las Carreras")
        careers = sorted(list(set(s.get('career', '') for s in self.engine.students if s.get('career'))))
        self.f_career.addItems(careers)
        
        self.f_cyc = QComboBox(); self.f_cyc.addItems(["Todos los Ciclos", "2024-1", "2024-2", "2025-1", "2025-2", "2026-1"])
        
        btn_refresh = QPushButton("🔄 Actualizar")
        btn_refresh.setCursor(Qt.PointingHandCursor)
        btn_refresh.setStyleSheet("background-color: #3b82f6; color: white;")
        btn_refresh.clicked.connect(self.apply_filter)
        
        row2.addWidget(QLabel("Semestre:")); row2.addWidget(self.f_sem)
        row2.addWidget(QLabel("Carrera:")); row2.addWidget(self.f_career)
        row2.addWidget(QLabel("Ciclo:")); row2.addWidget(self.f_cyc)
        row2.addWidget(btn_refresh)
        
        card_ly.addLayout(row1)
        card_ly.addLayout(row2)
        ly.addWidget(f_card)

        # Tabla
        self.stack = QStackedWidget(); self.stack.setStyleSheet("background: transparent;")
        self.table = QTableWidget(0, 6); self.table.setHorizontalHeaderLabels(["MATRÍCULA", "NOMBRE", "CARRERA", "SEM", "CICLO", "ACCIONES"])
        self.table.verticalHeader().setVisible(False); self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch); self.table.setSelectionBehavior(QAbstractItemView.SelectRows); self.table.setShowGrid(False); self.table.setFocusPolicy(Qt.NoFocus); self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.cellDoubleClicked.connect(self.open_student_profile)
        self.table.setStyleSheet("QTableWidget { background: white; border-radius: 10px; border: none; } QHeaderView::section { background-color: #f8fafc; color: #0f172a; padding: 12px; font-weight: bold; border-bottom: 2px solid #e2e8f0; border: none;} QTableWidget::item { padding: 10px; border-bottom: 1px solid #f1f5f9; } QTableWidget::item:selected { background-color: #eff6ff; color: #1e40af; }")
        
        self.empty = QWidget(); el = QVBoxLayout(self.empty); el.setAlignment(Qt.AlignCenter); el.addWidget(QLabel("No se encontraron resultados.", styleSheet="color: #94a3b8; font-weight: bold; border: none;"))
        self.stack.addWidget(self.table); self.stack.addWidget(self.empty); ly.addWidget(self.stack)

    def apply_filter(self):
        # 1. Obtener valores de los controles
        search_txt = self.search_input.text().lower().strip()
        sem_f = self.f_sem.currentText()
        car_f = self.f_career.currentText()
        cyc_f = self.f_cyc.currentText()
        
        self.table.setRowCount(0); found = 0
        st = self.engine.students if hasattr(self.engine, 'students') else []
        
        for s in st:
            # Regla Base: Solo mostrar si tiene documentos (Si quieres ver a todos, borra esta línea)
            if not any(w.get('pdf_path') for w in s.get('workshops', [])): continue

            # 2. Filtro por Texto (Nombre o Matrícula)
            full_name = f"{s.get('nombres','')} {s.get('apellidoPaterno','')} {s.get('apellidoMaterno','')}".lower()
            mat = str(s.get('matricula', '')).lower()
            
            if search_txt and (search_txt not in mat and search_txt not in full_name):
                continue

            # 3. Filtros Desplegables
            s_sem = str(s.get('semestre', '1'))
            s_car = str(s.get('career', ''))
            s_cyc = str(s.get('schoolCycle', ''))
            
            if sem_f != "Todos los Semestres" and s_sem != sem_f: continue
            if car_f != "Todas las Carreras" and s_car != car_f: continue
            if cyc_f != "Todos los Ciclos" and s_cyc != cyc_f: continue
            
            # 4. Insertar Fila
            found += 1; r = self.table.rowCount(); self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(s.get('matricula')))
            self.table.setItem(r, 1, QTableWidgetItem(full_name.upper()))
            self.table.setItem(r, 2, QTableWidgetItem(s.get('career')))
            self.table.setItem(r, 3, QTableWidgetItem(str(s.get('semestre'))))
            self.table.setItem(r, 4, QTableWidgetItem(s.get('schoolCycle')))
            
            btn = QPushButton("👁️ Ver"); btn.setCursor(Qt.PointingHandCursor); btn.setStyleSheet("background: #f1f5f9; border: 1px solid #cbd5e1; padding: 5px;")
            btn.clicked.connect(lambda _, x=s: self.open_dialog(x))
            w = QWidget(); l = QHBoxLayout(w); l.setContentsMargins(0,0,0,0); l.setAlignment(Qt.AlignCenter); l.addWidget(btn); self.table.setCellWidget(r, 5, w)
            self.table.item(r, 0).setData(Qt.UserRole, s)
            
        self.stack.setCurrentIndex(0 if found > 0 else 1)

    def open_student_profile(self, r, c): self.open_dialog(self.table.item(r, 0).data(Qt.UserRole))
    def open_dialog(self, s): d = StudentDetailDialog(s, self.engine, self); d.exec(); self.apply_filter()