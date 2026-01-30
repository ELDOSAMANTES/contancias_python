from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QToolTip
from PySide6.QtCharts import QChart, QChartView, QPieSeries
from PySide6.QtGui import QPainter, QCursor, QFont
from PySide6.QtCore import Qt
from components import StatCard

class DashboardPage(QWidget):
    def __init__(self, engine):
        super().__init__()
        self.engine = engine
        self.setup_ui()

    def setup_ui(self):
        ly = QVBoxLayout(self)
        ly.setContentsMargins(30, 30, 30, 30)
        ly.setSpacing(20)
        
        # 1. TÍTULO
        title = QLabel("Dashboard")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #0f172a; font-family: 'Segoe UI';")
        ly.addWidget(title)
        
        # 2. TARJETAS SUPERIORES (Stats)
        self.stats_ly = QHBoxLayout()
        self.stats_ly.setSpacing(20)
        ly.addLayout(self.stats_ly)

        # 3. GRÁFICAS (Charts)
        charts_ly = QHBoxLayout()
        charts_ly.setSpacing(20)
        
        # --- Gráfica 1: Distribución por Carrera ---
        self.c1_view = QChartView()
        self.c1_view.setRenderHint(QPainter.Antialiasing)
        self.c1_view.setStyleSheet("background: transparent;")
        
        c1_card = QFrame()
        c1_card.setStyleSheet("background: white; border-radius: 16px; border: 1px solid #f1f5f9;")
        c1_v = QVBoxLayout(c1_card)
        c1_v.setContentsMargins(20, 20, 20, 20)
        c1_v.addWidget(QLabel("<b style='color:#0f172a; font-size:14px;'>Distribución por Carrera</b>"))
        c1_v.addWidget(self.c1_view)
        charts_ly.addWidget(c1_card)

        # --- Gráfica 2: Talleres Populares ---
        self.c2_view = QChartView()
        self.c2_view.setRenderHint(QPainter.Antialiasing)
        self.c2_view.setStyleSheet("background: transparent;")
        
        c2_card = QFrame()
        c2_card.setStyleSheet("background: white; border-radius: 16px; border: 1px solid #f1f5f9;")
        c2_v = QVBoxLayout(c2_card)
        c2_v.setContentsMargins(20, 20, 20, 20)
        c2_v.addWidget(QLabel("<b style='color:#0f172a; font-size:14px;'>Talleres Populares</b>"))
        c2_v.addWidget(self.c2_view)
        charts_ly.addWidget(c2_card)

        ly.addLayout(charts_ly)

    def refresh(self):
        """Actualiza la información en tiempo real"""
        stats = self.engine.get_stats()
        
        # Limpiar tarjetas viejas
        for i in reversed(range(self.stats_ly.count())): 
            self.stats_ly.itemAt(i).widget().setParent(None)
        
        # --- CREAR TARJETAS (NUEVO FORMATO DE 6 ARGUMENTOS) ---
        
        # 1. Total Alumnos (Morado)
        self.stats_ly.addWidget(StatCard(
            "Total Alumnos", stats['total'], "Registrados", "👥", 
            "#f3e8ff", "#7e22ce" 
        ))
        
        # 2. Talleres Cursando (Azul)
        self.stats_ly.addWidget(StatCard(
            "Talleres Cursando", stats['cursando'], "En proceso", "📖", 
            "#dbeafe", "#2563eb" 
        ))
        
        # 3. Talleres Acreditados (Naranja)
        self.stats_ly.addWidget(StatCard(
            "Talleres Acreditados", stats['accredited'], "Completados", "🏅", 
            "#ffedd5", "#c2410c" 
        ))

        # 4. Listos p/ Constancia (Gris)
        self.stats_ly.addWidget(StatCard(
            "Listos p/ Constancia", stats['ready'], "Con 2+ créditos", "📄", 
            "#f1f5f9", "#64748b" 
        ))

        # --- ACTUALIZAR GRÁFICAS ---
        self.setup_pie(self.c1_view, stats['byCareer'])
        self.setup_pie(self.c2_view, dict(list(stats['byWorkshop'].items())[:5]))

    def setup_pie(self, view, data):
        series = QPieSeries()
        series.setHoleSize(0.45) # Hace el agujero de la dona
        
        for name, value in data.items():
            slice_ = series.append(name, value)
            slice_.hovered.connect(lambda state, s=slice_: self.on_slice_hover(state, s))
        
        chart = QChart()
        chart.addSeries(series)
        chart.setAnimationOptions(QChart.SeriesAnimations)
        
        # Configuración de Leyenda
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignTop)
        chart.legend().setFont(QFont("Segoe UI", 8))
        chart.setBackgroundVisible(False)
        chart.layout().setContentsMargins(0, 0, 0, 0)
        
        view.setChart(chart)

    def on_slice_hover(self, state, slice_):
        slice_.setExploded(state)
        if state:
            percentage = (slice_.percentage() * 100)
            QToolTip.showText(QCursor.pos(), f"{slice_.label()}: {slice_.value()} ({percentage:.1f}%)")