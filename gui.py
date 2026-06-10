import json, os, re, webbrowser
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QPushButton, QLineEdit, QComboBox,
    QTabWidget, QScrollArea, QFrame, QTextEdit, QSizePolicy,
    QMessageBox, QDateEdit, QDialog, QFormLayout, QDialogButtonBox,
    QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt, QTimer, QDate, pyqtSignal
from PyQt6.QtGui import QFont, QAction

from ortools.sat.python import cp_model
from scheduler import ExamScheduler
from html_exporter import export_html_file
from seed_data import get_seed_data

# ── Colores del tema (azul índigo + dorado) ─────────────────────────────
C_PRI    = "#6366f1"   # Azul índigo principal
C_PRI_D  = "#4f46e5"   # Azul más oscuro (hover)
C_PRI_L  = "#a5b4fc"   # Azul claro (texto seleccionado en modo oscuro)
C_ACCENT = "#f59e0b"   # Dorado/ámbar (acento)
C_RED    = "#ef4444"   # Rojo (peligro/eliminar)
C_SLATE  = "#94a3b8"   # Gris pizarra (texto secundario)

# Colores modo CLARO
C_BG      = "#f8fafc"
C_CARD    = "#ffffff"
C_BORDER  = "#e2e8f0"
C_TEXT    = "#0f172a"
C_TEXT2   = "#475569"

# Colores modo OSCURO
C_BG_D      = "#0f172a"
C_CARD_D    = "#1e293b"
C_BORDER_D  = "#334155"
C_TEXT_D    = "#f8fafc"
C_TEXT2_D   = "#94a3b8"

# Colores para destacar cada estudio (se asignan cíclicamente)
STUDY_COLORS = [C_PRI, C_RED, "#10b981", "#8b5cf6", C_ACCENT, "#06b6d4", "#ec4899", "#3b82f6", "#f97316", "#14b8a6"]

# Días de la semana en español
DAYS_ES = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]

# Directorios del proyecto
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECTS_DIR = os.path.join(BASE_DIR, "projects")

# ══════════════════════════════════════════════════════════════════════════
# HOJAS DE ESTILO QSS (Qt Style Sheets)
# ══════════════════════════════════════════════════════════════════════════
# QSS es el equivalente a CSS para aplicaciones Qt. Aquí definimos dos
# temas completos: modo claro y modo oscuro. Se aplican con setStyleSheet().

LIGHT_QSS = f"""
QMainWindow {{ background: {C_BG}; }}
QTabWidget {{ background: {C_BG}; }}
QTabWidget::pane {{ background: {C_BG}; border: 1px solid {C_BORDER}; border-radius: 8px; }}
QWidget#tab_content {{ background: transparent; }}
QTabBar::tab {{ background: {C_BORDER}; color: {C_TEXT2}; padding: 8px 18px; margin-right: 2px; border-top-left-radius: 6px; border-top-right-radius: 6px; font-size: 13px; }}
QTabBar::tab:selected {{ background: {C_CARD}; color: {C_PRI}; font-weight: bold; }}
QPushButton {{ background: {C_PRI}; color: #fff; border: none; padding: 6px 14px; border-radius: 5px; font-size: 12px; }}
QPushButton:hover {{ background: {C_PRI_D}; }}
QPushButton#danger {{ background: {C_RED}; }}
QPushButton#danger:hover {{ background: #b91c1c; }}
QPushButton#secondary {{ background: {C_BORDER}; color: {C_TEXT}; }}
QPushButton#secondary:hover {{ background: #cbd5e1; }}
QLineEdit {{ background: {C_CARD}; border: 1px solid {C_BORDER}; border-radius: 4px; padding: 4px 7px; color: {C_TEXT}; }}
QComboBox {{ background: {C_CARD}; border: 1px solid {C_BORDER}; border-radius: 4px; padding: 4px 7px; color: {C_TEXT}; }}
QLabel {{ color: {C_TEXT}; }}
QTextEdit {{ background: #f1f5f9; border: 1px solid {C_BORDER}; border-radius: 6px; color: {C_TEXT}; font-family: Consolas; }}
QScrollBar:vertical {{ background: {C_BG}; width: 8px; border-radius: 4px; }}
QScrollBar::handle:vertical {{ background: #cbd5e1; border-radius: 4px; min-height: 20px; }}
QFrame#card {{ background: {C_CARD}; border: 1px solid {C_BORDER}; border-radius: 8px; }}
QFrame#sep {{ background: {C_BORDER}; max-height: 1px; }}
QFrame#row {{ background: {C_CARD}; border: 1px solid {C_BORDER}; border-radius: 5px; }}
QFrame#row:hover {{ background: #f1f5f9; }}
QFrame#row_selected {{ background: #dbeafe; border: 1px solid {C_PRI}; border-radius: 5px; }}
QFrame#slot_row {{ background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 4px; }}
QFrame#exam_row {{ background: #fefce8; border: 1px solid #fde68a; border-radius: 4px; }}
"""

DARK_QSS = f"""
QMainWindow {{ background: {C_BG_D}; }}
QTabWidget {{ background: {C_BG_D}; }}
QTabWidget::pane {{ background: {C_BG_D}; border: 1px solid {C_BORDER_D}; border-radius: 8px; }}
QWidget#tab_content {{ background: transparent; }}
QTabBar::tab {{ background: {C_BORDER_D}; color: {C_TEXT2_D}; padding: 8px 18px; margin-right: 2px; border-top-left-radius: 6px; border-top-right-radius: 6px; font-size: 13px; }}
QTabBar::tab:selected {{ background: {C_CARD_D}; color: {C_PRI_L}; font-weight: bold; }}
QPushButton {{ background: {C_PRI}; color: #fff; border: none; padding: 6px 14px; border-radius: 5px; font-size: 12px; }}
QPushButton:hover {{ background: {C_PRI_D}; }}
QPushButton#danger {{ background: {C_RED}; }}
QPushButton#danger:hover {{ background: #b91c1c; }}
QPushButton#secondary {{ background: {C_BORDER_D}; color: {C_TEXT_D}; }}
QPushButton#secondary:hover {{ background: #475569; }}
QLineEdit {{ background: {C_BG_D}; border: 1px solid {C_BORDER_D}; border-radius: 4px; padding: 4px 7px; color: {C_TEXT_D}; }}
QComboBox {{ background: {C_BG_D}; border: 1px solid {C_BORDER_D}; border-radius: 4px; padding: 4px 7px; color: {C_TEXT_D}; }}
QLabel {{ color: {C_TEXT_D}; }}
QTextEdit {{ background: {C_BG_D}; border: 1px solid {C_BORDER_D}; border-radius: 6px; color: #e2e8f0; font-family: Consolas; }}
QScrollBar:vertical {{ background: {C_BG_D}; width: 8px; border-radius: 4px; }}
QScrollBar::handle:vertical {{ background: #475569; border-radius: 4px; min-height: 20px; }}
QFrame#card {{ background: {C_CARD_D}; border: 1px solid {C_BORDER_D}; border-radius: 8px; }}
QFrame#sep {{ background: {C_BORDER_D}; max-height: 1px; }}
QFrame#row {{ background: {C_CARD_D}; border: 1px solid {C_BORDER_D}; border-radius: 5px; }}
QFrame#row:hover {{ background: #1a2332; }}
QFrame#row_selected {{ background: #1a3a5c; border: 1px solid {C_PRI_L}; border-radius: 5px; }}
QFrame#slot_row {{ background: #0a3d2a; border: 1px solid #166534; border-radius: 4px; }}
QFrame#exam_row {{ background: #422006; border: 1px solid #713f12; border-radius: 4px; }}
"""


# ══════════════════════════════════════════════════════════════════════════
# FUNCIONES AUXILIARES (independientes de la UI)
# ══════════════════════════════════════════════════════════════════════════

def _ensure_dirs():
    """Crea la carpeta projects/ si no existe."""
    os.makedirs(PROJECTS_DIR, exist_ok=True)


def _list_projects():
    """Lista los nombres de todos los proyectos guardados en projects/."""
    _ensure_dirs()
    names = []
    for f in sorted(os.listdir(PROJECTS_DIR)):
        if not f.endswith(".json"): continue
        try:
            with open(os.path.join(PROJECTS_DIR, f), "r", encoding="utf-8") as fh:
                names.append(json.load(fh).get("name", f.replace(".json", "")))
        except Exception:
            names.append(f.replace(".json", ""))
    return names


def _project_filename(name):
    """Convierte un nombre de proyecto en una ruta de archivo JSON segura."""
    safe = re.sub(r"[^a-zA-Z0-9_\-]", "_", name.strip() or "sin_titulo")
    return os.path.join(PROJECTS_DIR, f"{safe}.json")


def _save_project(name, classrooms, exams):
    """Guarda un proyecto (nombre, aulas, exámenes) en un archivo JSON."""
    _ensure_dirs()
    with open(_project_filename(name), "w", encoding="utf-8") as f:
        json.dump({"name": name.strip() or "Sin título", "classrooms": classrooms, "exams": exams},
                  f, ensure_ascii=False, indent=2)


def _load_project(name):
    """Carga un proyecto desde un archivo JSON."""
    with open(_project_filename(name), "r", encoding="utf-8") as f:
        return json.load(f)


def _delete_project_file(name):
    """Elimina el archivo JSON de un proyecto."""
    p = _project_filename(name)
    if os.path.exists(p): os.remove(p)


def _fmt_slot(s):
    """Formatea una franja horaria como texto legible. Ej: '15/06/2026  09:00 - 11:00'."""
    try:
        d = datetime.strptime(s["date"], "%Y-%m-%d")
        df = d.strftime("%d/%m/%Y")
    except Exception:
        df = s.get("date", "?")
    return f"{df}  {s.get('start', '?')} - {s.get('end', '?')}"


def _fmt_short_day(date_str):
    """Formatea una fecha como 'Lunes 15/06'."""
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d")
        wd = d.weekday()
        return f"{DAYS_ES[wd].capitalize()} {d.day}/{d.month:02d}"
    except ValueError:
        return date_str


# ══════════════════════════════════════════════════════════════════════════
# CLASE Toast - Notificaciones emergentes
# ══════════════════════════════════════════════════════════════════════════

class Toast(QFrame):
    """Notificación tipo 'toast' que aparece y desaparece sola."""

    def __init__(self, parent):
        super().__init__(parent)
        self.setObjectName("toast")
        self.setStyleSheet("background: #059669; border-radius: 8px;")
        self.label = QLabel(self)
        self.label.setStyleSheet("color: white; font-size: 13px; padding: 10px 24px;")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hide()

    def show(self, message, type="success"):
        colors = {"success": "#059669", "warning": "#d97706", "error": "#dc2626"}
        self.setStyleSheet(f"background: {colors.get(type, '#059669')}; border-radius: 8px;")
        self.label.setText(message)
        w = self.parent().width()
        self.setFixedWidth(min(400, w - 40))
        self.adjustSize()
        self.move((w - self.width()) // 2, 16)
        self.raise_()
        super().show()
        QTimer.singleShot(3500, self.hide)


# ══════════════════════════════════════════════════════════════════════════
# CLASE ClickFrame - Marco cliqueable
# ══════════════════════════════════════════════════════════════════════════

class ClickFrame(QFrame):
    """QFrame que emite una señal cuando se hace clic en él."""
    clicked = pyqtSignal(int)
    def __init__(self, idx, parent=None):
        super().__init__(parent)
        self.idx = idx
    def mousePressEvent(self, e):
        self.clicked.emit(self.idx)
        super().mousePressEvent(e)


# ══════════════════════════════════════════════════════════════════════════
# CLASE PRINCIPAL App
# ══════════════════════════════════════════════════════════════════════════

class App(QMainWindow):
    """
    Ventana principal de la aplicación.
    
    Pestañas:
      🏠 Proyecto   - Gestión de proyectos (crear, guardar, cargar)
      📋 Exámenes   - Añadir/eliminar exámenes
      🏫 Aulas      - Añadir/eliminar aulas con sus franjas horarias
      ⚙️ Generar    - Generar calendario (con múltiples opciones)
      📅 Calendario - Ver el calendario generado
    """

    def __init__(self):
        super().__init__()
        # Configuración de la ventana
        # Título con emojis: 📅=calendario, 🎓=exámenes, ⚡=solver rápido
        self.setWindowTitle("📅🎓 Generador de Calendario de Exámenes ⚡")
        # Tamaño mínimo (proporción 16:9 aproximada)
        self.setMinimumSize(1100, 620)
        # Tamaño inicial 1280x720 (HD, 16:9 exacto)
        self.resize(1280, 720)

        # Datos de la aplicación
        self.exams = []                    # Lista de exámenes
        self.classrooms = []               # Lista de aulas
        self.project_name = ""             # Nombre del proyecto actual
        self.last_assignment = None        # Última asignación generada
        self.last_html_path = None         # Ruta del último HTML exportado
        self._dirty = False                # ¿Hay cambios sin guardar?
        self._selected_classroom_idx = None  # Índice del aula seleccionada
        self._dark_mode = False            # Modo oscuro activado?

        # Construir la interfaz
        self._build_ui()
        self._apply_theme()
        self._refresh_project_list()
        self._rebuild_classroom_list()
        self._rebuild_exam_list()
        self._update_stats()

    # ── Tema (claro/oscuro) ─────────────────────────────────────────────

    def _apply_theme(self):
        """Aplica el tema claro u oscuro según _dark_mode."""
        qss = DARK_QSS if self._dark_mode else LIGHT_QSS
        QApplication.instance().setStyleSheet(qss)
        self.theme_btn.setText("☀️ Claro" if self._dark_mode else "🌙 Oscuro")
        self.header_bar.setStyleSheet(f"background: {C_PRI}; border-radius: 0;")

    def _toggle_theme(self):
        """Cambia entre modo claro y oscuro."""
        self._dark_mode = not self._dark_mode
        self._apply_theme()

    # ── Construcción de la interfaz ─────────────────────────────────────

    def _build_ui(self):
        """Construye toda la interfaz gráfica: barra superior y pestañas."""
        central = QWidget()
        self.setCentralWidget(central)
        main_v = QVBoxLayout(central)
        main_v.setContentsMargins(0, 0, 0, 0)
        main_v.setSpacing(0)

        # ─── Barra superior (encabezado) ───
        self.header_bar = QFrame()
        self.header_bar.setFixedHeight(48)
        hdr_lay = QHBoxLayout(self.header_bar)
        hdr_lay.setContentsMargins(20, 0, 20, 0)

        title = QLabel("📅🎓  Generador de Calendario de Exámenes  ⚡")
        title.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
        hdr_lay.addWidget(title)
        hdr_lay.addStretch()

        self.theme_btn = QPushButton("☀️ Claro")
        self.theme_btn.setFixedSize(100, 30)
        self.theme_btn.setStyleSheet("background: rgba(255,255,255,0.2); color: white; border: 1px solid rgba(255,255,255,0.3); border-radius: 4px;")
        self.theme_btn.clicked.connect(self._toggle_theme)
        hdr_lay.addWidget(self.theme_btn)
        main_v.addWidget(self.header_bar)

        # ─── Pestañas ───
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        main_v.addWidget(self.tabs)

        self._build_project_tab()
        self._build_exams_tab()
        self._build_classrooms_tab()
        self._build_generate_tab()
        self._build_calendar_tab()

        # Toast (notificaciones emergentes)
        self.toast = Toast(self)

    def _tab_widget(self, scroll=True):
        """Crea un widget para el contenido de una pestaña, con o sin scroll."""
        w = QWidget()
        w.setObjectName("tab_content")
        if scroll:
            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)
            scroll_area.setWidget(w)
            scroll_area.setFrameShape(QFrame.Shape.NoFrame)
            scroll_area.viewport().setAutoFillBackground(False)
            return scroll_area, w
        return w, w

    # ── Pestaña: Proyecto ───────────────────────────────────────────────

    def _build_project_tab(self):
        """Construye la pestaña de gestión de proyectos."""
        sa, tab = self._tab_widget(True)
        self.tabs.addTab(sa, "🏠 Proyecto")
        v = QVBoxLayout(tab)
        v.setContentsMargins(20, 16, 20, 16)
        v.setSpacing(8)

        # Título de la sección
        titulo = QLabel("🏠  Gestión de Proyectos")
        titulo.setStyleSheet("font-size: 18px; font-weight: bold;")
        v.addWidget(titulo)

        # Fila: selector de proyectos + botones
        sel = QHBoxLayout()
        self.project_selector = QComboBox()
        self.project_selector.setMinimumWidth(300)
        self.project_selector.currentTextChanged.connect(self._on_project_selected)
        sel.addWidget(self.project_selector)

        def btn(text, obj, cmd, color=None):
            b = QPushButton(text)
            b.clicked.connect(cmd)
            if color: b.setObjectName(color)
            sel.addWidget(b)
            return b
        btn("➕ Nuevo", None, self._new_project, "secondary")
        btn("💾 Guardar", None, self._save_current)
        btn("🗑️ Eliminar", None, self._delete_project, "danger")
        v.addLayout(sel)

        # Nombre del proyecto
        v.addWidget(QLabel("📛 Nombre del proyecto:"))
        self.project_name_input = QLineEdit()
        self.project_name_input.setPlaceholderText("Nombre del proyecto...")
        self.project_name_input.textChanged.connect(lambda: self._mark_dirty())
        v.addWidget(self.project_name_input)

        # Estadísticas
        stats = QHBoxLayout()
        self.info_exams = QLabel("📋 0 exámenes")
        self.info_exams.setStyleSheet(f"font-weight: bold; color: {C_PRI};")
        self.info_classrooms = QLabel("🏫 0 aulas")
        self.info_slots = QLabel("🗓 0 franjas")
        self.info_students = QLabel("👥 0 alumnos")
        self.info_studies = QLabel("📚 0 estudios")
        for lbl in [self.info_exams, self.info_classrooms, self.info_slots, self.info_students, self.info_studies]:
            stats.addWidget(lbl)
            stats.addSpacing(18)
        stats.addStretch()
        v.addLayout(stats)

        # Fila inferior
        bf = QHBoxLayout()
        btn("📦 Cargar datos ficticios", None, self._load_seed, "secondary")
        self._dirty_label = QLabel("")
        self._dirty_label.setStyleSheet(f"color: {C_ACCENT};")
        bf.addWidget(self._dirty_label)
        bf.addStretch()
        v.addLayout(bf)

        v.addWidget(self._sep())

        # Flujo de trabajo
        v.addWidget(QLabel("💡 Flujo de trabajo — pasos:"))
        info = QLabel(
            "1. 📋 Crea o selecciona un proyecto\n"
            "2. 📝 Añade exámenes: nombre, alumnos, estudio\n"
            "3. 🏫 Añade aulas con capacidad y franjas disponibles\n"
            "4. ⚙️ Genera el calendario — el solver CP-SAT asigna todo\n"
            "5. 📅 Abre el HTML e imprime como PDF"
        )
        info.setWordWrap(True)
        info.setStyleSheet(f"color: {C_TEXT2}; padding: 8px;")
        v.addWidget(info)
        v.addStretch()

    # ── Pestaña: Exámenes ──────────────────────────────────────────────

    def _build_exams_tab(self):
        """Construye la pestaña para gestionar exámenes."""
        sa, tab = self._tab_widget(True)
        self.tabs.addTab(sa, "📋 Exámenes")
        v = QVBoxLayout(tab)
        v.setContentsMargins(20, 16, 20, 16)
        v.setSpacing(8)

        # Formulario de añadir examen
        f = QHBoxLayout()
        f.addWidget(QLabel("📝 Nombre:"))
        self.ex_name = QLineEdit(); self.ex_name.setPlaceholderText("Nombre examen"); self.ex_name.setFixedWidth(200)
        f.addWidget(self.ex_name)
        f.addSpacing(4)
        f.addWidget(QLabel("👥 Alumnos:"))
        self.ex_students = QLineEdit("25"); self.ex_students.setFixedWidth(50)
        f.addWidget(self.ex_students)
        f.addSpacing(4)
        f.addWidget(QLabel("📚 Estudio:"))
        self.ex_study = QLineEdit(); self.ex_study.setPlaceholderText("Ciclo / materia"); self.ex_study.setFixedWidth(180)
        f.addWidget(self.ex_study)
        f.addSpacing(6)
        b = QPushButton("➕ Añadir examen")
        b.clicked.connect(self._add_exam)
        f.addWidget(b)
        f.addStretch()
        v.addLayout(f)

        self.exam_count = QLabel("📋 0 exámenes")
        self.exam_count.setStyleSheet("font-weight: bold;")
        v.addWidget(self.exam_count)

        # Lista de exámenes (con scroll)
        self.exam_scroll = QScrollArea()
        self.exam_scroll.setWidgetResizable(True)
        self.exam_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.exam_container = QWidget()
        self.exam_layout = QVBoxLayout(self.exam_container)
        self.exam_layout.setSpacing(2)
        self.exam_layout.setContentsMargins(0, 0, 0, 0)
        self.exam_layout.addStretch()
        self.exam_scroll.setWidget(self.exam_container)
        v.addWidget(self.exam_scroll, 1)

    # ── Pestaña: Aulas ─────────────────────────────────────────────────

    def _build_classrooms_tab(self):
        """Construye la pestaña para gestionar aulas y sus franjas."""
        sa, tab = self._tab_widget(True)
        self.tabs.addTab(sa, "🏫 Aulas")
        v = QVBoxLayout(tab)
        v.setContentsMargins(20, 16, 20, 16)
        v.setSpacing(8)

        # Formulario de añadir aula
        f = QHBoxLayout()
        f.addWidget(QLabel("🏫 Nombre:"))
        self.cl_name = QLineEdit(); self.cl_name.setPlaceholderText("Nombre aula"); self.cl_name.setFixedWidth(150)
        f.addWidget(self.cl_name)
        f.addSpacing(4)
        f.addWidget(QLabel("👥 Capacidad:"))
        self.cl_cap = QLineEdit("30"); self.cl_cap.setFixedWidth(50)
        f.addWidget(self.cl_cap)
        f.addSpacing(6)
        b = QPushButton("➕ Añadir aula")
        b.clicked.connect(self._add_classroom)
        f.addWidget(b)
        f.addStretch()
        v.addLayout(f)

        self.classroom_count = QLabel("🏫 0 aulas")
        self.classroom_count.setStyleSheet("font-weight: bold;")
        v.addWidget(self.classroom_count)

        # Lista de aulas (clicables)
        self.classroom_scroll = QScrollArea()
        self.classroom_scroll.setWidgetResizable(True)
        self.classroom_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.classroom_container = QWidget()
        self.classroom_list_layout = QVBoxLayout(self.classroom_container)
        self.classroom_list_layout.setSpacing(3)
        self.classroom_list_layout.setContentsMargins(0, 0, 0, 0)
        self.classroom_list_layout.addStretch()
        self.classroom_scroll.setWidget(self.classroom_container)
        v.addWidget(self.classroom_scroll, 2)

        v.addWidget(self._sep())

        # ─── Gestión de franjas del aula seleccionada ───
        slot_top = QHBoxLayout()
        self.slot_header = QLabel("📅 Franjas: (ningún aula seleccionada)")
        self.slot_header.setStyleSheet("font-weight: bold; font-size: 14px;")
        slot_top.addWidget(self.slot_header)
        slot_top.addStretch()

        self.slot_date = QDateEdit()
        self.slot_date.setCalendarPopup(True)
        self.slot_date.setDisplayFormat("yyyy-MM-dd")
        self.slot_date.setDate(datetime.strptime("2026-06-15", "%Y-%m-%d").date())
        slot_top.addWidget(self.slot_date)
        v.addLayout(slot_top)

        # Botones de añadir franja
        presets = QHBoxLayout()
        presets.setSpacing(6)
        add_custom = QPushButton("➕ Personalizada")
        add_custom.clicked.connect(self._add_slot_custom)
        presets.addWidget(add_custom)
        presets.addSpacing(12)
        for lbl, s, e in [("☕ Mañana  09-14h", "09:00", "14:00"),
                          ("🌤 Tarde 15-18h", "15:00", "18:00"),
                          ("🌞 Completa 09-18h", "09:00", "18:00")]:
            b = QPushButton(lbl)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.clicked.connect(lambda checked, ss=s, ee=e: self._add_slot_preset(ss, ee))
            presets.addWidget(b)
        presets.addStretch()
        v.addLayout(presets)

        # Lista de franjas del aula seleccionada
        self.slot_scroll = QScrollArea()
        self.slot_scroll.setWidgetResizable(True)
        self.slot_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.slot_container = QWidget()
        self.slot_layout = QVBoxLayout(self.slot_container)
        self.slot_layout.setSpacing(2)
        self.slot_layout.setContentsMargins(0, 0, 0, 0)
        self.slot_layout.addStretch()
        self.slot_scroll.setWidget(self.slot_container)
        v.addWidget(self.slot_scroll, 3)

    # ── Pestaña: Generar ───────────────────────────────────────────────

    def _build_generate_tab(self):
        """Construye la pestaña para generar el calendario."""
        sa, tab = self._tab_widget(True)
        self.tabs.addTab(sa, "⚙️ Generar")
        v = QVBoxLayout(tab)
        v.setContentsMargins(20, 16, 20, 16)
        v.setSpacing(8)

        v.addWidget(QLabel("⚙️ Generar calendario de exámenes"))
        self.gen_summary = QLabel("")
        self.gen_summary.setStyleSheet(f"color: {C_SLATE};")
        v.addWidget(self.gen_summary)

        gen_btn = QPushButton("🚀 Generar Calendario")
        gen_btn.setMinimumHeight(50)
        gen_btn.setStyleSheet(f"font-size: 18px; font-weight: bold; background: {C_PRI}; color: white; border-radius: 8px;")
        gen_btn.clicked.connect(self._generate)
        v.addWidget(gen_btn)

        v.addWidget(QLabel("📜 Log:"), alignment=Qt.AlignmentFlag.AlignBottom)
        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        self.status_text.setMinimumHeight(200)
        self.status_text.append("💡 Define exámenes y aulas, después pulsa Generar.\n")
        v.addWidget(self.status_text, 1)

    # ── Pestaña: Calendario ────────────────────────────────────────────

    def _build_calendar_tab(self):
        """Construye la pestaña que muestra el calendario generado."""
        sa, tab = self._tab_widget(True)
        self.tabs.addTab(sa, "📅 Calendario")
        v = QVBoxLayout(tab)
        v.setContentsMargins(20, 16, 20, 16)
        v.setSpacing(8)

        bf = QHBoxLayout()
        self.open_btn = QPushButton("🌐 Abrir en navegador")
        self.open_btn.setObjectName("secondary")
        self.open_btn.clicked.connect(self._open_html)
        self.open_btn.setEnabled(False)
        bf.addWidget(self.open_btn)

        self.open_folder_btn = QPushButton("📂 Abrir carpeta")
        self.open_folder_btn.setObjectName("secondary")
        self.open_folder_btn.clicked.connect(self._open_folder)
        self.open_folder_btn.setEnabled(False)
        bf.addWidget(self.open_folder_btn)

        self.cal_summary = QLabel("")
        self.cal_summary.setStyleSheet(f"color: {C_SLATE};")
        bf.addStretch()
        bf.addWidget(self.cal_summary)
        v.addLayout(bf)

        self.cal_scroll = QScrollArea()
        self.cal_scroll.setWidgetResizable(True)
        self.cal_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.cal_container = QWidget()
        self.cal_layout = QVBoxLayout(self.cal_container)
        self.cal_layout.setContentsMargins(0, 0, 0, 0)
        self.cal_scroll.setWidget(self.cal_container)
        v.addWidget(self.cal_scroll, 1)

        empty = QLabel("📭 Aún no hay calendario.\nVe a ⚙️ Generar y pulsa el botón.")
        empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty.setStyleSheet(f"color: {C_SLATE}; font-size: 15px;")
        self.cal_layout.addWidget(empty)

    # ── Métodos auxiliares ─────────────────────────────────────────────

    def _sep(self):
        """Crea una línea separadora horizontal."""
        s = QFrame()
        s.setObjectName("sep")
        s.setFixedHeight(1)
        return s

    def _study_color(self, study_name):
        """Devuelve el color asignado a un estudio."""
        studies = sorted({e["study"] for e in self.exams})
        idx = studies.index(study_name) % len(STUDY_COLORS) if study_name in studies else 0
        return STUDY_COLORS[idx]

    @staticmethod
    def _rgba(hexc, alpha=0.13):
        """Convierte un color hex a rgba con transparencia."""
        h = hexc.lstrip("#")
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return f"rgba({r},{g},{b},{alpha})"

    # ── Lista de aulas ─────────────────────────────────────────────────

    def _rebuild_classroom_list(self):
        """Reconstruye la lista visual de aulas."""
        while self.classroom_list_layout.count() > 1:
            item = self.classroom_list_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        for i, c in enumerate(self.classrooms):
            frame = ClickFrame(i)
            if i == self._selected_classroom_idx:
                frame.setObjectName("row_selected")
            else:
                frame.setObjectName("row")
            frame.setStyleSheet("")
            frame.setCursor(Qt.CursorShape.PointingHandCursor)
            frame.clicked.connect(self._select_classroom)

            row = QHBoxLayout(frame)
            row.setContentsMargins(10, 6, 10, 6)
            n_slots = len(c.get("time_slots", []))
            dot = QLabel("🏫")
            dot.setStyleSheet("font-size: 16px;")
            row.addWidget(dot)
            txt = QLabel(f"{c['name']:20s}  👥 {c['capacity']}  🗓 {n_slots} franjas")
            row.addWidget(txt, 1)
            del_btn = QPushButton("✕")
            del_btn.setFixedSize(28, 28)
            del_btn.setObjectName("danger")
            del_btn.clicked.connect(lambda checked, idx=i: self._delete_classroom(idx))
            row.addWidget(del_btn)

            self.classroom_list_layout.insertWidget(self.classroom_list_layout.count()-1, frame)

        self.classroom_count.setText(f"🏫 {len(self.classrooms)} aulas")

    def _select_classroom(self, idx):
        """Selecciona un aula de la lista para gestionar sus franjas."""
        if idx >= len(self.classrooms): return
        self._selected_classroom_idx = idx
        self._rebuild_classroom_list()
        self._refresh_slot_panel()

    # ── Panel de franjas ───────────────────────────────────────────────

    def _refresh_slot_panel(self):
        """Actualiza el panel de franjas del aula seleccionada."""
        while self.slot_layout.count() > 1:
            item = self.slot_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        if self._selected_classroom_idx is None or self._selected_classroom_idx >= len(self.classrooms):
            self.slot_header.setText("Franjas: (ningún aula seleccionada)")
            empty = QLabel("Selecciona un aula de la lista para gestionar sus franjas.")
            empty.setStyleSheet(f"color: {C_SLATE};")
            self.slot_layout.insertWidget(0, empty)
            return

        c = self.classrooms[self._selected_classroom_idx]
        self.slot_header.setText(f"Franjas de: {c['name']}  ({len(c.get('time_slots', []))} franjas)")

        for s in c.get("time_slots", []):
            frame = QFrame()
            frame.setObjectName("slot_row")
            row = QHBoxLayout(frame)
            row.setContentsMargins(10, 4, 10, 4)
            row.addWidget(QLabel(_fmt_slot(s)))
            del_btn = QPushButton("✕")
            del_btn.setFixedSize(24, 24)
            del_btn.setObjectName("danger")
            del_btn.clicked.connect(lambda checked, ref=s: self._delete_slot(ref))
            row.addWidget(del_btn, alignment=Qt.AlignmentFlag.AlignRight)
            row.addStretch()
            self.slot_layout.insertWidget(self.slot_layout.count()-1, frame)

    # ── Lista de exámenes ──────────────────────────────────────────────

    def _rebuild_exam_list(self):
        """Reconstruye la lista visual de exámenes."""
        while self.exam_layout.count() > 1:
            item = self.exam_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        for e in self.exams:
            frame = QFrame()
            frame.setObjectName("exam_row")
            row = QHBoxLayout(frame)
            row.setContentsMargins(10, 4, 10, 4)
            dsp = f"👥 {e['students']}  |  📚 {e['study']}"
            lbl = QLabel(f"📋 <b>{e['name']}</b>  —  {dsp}")
            lbl.setTextFormat(Qt.TextFormat.RichText)
            row.addWidget(lbl, 1)
            del_btn = QPushButton("✕")
            del_btn.setFixedSize(24, 24)
            del_btn.setObjectName("danger")
            del_btn.clicked.connect(lambda checked, ref=e: self._delete_exam(ref))
            row.addWidget(del_btn)
            self.exam_layout.insertWidget(self.exam_layout.count()-1, frame)

        self.exam_count.setText(f"📋 {len(self.exams)} exámenes")

    # ── Estadísticas ───────────────────────────────────────────────────

    def _update_stats(self):
        """Actualiza las estadísticas mostradas en la pestaña Proyecto."""
        n_slots = sum(len(c.get("time_slots", [])) for c in self.classrooms)
        n_students = sum(e["students"] for e in self.exams)
        n_studies = len({e["study"] for e in self.exams})
        self.info_exams.setText(f"📋 {len(self.exams)} exámenes")
        self.info_classrooms.setText(f"🏫 {len(self.classrooms)} aulas")
        self.info_slots.setText(f"🗓 {n_slots} franjas")
        self.info_students.setText(f"👥 {n_students} alumnos")
        self.info_studies.setText(f"📚 {n_studies} estudios")
        self.gen_summary.setText(
            f"📋 {len(self.exams)} exámenes  ·  🏫 {len(self.classrooms)} aulas  ·  🗓 {n_slots} franjas  ·  👥 {n_students} alumnos"
        )

    # ── Acciones: Aulas ────────────────────────────────────────────────

    def _add_classroom(self):
        """Añade un aula nueva a la lista."""
        name = self.cl_name.text().strip()
        if not name:
            self.toast.show("Nombre obligatorio", "warning"); return
        try:
            cap = int(self.cl_cap.text())
        except ValueError:
            self.toast.show("Capacidad debe ser un número entero", "warning"); return
        self.classrooms.append({"name": name, "capacity": cap, "time_slots": []})
        self._selected_classroom_idx = len(self.classrooms) - 1
        self._rebuild_classroom_list()
        self._refresh_slot_panel()
        self._update_stats()
        self.cl_name.clear()
        self.cl_cap.setText("30")
        self.toast.show(f"Aula «{name}» añadida")

    def _delete_classroom(self, idx):
        """Elimina un aula por su índice."""
        if idx >= len(self.classrooms): return
        self.classrooms.pop(idx)
        if self._selected_classroom_idx is not None:
            if self._selected_classroom_idx >= len(self.classrooms):
                self._selected_classroom_idx = len(self.classrooms) - 1 if self.classrooms else None
            elif self._selected_classroom_idx == idx:
                self._selected_classroom_idx = min(idx, len(self.classrooms)-1) if self.classrooms else None
        self._rebuild_classroom_list()
        self._refresh_slot_panel()
        self._update_stats()

    def _add_slot_preset(self, start, end):
        """Añade una franja predefinida al aula seleccionada."""
        if self._selected_classroom_idx is None or self._selected_classroom_idx >= len(self.classrooms):
            self.toast.show("Selecciona un aula primero", "warning"); return
        date = self.slot_date.date().toString("yyyy-MM-dd")
        slot = {"date": date, "start": start, "end": end}
        self.classrooms[self._selected_classroom_idx].setdefault("time_slots", []).append(slot)
        self._refresh_slot_panel()
        self._rebuild_classroom_list()
        self._update_stats()
        self.toast.show(f"✅ Franja {start}-{end} añadida", "success")

    def _add_slot_custom(self):
        """Muestra un diálogo para añadir una franja personalizada."""
        if self._selected_classroom_idx is None or self._selected_classroom_idx >= len(self.classrooms):
            self.toast.show("Selecciona un aula primero", "warning"); return
        d = QDialog(self)
        d.setWindowTitle("➕ Franja personalizada")
        d.setMinimumWidth(320)
        fl = QFormLayout(d)
        start_ed = QLineEdit("09:00")
        end_ed = QLineEdit("10:00")
        fl.addRow("🕐 Desde:", start_ed)
        fl.addRow("🕐 Hasta:", end_ed)
        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        bb.accepted.connect(d.accept)
        bb.rejected.connect(d.reject)
        fl.addRow(bb)
        if d.exec() != QDialog.DialogCode.Accepted:
            return
        date = self.slot_date.date().toString("yyyy-MM-dd")
        start = start_ed.text().strip()
        end = end_ed.text().strip()
        if not re.match(r"^\d{2}:\d{2}$", start) or not re.match(r"^\d{2}:\d{2}$", end):
            self.toast.show("La hora debe tener formato HH:MM", "warning"); return
        if start >= end:
            self.toast.show("La hora de inicio debe ser anterior a la de fin", "warning"); return
        slot = {"date": date, "start": start, "end": end}
        self.classrooms[self._selected_classroom_idx].setdefault("time_slots", []).append(slot)
        self._refresh_slot_panel()
        self._rebuild_classroom_list()
        self._update_stats()
        self.toast.show(f"✅ Franja {start}-{end} añadida", "success")

    def _delete_slot(self, slot):
        """Elimina una franja del aula seleccionada."""
        if self._selected_classroom_idx is not None and self._selected_classroom_idx < len(self.classrooms):
            c = self.classrooms[self._selected_classroom_idx]
            c["time_slots"] = [s for s in c["time_slots"] if s is not slot]
            self._refresh_slot_panel()
            self._rebuild_classroom_list()
            self._update_stats()

    # ── Acciones: Exámenes ─────────────────────────────────────────────

    def _add_exam(self):
        """Añade un examen nuevo a la lista."""
        name = self.ex_name.text().strip()
        nstr = self.ex_students.text().strip()
        study = self.ex_study.text().strip()
        if not name or not study:
            self.toast.show("Nombre y estudio obligatorios", "warning"); return
        try:
            students = int(nstr)
        except ValueError:
            self.toast.show("El número de alumnos debe ser un entero", "warning"); return
        self.exams.append({"name": name, "students": students, "study": study})
        self._rebuild_exam_list()
        self._mark_dirty()
        self._update_stats()
        self.ex_name.clear()
        self.ex_study.clear()
        self.toast.show(f"Examen «{name}» añadido")

    def _delete_exam(self, exam):
        """Elimina un examen de la lista."""
        self.exams = [x for x in self.exams if x is not exam]
        self._rebuild_exam_list()
        self._mark_dirty()
        self._update_stats()

    # ── Acciones: Proyectos ─────────────────────────────────────────────

    def _refresh_project_list(self):
        """Actualiza el selector de proyectos desde el disco."""
        self.project_selector.blockSignals(True)
        cur = self.project_selector.currentText()
        self.project_selector.clear()
        names = _list_projects()
        if names:
            self.project_selector.addItems(names)
            idx = self.project_selector.findText(cur)
            if idx >= 0:
                self.project_selector.setCurrentIndex(idx)
            else:
                self.project_selector.setCurrentIndex(0)
                self._load_project_data(names[0])
        else:
            self.project_selector.addItem("(ninguno)")
        self.project_selector.blockSignals(False)

    def _on_project_selected(self, choice):
        """Maneja el evento de seleccionar un proyecto en el combo."""
        if choice in ("(ninguno)", ""): return
        self._save_current(silent=True)
        self._load_project_data(choice)

    def _new_project(self):
        """Crea un proyecto nuevo (limpia los datos actuales)."""
        self._save_current(silent=True)
        self.project_name_input.clear()
        self.exams = []
        self.classrooms = []
        self._selected_classroom_idx = None
        self._dirty = False
        self._dirty_label.setText("")
        self._rebuild_exam_list()
        self._rebuild_classroom_list()
        self._refresh_slot_panel()
        self._update_stats()
        self.project_name_input.setText("Nuevo proyecto")
        self._mark_dirty()
        self.toast.show("Nuevo proyecto creado")

    def _save_current(self, silent=False):
        """Guarda el proyecto actual en un archivo JSON."""
        name = self.project_name_input.text().strip()
        if not name:
            self.toast.show("Escribe un nombre para guardar", "warning"); return
        _save_project(name, self.classrooms, self.exams)
        self._dirty = False
        self._dirty_label.setText("")
        self._refresh_project_list()
        if not silent:
            self.toast.show(f"Proyecto «{name}» guardado")

    def _delete_project(self):
        """Elimina el proyecto seleccionado."""
        name = self.project_selector.currentText()
        if name in ("(ninguno)", ""): return
        reply = QMessageBox.question(self, "Confirmar", f"¿Eliminar el proyecto «{name}»?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            _delete_project_file(name)
            self._refresh_project_list()
            self.toast.show("Proyecto eliminado")

    def _load_project_data(self, name):
        """Carga los datos de un proyecto desde su archivo JSON."""
        try:
            data = _load_project(name)
        except Exception as e:
            self.toast.show(f"Error al cargar: {e}", "error"); return
        self.project_name_input.setText(data.get("name", name))
        self.classrooms = [dict(c) for c in data.get("classrooms", [])]
        self.exams = [dict(e) for e in data.get("exams", [])]
        self._selected_classroom_idx = 0 if self.classrooms else None
        self._dirty = False
        self._dirty_label.setText("")
        self._rebuild_exam_list()
        self._rebuild_classroom_list()
        self._refresh_slot_panel()
        self._update_stats()

    def _mark_dirty(self):
        """Marca el proyecto como teniendo cambios sin guardar."""
        if not self._dirty:
            self._dirty = True
            self._dirty_label.setText("⚠️ Sin guardar")
        self._update_stats()

    def _load_seed(self):
        """Carga los datos ficticios de ejemplo."""
        data = get_seed_data()
        self.project_name_input.setText(data["project_name"])
        self.classrooms = [dict(c) for c in data["classrooms"]]
        self.exams = [dict(e) for e in data["exams"]]
        self._selected_classroom_idx = 0 if self.classrooms else None
        self._rebuild_exam_list()
        self._rebuild_classroom_list()
        self._refresh_slot_panel()
        self._mark_dirty()
        self.toast.show("Datos ficticios cargados (5 días, 6 aulas, 16 exámenes)")

    # ── Generar calendario (con múltiples opciones) ────────────────────

    def _generate(self):
        """
        Genera múltiples opciones de calendario y deja que el usuario
        elija la que prefiera antes de mostrarla.
        
        Flujo:
        1. Validar datos de entrada
        2. Crear el scheduler y construir el modelo CP-SAT
        3. Generar 3 soluciones alternativas
        4. Mostrar un diálogo con las opciones para que el usuario elija
        5. Exportar a HTML y mostrar la opción seleccionada
        """
        # ── Validación ──
        if not self.exams:
            self.toast.show("Añade al menos un examen", "warning"); return
        if not self.classrooms:
            self.toast.show("Añade al menos un aula", "warning"); return
        total_slots = sum(len(c.get("time_slots", [])) for c in self.classrooms)
        if total_slots == 0:
            self.toast.show("Las aulas necesitan franjas horarias", "warning"); return

        pname = self.project_name_input.text().strip() or "(sin nombre)"

        # ── Log inicial ──
        self._log(f"\n{'='*60}")
        self._log(f"🚀 Proyecto: {pname}")
        self._log(f"🏫 Aulas: {len(self.classrooms)}  |  🗓 Franjas totales: {total_slots}")
        self._log(f"📋 Exámenes: {len(self.exams)}  |  👥 Alumnos: {sum(e['students'] for e in self.exams)}  |  📚 Estudios: {len({e['study'] for e in self.exams})}")

        # ── Crear scheduler ──
        scheduler = ExamScheduler(self.exams, self.classrooms)
        self._log(f"🔢 Franjas únicas (fecha+hora): {scheduler.num_slots}")
        self._log("🧠 Construyendo modelo CP-SAT...")
        scheduler.build_model()

        # ── Generar múltiples soluciones ──
        self._log("🔄 Generando múltiples opciones...")
        solutions = scheduler.generate_multiple_solutions(num_options=3, time_limit=15)

        if not solutions:
            self._log("❌ Sin solución posible. Añade más franjas o aulas.")
            self.toast.show("Sin solución posible", "error"); return

        # ── Mostrar opciones encontradas ──
        self._log(f"\n✅ {len(solutions)} opciones generadas:")
        for idx, slots_used, _ in solutions:
            self._log(f"   Opción {idx}: {slots_used} franjas usadas")

        # ── Si solo hay una, se usa directamente ──
        if len(solutions) == 1:
            self._log("ℹ️ Solo una opción disponible, se muestra directamente.")
            chosen_idx, chosen_slots, chosen_assignment = solutions[0]
        else:
            # ── Mostrar diálogo de selección ──
            self._log("🗳️ Esperando que el usuario seleccione una opción...")
            chosen = self._show_solution_selector(solutions)
            if chosen is None:
                self._log("❌ El usuario canceló la selección.")
                self.toast.show("Selección cancelada", "warning"); return
            chosen_idx, chosen_slots, chosen_assignment = chosen
            self._log(f"✅ Opción {chosen_idx} seleccionada ({chosen_slots} franjas)")

        # ── Guardar asignación ──
        self.last_assignment = chosen_assignment

        # ── Log detallado ──
        self._log(f"\n📊 Detalle de la opción {chosen_idx}:")
        self._log(f"   Franjas usadas: {chosen_slots} de {scheduler.num_slots}")
        for a in sorted(chosen_assignment, key=lambda x: (x["slot"], x["classroom"]["name"])):
            self._log(f"   🕐 {a['slot_label']}  |  🏫 {a['classroom']['name']:20s}  |  📝 {a['exam']['name'][:40]:40s}  |  👥 {a['exam']['students']} alumnos")

        # ── Exportar a HTML ──
        out_dir = os.path.join(BASE_DIR, "output")
        os.makedirs(out_dir, exist_ok=True)
        safe = re.sub(r"[^a-zA-Z0-9_\-]", "_", pname)
        filename = f"{safe}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_opcion{chosen_idx}.html"
        path = os.path.join(out_dir, filename)
        export_html_file(pname, scheduler.global_slots, self.exams, self.classrooms,
                         chosen_assignment, scheduler.num_slots, path)
        self.last_html_path = path
        self._log(f"\n✅ HTML exportado: {path}")
        self.toast.show(f"✅ Calendario generado (Opción {chosen_idx})")

        # ── Mostrar en la pestaña de calendario ──
        self.tabs.setCurrentIndex(4)
        self._update_calendar_tab(chosen_slots, scheduler.num_slots)

    def _show_solution_selector(self, solutions):
        """
        Muestra un diálogo para que el usuario elija entre las opciones.
        
        Parámetros:
            solutions: lista de (índice, slots_usados, asignación)
        
        Devuelve:
            La tupla seleccionada, o None si el usuario canceló.
        """
        dialog = QDialog(self)
        dialog.setWindowTitle("🎯 Selecciona una Opción de Calendario")
        dialog.setMinimumWidth(550)
        dialog.setMinimumHeight(400)

        layout = QVBoxLayout(dialog)
        layout.setSpacing(12)

        # Título
        titulo = QLabel("🎯  Se han generado varias opciones de calendario")
        titulo.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(titulo)

        subtitulo = QLabel("Selecciona la que prefieras para ver los detalles:")
        subtitulo.setStyleSheet("color: #94a3b8; font-size: 12px;")
        layout.addWidget(subtitulo)

        # Lista de opciones
        lista = QListWidget()
        lista.setStyleSheet("""
            QListWidget {
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 4px;
                font-size: 13px;
            }
            QListWidget::item {
                padding: 12px 16px;
                border-bottom: 1px solid #1e293b;
            }
            QListWidget::item:selected {
                background: #1e3a5f;
                color: white;
            }
        """)

        for idx, slots_used, assignment in solutions:
            n_exams = len({a["exam"]["name"] for a in assignment})
            classroom_usage = {}
            for a in assignment:
                cn = a["classroom"]["name"]
                classroom_usage[cn] = classroom_usage.get(cn, 0) + 1

            usage_str = "  |  ".join(
                f"🏫 {cn}: {count} exámenes"
                for cn, count in sorted(classroom_usage.items())
            )

            item_text = (
                f"📅 Opción {idx}  —  🗓 {slots_used} franjas usadas  |  📋 {n_exams} exámenes\n"
                f"   {usage_str}"
            )
            item = QListWidgetItem(item_text)
            item.setData(32, idx)
            lista.addItem(item)

        if lista.count() > 0:
            lista.setCurrentRow(0)

        layout.addWidget(lista)

        # Botones
        botones = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        botones.accepted.connect(dialog.accept)
        botones.rejected.connect(dialog.reject)

        ok_btn = botones.button(QDialogButtonBox.StandardButton.Ok)
        ok_btn.setText("✅ Mostrar esta opción")
        ok_btn.setStyleSheet(f"background: {C_PRI}; color: white; padding: 8px 20px; border-radius: 5px;")

        cancel_btn = botones.button(QDialogButtonBox.StandardButton.Cancel)
        cancel_btn.setText("❌ Cancelar")
        cancel_btn.setStyleSheet("background: #475569; color: white; padding: 8px 20px; border-radius: 5px;")

        layout.addWidget(botones)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected_row = lista.currentRow()
            if selected_row >= 0 and selected_row < len(solutions):
                return solutions[selected_row]

        return None

    def _log(self, msg):
        """Añade un mensaje al log de la pestaña Generar."""
        self.status_text.append(msg)
        sb = self.status_text.verticalScrollBar()
        sb.setValue(sb.maximum())

    # ── Actualizar pestaña de calendario ───────────────────────────────

    def _update_calendar_tab(self, slots_used=None, total_slots=None):
        """Muestra el calendario generado en la pestaña correspondiente."""
        while self.cal_layout.count():
            item = self.cal_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        if not self.last_assignment:
            return

        self.open_btn.setEnabled(True)
        self.open_folder_btn.setEnabled(True)

        a = self.last_assignment
        n = slots_used or len({x["slot"] for x in a})
        studies = sorted({e["study"] for e in self.exams})
        total_students = sum(e["students"] for e in self.exams)
        self.cal_summary.setText(f"📋 {len(self.exams)} exámenes · {n} franjas · "
                                 f"🏫 {len(self.classrooms)} aulas · {total_students} alumnos · {len(studies)} estudios")

        # Agrupar asignaciones por franja
        groups = {}
        for x in sorted(a, key=lambda x: (x["slot"], x["classroom"]["name"])):
            groups.setdefault(x["slot"], []).append(x)

        # Mostrar cada franja como una tarjeta
        for t in sorted(groups.keys()):
            slot_card = QFrame()
            slot_card.setObjectName("card")
            slot_card.setStyleSheet("")
            slot_card_v = QVBoxLayout(slot_card)
            slot_card_v.setContentsMargins(12, 10, 12, 10)
            slot_card_v.setSpacing(6)

            label_text = groups[t][0]["slot_label"] if groups[t] else f"Franja {t+1}"
            header = QLabel(f"🕐 {label_text}")
            header.setStyleSheet(f"font-weight: bold; font-size: 14px; color: {C_PRI};")
            slot_card_v.addWidget(header)

            items_frame = QFrame()
            items_frame.setStyleSheet("")
            items_lay = QVBoxLayout(items_frame)
            items_lay.setContentsMargins(0, 0, 0, 0)
            items_lay.setSpacing(4)

            for x in sorted(groups[t], key=lambda x: x["classroom"]["name"]):
                c = self._study_color(x["exam"]["study"])
                card = QFrame()
                card.setObjectName("slot_row")
                card.setStyleSheet("")
                row = QHBoxLayout(card)
                row.setContentsMargins(10, 4, 10, 4)
                info = QLabel(f"🏫 {x['classroom']['name']:15s}  |  📝 {x['exam']['name']:35s}  |  👥 {x['exam']['students']} alumnos  |  📚 {x['exam']['study']}")
                row.addWidget(info, 1)
                items_lay.addWidget(card)

            slot_card_v.addWidget(items_frame)
            self.cal_layout.addWidget(slot_card)

    # ── Abrir HTML ─────────────────────────────────────────────────────

    def _open_html(self):
        """Abre el HTML generado en el navegador web."""
        if self.last_html_path and os.path.exists(self.last_html_path):
            webbrowser.open(f"file://{os.path.abspath(self.last_html_path)}")

    def _open_folder(self):
        """Abre la carpeta que contiene el HTML generado."""
        if self.last_html_path:
            os.startfile(os.path.dirname(os.path.abspath(self.last_html_path)))
