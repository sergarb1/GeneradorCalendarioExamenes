# Copyright (C) 2026 Sergi Albuixech
# SPDX-License-Identifier: AGPL-3.0-or-later

import json, os, re, webbrowser, copy
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QPushButton, QLineEdit, QComboBox,
    QTabWidget, QScrollArea, QFrame, QTextEdit, QSizePolicy,
    QMessageBox, QDateEdit, QDialog, QFormLayout, QDialogButtonBox,
    QListWidget, QListWidgetItem, QFileDialog, QProgressBar, QMenu
)
from PyQt6.QtCore import Qt, QTimer, QDate, pyqtSignal, QThread, QObject, QMimeData
from PyQt6.QtGui import QFont, QAction, QDrag, QShortcut, QKeySequence

from ortools.sat.python import cp_model
from scheduler import ExamScheduler
from html_exporter import export_html_file
from word_exporter import export_calendar_to_word, export_exams_to_word
from md_exporter import export_calendar_to_md, export_exams_to_md
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
QPushButton#danger {{ background: transparent; color: {C_RED}; border: 1px solid #fecaca; font-size: 12px; }}
QPushButton#danger:hover {{ background: #fef2f2; border-color: {C_RED}; }}
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
QPushButton#danger {{ background: transparent; color: #f87171; border: 1px solid {C_BORDER_D}; font-size: 12px; }}
QPushButton#danger:hover {{ background: #1c1010; border-color: #f87171; }}
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
# WORKER SolverWorker — ejecuta el solver en un hilo separado
# ══════════════════════════════════════════════════════════════════════════

class SolverWorker(QObject):
    """Ejecuta el scheduler CP-SAT en un QThread para no bloquear la UI."""
    finished = pyqtSignal(object, object, object)  # scheduler, solutions, pname
    error = pyqtSignal(str)
    log = pyqtSignal(str)

    def __init__(self, exams, classrooms, num_options, locked_assignments=None):
        super().__init__()
        self.exams = exams
        self.classrooms = classrooms
        self.num_options = num_options
        self.locked_assignments = locked_assignments or {}

    def run(self):
        try:
            self.log.emit(f"\n{'='*60}")
            self.log.emit(f"🏫 Aulas: {len(self.classrooms)} | 📋 Exámenes: {len(self.exams)}")
            self.log.emit(f"🔢 Opciones: {self.num_options}")

            # Copia profunda para evitar problemas de concurrencia
            exams_copy = copy.deepcopy(self.exams)
            classrooms_copy = copy.deepcopy(self.classrooms)
            locks_copy = copy.deepcopy(self.locked_assignments)

            scheduler = ExamScheduler(exams_copy, classrooms_copy)
            self.log.emit(f"🔢 Franjas únicas: {scheduler.num_slots}")
            self.log.emit("🧠 Construyendo modelo CP-SAT...")
            scheduler.build_model()

            if locks_copy:
                self.log.emit(f"🔒 Aplicando {len(locks_copy)} bloqueos...")
                scheduler.add_locked_assignments(locks_copy)

            self.log.emit("🔄 Generando múltiples opciones...")
            solutions = scheduler.generate_multiple_solutions(
                num_options=self.num_options, time_limit=15
            )

            if not solutions:
                self.error.emit("Sin solución posible")
                return

            self.log.emit(f"\n✅ {len(solutions)} opciones generadas:")
            for idx, slots_used, _ in solutions:
                self.log.emit(f"   Opción {idx}: {slots_used} franjas usadas")

            self.finished.emit(scheduler, solutions, "")
        except Exception as e:
            self.error.emit(str(e))

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
        self.generated_solutions = []      # Lista de (idx, slots_usados, asignacion)
        self.generated_paths = {}          # idx -> ruta del HTML
        self.current_option_idx = 0        # Índice de la opción mostrada actualmente
        self._dirty = False                # ¿Hay cambios sin guardar?
        self._selected_classroom_idx = None  # Índice del aula seleccionada
        self._dark_mode = False            # Modo oscuro activado?
        self._undo_stack = []              # Pila para deshacer
        self._redo_stack = []              # Pila para rehacer
        self._last_scheduler = None        # Último scheduler usado
        self._locked_assignments = {}      # exam_idx -> (slot_idx, classroom_idx)
        self._solving = False              # ¿Se está ejecutando el solver?
        self._exam_filter = ""             # Texto de filtro de exámenes
        self._classroom_filter = ""        # Texto de filtro de aulas
        self._cal_filter = ""              # Texto de filtro del calendario

        # Auto-guardado cada 5 minutos
        self._auto_save_timer = QTimer(self)
        self._auto_save_timer.timeout.connect(self._auto_save)
        self._auto_save_timer.start(300000)

        # Construir la interfaz
        self._build_ui()
        self._load_config()
        self._apply_theme()
        self._refresh_project_list()
        self._rebuild_classroom_list()
        self._rebuild_exam_list()
        self._update_stats()

    # ── Configuración persistente ───────────────────────────────────────

    CONFIG_PATH = os.path.join(BASE_DIR, "config.json")

    def _load_config(self):
        """Carga la configuración persistente (tema, etc.)."""
        try:
            if os.path.exists(self.CONFIG_PATH):
                with open(self.CONFIG_PATH, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                self._dark_mode = cfg.get("dark_mode", False)
        except Exception:
            pass

    def _save_config(self):
        """Guarda la configuración persistente."""
        try:
            with open(self.CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump({"dark_mode": self._dark_mode}, f)
        except Exception:
            pass

    # ── Tema (claro/oscuro) ─────────────────────────────────────────────

    def _apply_theme(self):
        """Aplica el tema claro u oscuro según _dark_mode."""
        qss = DARK_QSS if self._dark_mode else LIGHT_QSS
        QApplication.instance().setStyleSheet(qss)
        self.theme_btn.setText("☀️ Claro" if self._dark_mode else "🌙 Oscuro")
        self.header_bar.setStyleSheet(f"background: {C_PRI}; border-radius: 0;")
        sb_bg = "#0f172a" if self._dark_mode else "#f1f5f9"
        sb_fg = "#94a3b8" if self._dark_mode else "#64748b"
        self.status_bar.setStyleSheet(f"background: {sb_bg}; border-top: 1px solid {C_BORDER};")
        self.status_label.setStyleSheet(f"font-size: 11px; color: {sb_fg};")

    def _toggle_theme(self):
        """Cambia entre modo claro y oscuro."""
        self._dark_mode = not self._dark_mode
        self._apply_theme()
        self._save_config()

    # ── Ayuda / Tips ─────────────────────────────────────────────────────

    def _show_help(self):
        """Muestra un diálogo con tips y ayuda detallada sobre la aplicación."""
        dlg = QDialog(self)
        dlg.setWindowTitle("❔ Ayuda y Tips")
        dlg.setMinimumSize(660, 640)
        dlg.resize(720, 700)
        tc = C_TEXT2_D if self._dark_mode else C_TEXT2
        v = QVBoxLayout(dlg)
        v.setSpacing(8)

        title = QLabel("📅🎓 Tips y Ayuda — Generador de Calendario de Exámenes")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: " + C_PRI + ";")
        v.addWidget(title)

        subtitle = QLabel("Consejos rápidos para usar la aplicación. Pulsa el ❔ de la barra superior para volver a ver esto.")
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("font-size: 12px; color: " + tc + "; margin-bottom: 6px;")
        v.addWidget(subtitle)

        sections = [
            ("🚀 Flujo de trabajo (orden recomendado)",
             [
                 "1️⃣ 🏠 Proyecto → Crea o carga un proyecto (o usa datos de ejemplo).",
                 "2️⃣ 📋 Exámenes → Añade todos los exámenes (nombre, alumnos, estudio).",
                 "3️⃣ 🏫 Aulas → Define aulas con capacidad y franjas horarias.",
                 "4️⃣ ⚙️ Generar → Elige nº de opciones (5 es ideal) y pulsa el botón.",
                 "5️⃣ 📅 Calendario → Explora opciones, bloquea exámenes, exporta.",
                 "💡 No hace falta hacer todo seguido: guarda el proyecto y continúa después.",
             ]),
            ("💡 Tips generales",
             [
                 "🌙☀️ Cambia de tema con el botón en la barra superior (oscuro para la noche, claro para proyectores).",
                 "💾 Auto-guardado cada 5 minutos si hay cambios. También puedes guardar manualmente en Proyecto.",
                 "↩️ Deshacer/Rehacer: hasta 50 cambios atrás. Perfecto si eliminas algo por error.",
                 "📤 Exporta/importa exámenes y aulas por separado (JSON) para compartir con compañeros.",
                 "🔍 Los filtros de búsqueda no distinguen mayúsculas y buscan en nombre y estudio.",
                 "📊 Revisa Estadísticas en Proyecto antes de generar para detectar desequilibrios.",
             ]),
            ("🧠 Tips sobre el solver (cómo piensa)",
             [
                 "🎯 Objetivo: minimizar el número de franjas usadas. Tiende a concentrar exámenes.",
                 "🔒 Exámenes del MISMO ESTUDIO nunca coinciden en la misma franja (restricción dura).",
                 "👨‍🏫 Exámenes del MISMO PROFESOR nunca coinciden en la misma franja (aunque sean de distintos estudios).",
                 "🌅 La preferencia de turno es BLANDA: el solver la respeta si puede, pero no es obligatorio.",
                 "❌ Si no encuentra solución, suele ser por: pocas franjas, aulas pequeñas, o bloqueos incompatibles.",
                 "⏳ Límite de 15 segundos por opción. Si tarda más, reduce opciones o simplifica los datos.",
                 "💡 Estudios con nombres inconsistentes (ej. 'Informática (GS)' vs 'Informática(GS)') se tratan como distintos.",
             ]),
            ("🔒 Tips sobre bloqueos",
             [
                 "🔓 → 🔒 Pulsa el candado abierto junto a un examen para fijarlo a su franja/aula.",
                 "🟡 Los exámenes bloqueados se marcan con borde dorado para identificarlos.",
                 "🔄 'Regenerar con bloqueos' recoloca el resto manteniendo los bloqueados.",
                 "⚠️ Bloquear demasiados exámenes puede hacer que no haya solución. El solver te avisará.",
                 "🧹 'Limpiar bloqueos' desbloquea todos de golpe.",
                 "💡 Útil para: fijar exámenes con necesidades especiales (aula con ordenadores, profesor solo por la mañana...).",
             ]),
            ("👨‍🏫 Tips sobre profesores",
             [
                 "✏️ El campo profesor es opcional. Si lo rellenas, el solver evita solapamientos.",
                 "🔗 Funciona entre estudios: un profesor de Informática y Administración no tendrá dos exámenes a la vez.",
                 "📝 Los nombres se comparan exactamente (mayúsculas incluidas). Sé consistente.",
                 "👥 Si no pones profesor en ningún examen, no hay restricción de profesor.",
                 "💡 Pon el mismo profesor en exámenes de distintos estudios para asegurar que no coincidan.",
             ]),
            ("📊 Tips sobre el calendario",
             [
                 "📌 Selector de opciones: cambia entre las diferentes soluciones generadas.",
                 "📋 Vista detalle (tarjetas) vs Vista completa (tabla): alterna según necesites.",
                 "🔀 Comparativa: dos opciones lado a lado para elegir la mejor distribución.",
                 "🖨️ HTML imprimible: incluye colores, leyenda y nombre del proyecto.",
                 "📋 CSV: ábrelo en Excel o Google Sheets para filtrar y ordenar.",
                 "🖼️ PNG: captura lo que ves en pantalla (cambia a vista completa para capturar la tabla completa).",
                 "💡 Cada examen se muestra con el color de su estudio. Si pusiste color personalizado, ese prevalece.",
             ]),
            ("🌐 Enlaces útiles",
             [
                 "📘 Manual completo (presentación interactiva): https://sergarb1.github.io/GeneradorCalendarioExamenes/manual.html",
                 "🐙 Repositorio GitHub: https://github.com/sergarb1/GeneradorCalendarioExamenes",
                 "🌐 GitHub Pages: https://sergarb1.github.io/GeneradorCalendarioExamenes/",
                 "📄 Documentación del proyecto: index.html (en la carpeta del proyecto)",
             ]),
        ]

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")
        inner = QWidget()
        inner_layout = QVBoxLayout(inner)
        inner_layout.setSpacing(6)
        inner_layout.setContentsMargins(0, 0, 0, 0)

        for icon_title, tips in sections:
            lbl = QLabel(icon_title)
            lbl.setStyleSheet("font-size: 14px; font-weight: 600; margin-top: 8px; color: " + C_PRI + ";")
            inner_layout.addWidget(lbl)
            for tip in tips:
                tb = QLabel(tip)
                tb.setWordWrap(True)
                tb.setStyleSheet("font-size: 12px; color: " + tc + "; padding-left: 14px; line-height: 1.5;")
                inner_layout.addWidget(tb)

        inner_layout.addStretch()
        scroll.setWidget(inner)
        v.addWidget(scroll)

        btn_close = QPushButton("Cerrar")
        btn_close.setStyleSheet(f"background: {C_PRI}; color: white; border: none; padding: 8px 24px; border-radius: 5px; font-weight: 600;")
        btn_close.clicked.connect(dlg.accept)
        hb = QHBoxLayout()
        hb.addStretch()
        hb.addWidget(btn_close)
        v.addLayout(hb)
        dlg.exec()

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

        self.help_btn = QPushButton("❔ Ayuda")
        self.help_btn.setFixedSize(90, 30)
        self.help_btn.setStyleSheet("background: rgba(255,255,255,0.2); color: white; border: 1px solid rgba(255,255,255,0.3); border-radius: 4px;")
        self.help_btn.clicked.connect(self._show_help)
        hdr_lay.addWidget(self.help_btn)

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

        # ─── Barra de estado ───
        self.status_bar = QFrame()
        self.status_bar.setFixedHeight(28)
        sb_lay = QHBoxLayout(self.status_bar)
        sb_lay.setContentsMargins(12, 0, 12, 0)
        self.status_label = QLabel("")
        self.status_label.setStyleSheet(f"font-size: 11px; color: {C_SLATE};")
        sb_lay.addWidget(self.status_label, 1)
        main_v.addWidget(self.status_bar)

        # Toast (notificaciones emergentes)
        self.toast = Toast(self)

        # Atajos de teclado
        self._setup_shortcuts()

    def _setup_shortcuts(self):
        """Configura los atajos de teclado globales."""
        QShortcut(QKeySequence("Ctrl+Z"), self, self._undo)
        QShortcut(QKeySequence("Ctrl+Shift+Z"), self, self._redo)
        QShortcut(QKeySequence("Ctrl+S"), self, self._save_current)
        QShortcut(QKeySequence("Ctrl+G"), self, self._generate)

        # Ctrl+1-5 para cambiar de pestaña
        for i in range(5):
            QShortcut(QKeySequence(f"Ctrl+{i+1}"), self, lambda idx=i: self.tabs.setCurrentIndex(idx))

        # Ctrl+E → pestaña Exámenes, Ctrl+A → pestaña Aulas
        QShortcut(QKeySequence("Ctrl+E"), self, lambda: self.tabs.setCurrentIndex(1))
        QShortcut(QKeySequence("Ctrl+A"), self, lambda: self.tabs.setCurrentIndex(2))

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

    def _mkbtn(self, text, cmd, color=None):
        """Crea un QPushButton con comando y estilo opcional."""
        b = QPushButton(text)
        b.clicked.connect(cmd)
        if color: b.setObjectName(color)
        return b

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

        # Fila 1: selector de proyectos
        sel = QHBoxLayout()
        self.project_selector = QComboBox()
        self.project_selector.setMinimumWidth(300)
        self.project_selector.currentTextChanged.connect(self._on_project_selected)
        sel.addWidget(self.project_selector)
        sel.addWidget(self._mkbtn("➕ Nuevo", self._new_project, "secondary"))
        sel.addWidget(self._mkbtn("💾 Guardar", self._save_current))
        sel.addWidget(self._mkbtn("🗑️ Eliminar", self._delete_project, "danger"))
        sel.addWidget(self._mkbtn("📦 Cargar datos ficticios", self._load_seed, "secondary"))
        v.addLayout(sel)

        # Fila 2: nombre del proyecto
        name_row = QHBoxLayout()
        name_row.addWidget(QLabel("📛 Nombre:"))
        self.project_name_input = QLineEdit()
        self.project_name_input.setPlaceholderText("Nombre del proyecto...")
        self.project_name_input.textChanged.connect(lambda: self._mark_dirty())
        name_row.addWidget(self.project_name_input, 1)
        v.addLayout(name_row)

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

        self._dirty_label = QLabel("")
        self._dirty_label.setStyleSheet(f"color: {C_ACCENT};")
        v.addWidget(self._dirty_label)

        # Fila inferior: acciones
        bf = QHBoxLayout()
        bf.addWidget(self._mkbtn("📤 Exportar todo", self._export_all, "secondary"))
        bf.addWidget(self._mkbtn("📥 Importar todo", self._import_all, "secondary"))
        bf.addWidget(self._mkbtn("↩️ Deshacer", self._undo, "secondary"))
        bf.addWidget(self._mkbtn("↪️ Rehacer", self._redo, "secondary"))
        bf.addWidget(self._mkbtn("📊 Estadísticas", self._show_stats, "secondary"))
        bf.addStretch()
        v.addLayout(bf)

        v.addWidget(self._sep())

        # Flujo de trabajo
        v.addWidget(QLabel("💡 Flujo de trabajo — pasos:"))
        info = QLabel(
            "1. 📋 Crea o selecciona un proyecto\n"
            "2. 📝 Añade exámenes: nombre, alumnos, estudio, color, turno\n"
            "3. 🏫 Añade aulas con capacidad y franjas disponibles\n"
            "4. ⚙️ Genera el calendario — el solver CP-SAT asigna todo\n"
            "5. 📅 Explora opciones, bloquea, exporta a HTML/CSV/PNG"
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
        self.ex_study = QLineEdit(); self.ex_study.setPlaceholderText("Ciclo / materia"); self.ex_study.setFixedWidth(160)
        f.addWidget(self.ex_study)
        f.addSpacing(4)
        f.addWidget(QLabel("👨‍🏫 Profesor:"))
        self.ex_teacher = QLineEdit(); self.ex_teacher.setPlaceholderText("Nombre profesor"); self.ex_teacher.setFixedWidth(150)
        f.addWidget(self.ex_teacher)
        f.addSpacing(6)
        self.ex_color_btn = QPushButton()
        self.ex_color_btn.setFixedSize(28, 28)
        self.ex_color_btn.setStyleSheet(f"background: {C_PRI}; border-radius: 4px; border: 1px solid {C_BORDER};")
        self.ex_color_btn.setToolTip("Color del estudio (clic para cambiar)")
        self.ex_color_btn.clicked.connect(self._pick_exam_color)
        f.addWidget(self.ex_color_btn)
        f.addSpacing(6)
        f.addWidget(QLabel("🕐 Turno:"))
        self.ex_shift = QComboBox()
        self.ex_shift.addItems(["Cualquiera", "Mañana", "Tarde"])
        self.ex_shift.setFixedWidth(100)
        f.addWidget(self.ex_shift)
        f.addSpacing(6)
        b = QPushButton("➕ Añadir examen")
        b.clicked.connect(self._add_exam)
        f.addWidget(b)
        f.addStretch()
        v.addLayout(f)

        self.exam_count = QLabel("📋 0 exámenes")
        self.exam_count.setStyleSheet("font-weight: bold;")
        v.addWidget(self.exam_count)

        self.exam_placeholder = QLabel("📭 No hay exámenes.\nAñade exámenes desde el formulario superior o importa un archivo JSON.")
        self.exam_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.exam_placeholder.setStyleSheet(f"color: {C_SLATE}; font-size: 13px; padding: 30px;")
        v.addWidget(self.exam_placeholder)

        # Filtro de exámenes
        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("🔍 Filtrar:"))
        self.exam_filter_input = QLineEdit()
        self.exam_filter_input.setPlaceholderText("Buscar por nombre o estudio...")
        self.exam_filter_input.textChanged.connect(self._on_exam_filter_changed)
        filter_row.addWidget(self.exam_filter_input, 1)
        v.addLayout(filter_row)

        ie_row = QHBoxLayout()
        export_ex_btn = QPushButton("📤 Exportar JSON")
        export_ex_btn.setObjectName("secondary")
        export_ex_btn.clicked.connect(self._export_exams)
        ie_row.addWidget(export_ex_btn)
        import_ex_btn = QPushButton("📥 Importar JSON")
        import_ex_btn.setObjectName("secondary")
        import_ex_btn.clicked.connect(self._import_exams)
        ie_row.addWidget(import_ex_btn)
        export_ex_word_btn = QPushButton("📄 Exportar Word")
        export_ex_word_btn.setObjectName("secondary")
        export_ex_word_btn.clicked.connect(self._export_exams_word)
        ie_row.addWidget(export_ex_word_btn)
        export_ex_md_btn = QPushButton("📝 Exportar MD")
        export_ex_md_btn.setObjectName("secondary")
        export_ex_md_btn.clicked.connect(self._export_exams_md)
        ie_row.addWidget(export_ex_md_btn)
        ie_row.addStretch()
        v.addLayout(ie_row)

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

        # Filtro + export/import en una sola fila
        filter_row = QHBoxLayout()
        self.classroom_count = QLabel("🏫 0 aulas")
        self.classroom_count.setStyleSheet("font-weight: bold;")
        filter_row.addWidget(self.classroom_count)

        self.classroom_placeholder = QLabel("🏫 No hay aulas.\nDefine aulas con capacidad y franjas horarias desde el formulario superior.")
        self.classroom_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.classroom_placeholder.setStyleSheet(f"color: {C_SLATE}; font-size: 13px; padding: 30px;")
        v.addWidget(self.classroom_placeholder)
        filter_row.addSpacing(12)
        filter_row.addWidget(QLabel("🔍"))
        self.classroom_filter_input = QLineEdit()
        self.classroom_filter_input.setPlaceholderText("Buscar aula...")
        self.classroom_filter_input.setFixedWidth(160)
        self.classroom_filter_input.textChanged.connect(self._on_classroom_filter_changed)
        filter_row.addWidget(self.classroom_filter_input)

        export_cl_btn = QPushButton("📤 Exportar")
        export_cl_btn.setObjectName("secondary")
        export_cl_btn.clicked.connect(self._export_classrooms)
        filter_row.addWidget(export_cl_btn)
        import_cl_btn = QPushButton("📥 Importar")
        import_cl_btn.setObjectName("secondary")
        import_cl_btn.clicked.connect(self._import_classrooms)
        filter_row.addWidget(import_cl_btn)
        filter_row.addStretch()
        v.addLayout(filter_row)

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
        slot_row = QHBoxLayout()
        slot_row.setSpacing(4)
        self.slot_header = QLabel("📅 Franjas: (ningún aula seleccionada)")
        self.slot_header.setStyleSheet("font-weight: bold; font-size: 14px;")
        slot_row.addWidget(self.slot_header)
        slot_row.addStretch()
        fecha_lbl = QLabel("📅 Fecha:")
        slot_row.addWidget(fecha_lbl)
        self.slot_date = QDateEdit()
        self.slot_date.setCalendarPopup(True)
        self.slot_date.setDisplayFormat("yyyy-MM-dd")
        self.slot_date.setDate(datetime.strptime("2026-06-15", "%Y-%m-%d").date())
        self.slot_date.setFixedWidth(120)
        slot_row.addWidget(self.slot_date)
        slot_row.addSpacing(6)
        add_custom = QPushButton("➕ Personalizada")
        add_custom.clicked.connect(self._add_slot_custom)
        slot_row.addWidget(add_custom)
        for lbl, s, e in [("☕ Mañana 09-14h", "09:00", "14:00"),
                          ("🌤 Tarde 15-18h", "15:00", "18:00")]:
            b = QPushButton(lbl)
            b.clicked.connect(lambda checked, ss=s, ee=e: self._add_slot_preset(ss, ee))
            slot_row.addWidget(b)
        slot_row.addSpacing(8)
        save_tmpl = QPushButton("💾 Plantilla")
        save_tmpl.setObjectName("secondary")
        save_tmpl.clicked.connect(self._save_slot_template)
        slot_row.addWidget(save_tmpl)
        load_tmpl = QPushButton("📂 Plantilla")
        load_tmpl.setObjectName("secondary")
        load_tmpl.clicked.connect(self._load_slot_template)
        slot_row.addWidget(load_tmpl)
        slot_row.addStretch()
        v.addLayout(slot_row)

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

        self.gen_placeholder = QLabel("📭 No hay datos para generar.\nAñade exámenes y aulas desde las pestañas anteriores.")
        self.gen_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.gen_placeholder.setStyleSheet(f"color: {C_SLATE}; font-size: 13px; padding: 30px;")
        v.addWidget(self.gen_placeholder)

        opts_row = QHBoxLayout()
        opts_row.addWidget(QLabel("🔢 Nº de opciones a generar:"))
        self.num_options_spin = QLineEdit("5")
        self.num_options_spin.setFixedWidth(50)
        opts_row.addWidget(self.num_options_spin)
        opts_row.addStretch()
        v.addLayout(opts_row)

        gen_btn = QPushButton("🚀 Generar Calendario")
        gen_btn.setMinimumHeight(50)
        gen_btn.setStyleSheet(f"font-size: 18px; font-weight: bold; background: {C_PRI}; color: white; border-radius: 8px;")
        gen_btn.clicked.connect(self._generate)
        v.addWidget(gen_btn)

        # Indicador de progreso (oculto por defecto)
        self.gen_progress = QProgressBar()
        self.gen_progress.setRange(0, 0)  # modo indeterminado
        self.gen_progress.setFixedHeight(24)
        self.gen_progress.setTextVisible(False)
        self.gen_progress.hide()
        self.gen_progress_label = QLabel("⏳ Generando calendarios, un momento...")
        self.gen_progress_label.setStyleSheet(f"color: {C_PRI}; font-size: 14px; font-weight: bold;")
        self.gen_progress_label.hide()
        self._loading_dots = 0
        self._loading_timer = QTimer(self)
        self._loading_timer.timeout.connect(self._animate_loading)
        self._loading_messages = [
            "🧠 Analizando restricciones y datos de entrada...",
            "⚙️ Optimizando distribución de exámenes...",
            "📋 Generando opciones de calendario...",
            "💾 Exportando resultados a HTML...",
        ]
        self._loading_msg_idx = 0
        v.addWidget(self.gen_progress_label)
        v.addWidget(self.gen_progress)
        self.gen_btn = gen_btn

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
        v.setSpacing(6)

        # Fila superior: selector + acciones
        top_row = QHBoxLayout()
        self.option_selector = QComboBox()
        self.option_selector.setMinimumWidth(200)
        self.option_selector.currentIndexChanged.connect(self._on_option_changed)
        self.option_selector.setEnabled(False)
        top_row.addWidget(QLabel("📅 Opción:"))
        top_row.addWidget(self.option_selector)
        top_row.addStretch()
        self.cal_summary = QLabel("")
        self.cal_summary.setStyleSheet(f"color: {C_SLATE};")
        top_row.addWidget(self.cal_summary)
        v.addLayout(top_row)

        # Filtro de búsqueda en calendario
        cal_filter_row = QHBoxLayout()
        cal_filter_row.addWidget(QLabel("🔍 Filtrar:"))
        self.cal_filter_input = QLineEdit()
        self.cal_filter_input.setPlaceholderText("Buscar examen o estudio en el calendario...")
        self.cal_filter_input.textChanged.connect(self._on_cal_filter_changed)
        cal_filter_row.addWidget(self.cal_filter_input, 1)
        v.addLayout(cal_filter_row)

        self._compact_view = False
        self._compare_view = False

        # Segunda fila: botones de acción (se envuelven solos)
        action_row = QHBoxLayout()
        action_row.setSpacing(4)
        self.open_btn = QPushButton("🌐 Abrir en navegador")
        self.open_btn.setObjectName("secondary")
        self.open_btn.clicked.connect(self._open_html)
        self.open_btn.setEnabled(False)
        action_row.addWidget(self.open_btn)

        self.open_folder_btn = QPushButton("📂 Carpeta")
        self.open_folder_btn.setObjectName("secondary")
        self.open_folder_btn.clicked.connect(self._open_folder)
        self.open_folder_btn.setEnabled(False)
        action_row.addWidget(self.open_folder_btn)

        self.csv_btn = QPushButton("📋 CSV")
        self.csv_btn.setObjectName("secondary")
        self.csv_btn.clicked.connect(self._export_csv)
        self.csv_btn.setEnabled(False)
        action_row.addWidget(self.csv_btn)

        self.word_btn = QPushButton("📄 Word")
        self.word_btn.setObjectName("secondary")
        self.word_btn.clicked.connect(self._export_word)
        self.word_btn.setEnabled(False)
        action_row.addWidget(self.word_btn)

        self.md_btn = QPushButton("📝 MD")
        self.md_btn.setObjectName("secondary")
        self.md_btn.clicked.connect(self._export_md)
        self.md_btn.setEnabled(False)
        action_row.addWidget(self.md_btn)

        self.compact_view_btn = QPushButton("📊 Vista completa")
        self.compact_view_btn.setObjectName("secondary")
        self.compact_view_btn.clicked.connect(self._toggle_compact_view)
        self.compact_view_btn.setEnabled(False)
        action_row.addWidget(self.compact_view_btn)

        self.compare_view_btn = QPushButton("🔀 Comparar")
        self.compare_view_btn.setObjectName("secondary")
        self.compare_view_btn.clicked.connect(self._toggle_compare_view)
        self.compare_view_btn.setEnabled(False)
        action_row.addWidget(self.compare_view_btn)
        action_row.addStretch()
        v.addLayout(action_row)

        # Tercera fila: bloqueos
        lock_row = QHBoxLayout()
        self.clear_locks_btn = QPushButton("🔓 Limpiar bloqueos")
        self.clear_locks_btn.setObjectName("secondary")
        self.clear_locks_btn.clicked.connect(self._clear_locks)
        self.clear_locks_btn.setEnabled(False)
        lock_row.addWidget(self.clear_locks_btn)
        self.regenerate_locked_btn = QPushButton("🔒 Regenerar con bloqueos")
        self.regenerate_locked_btn.setStyleSheet(f"background: {C_PRI}; color: white; border: none; padding: 6px 14px; border-radius: 5px; font-size: 12px;")
        self.regenerate_locked_btn.clicked.connect(self._regenerate_with_locks)
        self.regenerate_locked_btn.setEnabled(False)
        lock_row.addWidget(self.regenerate_locked_btn)
        lock_row.addStretch()
        v.addLayout(lock_row)

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
        """Reconstruye la lista visual de aulas aplicando filtro."""
        while self.classroom_list_layout.count() > 1:
            item = self.classroom_list_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        ft = self._classroom_filter
        shown = 0
        for i, c in enumerate(self.classrooms):
            if ft and ft not in c["name"].lower():
                continue
            shown += 1
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
            del_lbl = QLabel("❌")
            del_lbl.setFixedSize(28, 24)
            del_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            del_lbl.setStyleSheet("background:#fee2e2; border:1px solid #ef4444; border-radius:3px; font-size:13px;")
            del_lbl.mousePressEvent = lambda e, idx=i: self._delete_classroom(idx)
            row.addWidget(del_lbl)

            self.classroom_list_layout.insertWidget(self.classroom_list_layout.count()-1, frame)

        self.classroom_count.setText(f"🏫 {shown}/{len(self.classrooms)} aulas")
        self.classroom_placeholder.setVisible(len(self.classrooms) == 0)

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
            ic = QLabel("🕐")
            ic.setStyleSheet("font-size:14px;")
            row.addWidget(ic)
            row.addSpacing(4)
            row.addWidget(QLabel(_fmt_slot(s)))
            del_lbl = QLabel("❌")
            del_lbl.setFixedSize(28, 24)
            del_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            del_lbl.setStyleSheet("background:#fee2e2; border:1px solid #ef4444; border-radius:3px; font-size:13px;")
            del_lbl.mousePressEvent = lambda e, ref=s: self._delete_slot(ref)
            row.addWidget(del_lbl)
            row.addStretch()
            self.slot_layout.insertWidget(self.slot_layout.count()-1, frame)

    # ── Lista de exámenes ──────────────────────────────────────────────

    def _rebuild_exam_list(self):
        """Reconstruye la lista visual de exámenes aplicando filtro."""
        while self.exam_layout.count() > 1:
            item = self.exam_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        ft = self._exam_filter
        filtered = [e for e in self.exams if not ft or ft in e["name"].lower() or ft in e["study"].lower()]

        for e in filtered:
            frame = QFrame()
            frame.setObjectName("exam_row")
            row = QHBoxLayout(frame)
            row.setContentsMargins(10, 4, 10, 4)
            color = e.get("color", self._study_color(e["study"]))
            dot = QLabel("●")
            dot.setStyleSheet(f"color: {color}; font-size: 18px;")
            dot.setFixedWidth(20)
            row.addWidget(dot)
            shift_icon = {"morning": "🌅", "afternoon": "🌇"}.get(e.get("preferred_shift", ""), "")
            teacher = e.get("teacher", "")
            dsp = f"👥 {e['students']}  |  📚 {e['study']}"
            dsp += f"  |  👨‍🏫 {teacher}" if teacher else ""
            dsp += f"  |  {shift_icon}" if shift_icon else ""
            lbl = QLabel(f"<b>{e['name']}</b>  —  {dsp}")
            lbl.setTextFormat(Qt.TextFormat.RichText)
            row.addWidget(lbl, 1)
            del_lbl = QLabel("❌")
            del_lbl.setFixedSize(28, 24)
            del_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            del_lbl.setStyleSheet("background:#fee2e2; border:1px solid #ef4444; border-radius:3px; font-size:13px;")
            del_lbl.mousePressEvent = lambda e, ref=e: self._delete_exam(ref)
            row.addWidget(del_lbl)
            self.exam_layout.insertWidget(self.exam_layout.count()-1, frame)

        self.exam_count.setText(f"📋 {len(filtered)}/{len(self.exams)} exámenes")
        self.exam_placeholder.setVisible(len(self.exams) == 0)

    # ── Estadísticas ───────────────────────────────────────────────────

    def _update_stats(self):
        """Actualiza las estadísticas y la barra de estado."""
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
        self.gen_placeholder.setVisible(len(self.exams) == 0 or len(self.classrooms) == 0)
        self._update_status()

    def _update_status(self):
        """Actualiza la barra de estado inferior."""
        parts = [f"📋 {len(self.exams)} exámenes", f"🏫 {len(self.classrooms)} aulas"]
        if self.exams:
            parts.append(f"👥 {sum(e['students'] for e in self.exams)} alumnos")
        if self._last_scheduler and self.last_assignment:
            n_slots = len({a["slot"] for a in self.last_assignment})
            parts.append(f"🕐 {n_slots} franjas")
            parts.append(f"🔢 {len(self.generated_solutions)} opciones")
        if self._dirty:
            parts.append("💾 *")
        self.status_label.setText(" · ".join(parts))

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

    def _pick_exam_color(self):
        """Muestra un selector de color para el examen."""
        colors = [C_PRI, "#ef4444", "#10b981", "#8b5cf6", C_ACCENT, "#06b6d4", "#ec4899", "#3b82f6", "#f97316", "#14b8a6"]
        d = QDialog(self)
        d.setWindowTitle("🎨 Color del estudio")
        g = QGridLayout(d)
        g.setSpacing(6)
        for i, c in enumerate(colors):
            btn = QPushButton()
            btn.setFixedSize(36, 36)
            btn.setStyleSheet(f"background: {c}; border-radius: 6px; border: 2px solid transparent;")
            btn.clicked.connect(lambda checked, cc=c: self._set_exam_color(cc, d))
            g.addWidget(btn, i // 5, i % 5)
        d.exec()

    def _set_exam_color(self, color, dialog):
        """Establece el color seleccionado y cierra el diálogo."""
        self.ex_color_btn.setStyleSheet(f"background: {color}; border-radius: 4px; border: 1px solid {C_BORDER};")
        self.ex_color_btn.setProperty("color", color)
        dialog.accept()

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
        color = self.ex_color_btn.property("color") or C_PRI
        shift_map = {"Mañana": "morning", "Tarde": "afternoon", "Cualquiera": ""}
        shift = shift_map[self.ex_shift.currentText()]
        teacher = self.ex_teacher.text().strip()
        self._save_state()
        exam = {"name": name, "students": students, "study": study, "color": color}
        if teacher:
            exam["teacher"] = teacher
        if shift:
            exam["preferred_shift"] = shift
        self.exams.append(exam)
        self._rebuild_exam_list()
        self._mark_dirty()
        self._update_stats()
        self.ex_name.clear()
        self.ex_study.clear()
        self.ex_teacher.clear()
        self.ex_shift.setCurrentIndex(0)
        self.ex_color_btn.setStyleSheet(f"background: {C_PRI}; border-radius: 4px; border: 1px solid {C_BORDER};")
        self.ex_color_btn.setProperty("color", C_PRI)
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
        self.generated_solutions = []
        self.generated_paths = {}
        self.option_selector.blockSignals(True)
        self.option_selector.clear()
        self.option_selector.setEnabled(False)
        self.option_selector.blockSignals(False)
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
        self._update_status()
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
        self.generated_solutions = []
        self.generated_paths = {}
        self.option_selector.blockSignals(True)
        self.option_selector.clear()
        self.option_selector.setEnabled(False)
        self.option_selector.blockSignals(False)
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
        self.generated_solutions = []
        self.generated_paths = {}
        self.option_selector.blockSignals(True)
        self.option_selector.clear()
        self.option_selector.setEnabled(False)
        self.option_selector.blockSignals(False)
        self._rebuild_exam_list()
        self._rebuild_classroom_list()
        self._refresh_slot_panel()
        self._mark_dirty()
        self.toast.show("Datos ficticios cargados (5 días, 6 aulas, 16 exámenes)")

    # ── Importar / Exportar ─────────────────────────────────────────────

    def _export_exams(self):
        """Exporta los exámenes a un archivo JSON."""
        if not self.exams:
            self.toast.show("No hay exámenes para exportar", "warning"); return
        path, _ = QFileDialog.getSaveFileName(self, "Exportar exámenes", "examenes.json", "JSON (*.json)")
        if not path: return
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.exams, f, ensure_ascii=False, indent=2)
            self.toast.show(f"✅ {len(self.exams)} exámenes exportados")
        except Exception as e:
            self.toast.show(f"Error al exportar: {e}", "error")

    def _import_exams(self):
        """Importa exámenes desde un archivo JSON."""
        path, _ = QFileDialog.getOpenFileName(self, "Importar exámenes", "", "JSON (*.json)")
        if not path: return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, list):
                self.toast.show("El archivo debe contener una lista de exámenes", "warning"); return
            self.exams.extend(data)
            self._rebuild_exam_list()
            self._mark_dirty()
            self.toast.show(f"✅ {len(data)} exámenes importados")
        except Exception as e:
            self.toast.show(f"Error al importar: {e}", "error")

    def _export_classrooms(self):
        """Exporta las aulas a un archivo JSON."""
        if not self.classrooms:
            self.toast.show("No hay aulas para exportar", "warning"); return
        path, _ = QFileDialog.getSaveFileName(self, "Exportar aulas", "aulas.json", "JSON (*.json)")
        if not path: return
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.classrooms, f, ensure_ascii=False, indent=2)
            self.toast.show(f"✅ {len(self.classrooms)} aulas exportadas")
        except Exception as e:
            self.toast.show(f"Error al exportar: {e}", "error")

    def _import_classrooms(self):
        """Importa aulas desde un archivo JSON."""
        path, _ = QFileDialog.getOpenFileName(self, "Importar aulas", "", "JSON (*.json)")
        if not path: return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, list):
                self.toast.show("El archivo debe contener una lista de aulas", "warning"); return
            self.classrooms.extend(data)
            self._rebuild_classroom_list()
            self._refresh_slot_panel()
            self._mark_dirty()
            self.toast.show(f"✅ {len(data)} aulas importadas")
        except Exception as e:
            self.toast.show(f"Error al importar: {e}", "error")

    def _export_all(self):
        """Exporta el proyecto completo (exámenes + aulas) a un archivo JSON."""
        if not self.exams and not self.classrooms:
            self.toast.show("No hay datos para exportar", "warning"); return
        name = self.project_name_input.text().strip() or "proyecto"
        path, _ = QFileDialog.getSaveFileName(self, "Exportar proyecto", f"{name}.json", "JSON (*.json)")
        if not path: return
        try:
            data = {"project_name": name, "classrooms": self.classrooms, "exams": self.exams}
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.toast.show("✅ Proyecto exportado")
        except Exception as e:
            self.toast.show(f"Error al exportar: {e}", "error")

    def _import_all(self):
        """Importa un proyecto completo desde un archivo JSON."""
        path, _ = QFileDialog.getOpenFileName(self, "Importar proyecto", "", "JSON (*.json)")
        if not path: return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if "exams" not in data or "classrooms" not in data:
                self.toast.show("El archivo debe contener 'exams' y 'classrooms'", "warning"); return
            self.exams = [dict(e) for e in data.get("exams", [])]
            self.classrooms = [dict(c) for c in data.get("classrooms", [])]
            self.project_name_input.setText(data.get("project_name", "Importado"))
            self._selected_classroom_idx = 0 if self.classrooms else None
            self.generated_solutions = []
            self.generated_paths = {}
            self.option_selector.blockSignals(True)
            self.option_selector.clear()
            self.option_selector.setEnabled(False)
            self.option_selector.blockSignals(False)
            self._rebuild_exam_list()
            self._rebuild_classroom_list()
            self._refresh_slot_panel()
            self._mark_dirty()
            self.toast.show("✅ Proyecto importado")
        except Exception as e:
            self.toast.show(f"Error al importar: {e}", "error")

    # ── Nuevas funcionalidades ─────────────────────────────────────────

    def _auto_save(self):
        """Auto-guarda el proyecto cada 5 minutos si hay cambios."""
        name = self.project_name_input.text().strip()
        if self._dirty and name and self.exams:
            _save_project(name, self.classrooms, self.exams)
            self._dirty = False
            self._dirty_label.setText("")

    def _save_state(self):
        """Guarda el estado actual para deshacer."""
        state = {
            "exams": [dict(e) for e in self.exams],
            "classrooms": [dict(c) for c in self.classrooms],
        }
        self._undo_stack.append(state)
        self._redo_stack.clear()
        if len(self._undo_stack) > 50:
            self._undo_stack.pop(0)

    def _undo(self):
        """Deshace la última acción."""
        if not self._undo_stack:
            self.toast.show("No hay acciones para deshacer", "warning"); return
        state = self._undo_stack.pop()
        self._redo_stack.append({
            "exams": [dict(e) for e in self.exams],
            "classrooms": [dict(c) for c in self.classrooms],
        })
        self.exams = [dict(e) for e in state["exams"]]
        self.classrooms = [dict(c) for c in state["classrooms"]]
        self._selected_classroom_idx = min(self._selected_classroom_idx, len(self.classrooms)-1) if self.classrooms else None
        self._rebuild_exam_list()
        self._rebuild_classroom_list()
        self._refresh_slot_panel()
        self._mark_dirty()
        self.toast.show("↩️ Deshecho")

    def _redo(self):
        """Rehace la última acción deshecha."""
        if not self._redo_stack:
            self.toast.show("No hay acciones para rehacer", "warning"); return
        state = self._redo_stack.pop()
        self._undo_stack.append({
            "exams": [dict(e) for e in self.exams],
            "classrooms": [dict(c) for c in self.classrooms],
        })
        self.exams = [dict(e) for e in state["exams"]]
        self.classrooms = [dict(c) for c in state["classrooms"]]
        self._selected_classroom_idx = min(self._selected_classroom_idx, len(self.classrooms)-1) if self.classrooms else None
        self._rebuild_exam_list()
        self._rebuild_classroom_list()
        self._refresh_slot_panel()
        self._mark_dirty()
        self.toast.show("↪️ Rehecho")

    def _validate_before_generate(self):
        """Valida que los datos sean coherentes antes de generar."""
        warnings = []
        total_slots = sum(len(c.get("time_slots", [])) for c in self.classrooms)
        total_capacity = sum(c["capacity"] for c in self.classrooms for _ in c.get("time_slots", []))
        total_students = sum(e["students"] for e in self.exams)

        if not self.exams:
            return "No hay exámenes. Añade al menos uno."
        if not self.classrooms:
            return "No hay aulas. Añade al menos una."
        if total_slots == 0:
            return "Las aulas no tienen franjas horarias."

        for e in self.exams:
            if e["students"] <= 0:
                warnings.append(f"⚠️ «{e['name']}» tiene 0 alumnos")
            if not e["study"].strip():
                warnings.append(f"⚠️ «{e['name']}» no tiene estudio asignado")

        for c in self.classrooms:
            if c["capacity"] <= 0:
                warnings.append(f"⚠️ «{c['name']}» tiene capacidad 0")

        if total_students > total_capacity:
            warnings.append(f"⚠️ {total_students} alumnos totales pero solo {total_capacity} plazas disponibles")

        studies_exams = {}
        for e in self.exams:
            studies_exams.setdefault(e["study"], []).append(e["name"])
        for study, exam_list in studies_exams.items():
            n_slots_avail = total_slots
            if len(exam_list) > n_slots_avail:
                warnings.append(f"⚠️ {study}: {len(exam_list)} exámenes pero solo {n_slots_avail} franjas")

        return warnings if warnings else None

    def _export_csv(self):
        """Exporta la asignación actual a CSV."""
        if not self.last_assignment:
            self.toast.show("Genera un calendario primero", "warning"); return
        path, _ = QFileDialog.getSaveFileName(self, "Exportar CSV", "calendario.csv", "CSV (*.csv)")
        if not path: return
        try:
            with open(path, "w", encoding="utf-8-sig") as f:
                f.write("Examen,Alumnos,Estudio,Fecha,Inicio,Fin,Aula\n")
                for a in sorted(self.last_assignment, key=lambda x: (x["slot"], x["classroom"]["name"])):
                    slot = a["slot_label"].split(" ")
                    date = slot[0] if len(slot) > 0 else ""
                    times = slot[1].split("-") if len(slot) > 1 else ["", ""]
                    f.write(f"{a['exam']['name']},{a['exam']['students']},{a['exam']['study']},{date},{times[0]},{times[1]},{a['classroom']['name']}\n")
            self.toast.show("✅ CSV exportado")
        except Exception as e:
            self.toast.show(f"Error al exportar CSV: {e}", "error")

    def _export_md(self):
        """Exporta el calendario actual a Markdown."""
        if not self.last_assignment:
            self.toast.show("Genera un calendario primero", "warning"); return
        path, _ = QFileDialog.getSaveFileName(self, "Exportar Markdown", "calendario.md", "Markdown (*.md)")
        if not path: return
        try:
            pname = self.project_name_input.text().strip() or ""
            export_calendar_to_md(self.last_assignment, self.exams, self.classrooms, path, pname)
            self.toast.show("✅ Markdown exportado")
        except Exception as e:
            self.toast.show(f"Error al exportar Markdown: {e}", "error")

    def _export_word(self):
        """Exporta el calendario actual a Word."""
        if not self.last_assignment:
            self.toast.show("Genera un calendario primero", "warning"); return
        path, _ = QFileDialog.getSaveFileName(self, "Exportar Word", "calendario.docx", "Word (*.docx)")
        if not path: return
        try:
            pname = self.project_name_input.text().strip() or ""
            export_calendar_to_word(self.last_assignment, self.exams, self.classrooms, path, pname)
            self.toast.show("✅ Word exportado")
        except Exception as e:
            self.toast.show(f"Error al exportar Word: {e}", "error")

    def _export_exams_word(self):
        """Exporta la lista de exámenes a Word."""
        if not self.exams:
            self.toast.show("No hay exámenes para exportar", "warning"); return
        path, _ = QFileDialog.getSaveFileName(self, "Exportar exámenes a Word", "examenes.docx", "Word (*.docx)")
        if not path: return
        try:
            export_exams_to_word(self.exams, path)
            self.toast.show("✅ Exámenes exportados a Word")
        except Exception as e:
            self.toast.show(f"Error al exportar Word: {e}", "error")

    def _export_exams_md(self):
        """Exporta la lista de exámenes a Markdown."""
        if not self.exams:
            self.toast.show("No hay exámenes para exportar", "warning"); return
        path, _ = QFileDialog.getSaveFileName(self, "Exportar exámenes a MD", "examenes.md", "Markdown (*.md)")
        if not path: return
        try:
            export_exams_to_md(self.exams, path)
            self.toast.show("✅ Exámenes exportados a MD")
        except Exception as e:
            self.toast.show(f"Error al exportar MD: {e}", "error")

    def _show_stats(self):
        """Muestra un diálogo con estadísticas del proyecto."""
        if not self.exams:
            self.toast.show("No hay datos para mostrar estadísticas", "warning"); return
        d = QDialog(self)
        d.setWindowTitle("📊 Estadísticas del proyecto")
        d.setMinimumWidth(480)
        v = QVBoxLayout(d)
        v.setSpacing(10)

        total_slots = sum(len(c.get("time_slots", [])) for c in self.classrooms)
        total_students = sum(e["students"] for e in self.exams)
        studies = {}
        for e in self.exams:
            studies.setdefault(e["study"], []).append(e)

        stats_text = (
            f"📋   {len(self.exams)} exámenes\n"
            f"🏫   {len(self.classrooms)} aulas\n"
            f"🗓   {total_slots} franjas totales\n"
            f"👥   {total_students} alumnos\n"
            f"📚   {len(studies)} estudios\n\n"
        )
        stats_text += "📖 Por estudio:\n"
        for s, elist in sorted(studies.items()):
            stats_text += f"   • {s}: {len(elist)} exámenes, {sum(e['students'] for e in elist)} alumnos\n"

        if self.last_assignment:
            used_slots = len({a["slot"] for a in self.last_assignment})
            stats_text += f"\n✅ Última generación: {used_slots} franjas usadas\n"
            for a in self.last_assignment:
                cn = a["classroom"]["name"]
                stats_text += f"   🕐 {a['slot_label']}  🏫 {cn}  📝 {a['exam']['name']}\n"

        lbl = QLabel(stats_text)
        lbl.setStyleSheet("font-size: 13px; line-height: 1.6; padding: 12px; font-family: Consolas;")
        v.addWidget(lbl)

        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        bb.accepted.connect(d.accept)
        v.addWidget(bb)
        d.exec()

    def _save_slot_template(self):
        """Guarda las franjas del aula seleccionada como plantilla."""
        if self._selected_classroom_idx is None or self._selected_classroom_idx >= len(self.classrooms):
            self.toast.show("Selecciona un aula primero", "warning"); return
        c = self.classrooms[self._selected_classroom_idx]
        slots = c.get("time_slots", [])
        if not slots:
            self.toast.show("El aula no tiene franjas", "warning"); return
        path, _ = QFileDialog.getSaveFileName(self, "Guardar plantilla de franjas", "plantilla.json", "JSON (*.json)")
        if not path: return
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(slots, f, ensure_ascii=False, indent=2)
            self.toast.show(f"✅ {len(slots)} franjas guardadas como plantilla")
        except Exception as e:
            self.toast.show(f"Error: {e}", "error")

    def _load_slot_template(self):
        """Carga una plantilla de franjas y las aplica al aula seleccionada."""
        if self._selected_classroom_idx is None or self._selected_classroom_idx >= len(self.classrooms):
            self.toast.show("Selecciona un aula primero", "warning"); return
        path, _ = QFileDialog.getOpenFileName(self, "Cargar plantilla de franjas", "", "JSON (*.json)")
        if not path: return
        try:
            with open(path, "r", encoding="utf-8") as f:
                slots = json.load(f)
            if not isinstance(slots, list):
                self.toast.show("El archivo debe contener una lista de franjas", "warning"); return
            c = self.classrooms[self._selected_classroom_idx]
            c["time_slots"] = slots
            self._refresh_slot_panel()
            self._rebuild_classroom_list()
            self._update_stats()
            self._mark_dirty()
            self.toast.show(f"✅ {len(slots)} franjas cargadas")
        except Exception as e:
            self.toast.show(f"Error: {e}", "error")

    def _on_exam_filter_changed(self, text):
        """Filtra la lista de exámenes por texto."""
        self._exam_filter = text.lower()
        self._rebuild_exam_list()

    def _on_classroom_filter_changed(self, text):
        """Filtra la lista de aulas por texto."""
        self._classroom_filter = text.lower()
        self._rebuild_classroom_list()

    # ── Indicador de carga animado ─────────────────────────────────────

    def _start_loading(self, btn=None):
        """Activa el indicador de carga con animación de puntos y mensajes."""
        self._loading_dots = 0
        self._loading_msg_idx = 0
        self._loading_timer.start(600)
        self.gen_progress_label.show()
        self.gen_progress.show()
        self.gen_progress_label.setText("🧠 Analizando restricciones y datos de entrada...")
        if btn:
            btn.setEnabled(False)
        QApplication.processEvents()

    def _stop_loading(self, btn=None, btn_text=None):
        """Desactiva el indicador de carga."""
        self._loading_timer.stop()
        self.gen_progress_label.hide()
        self.gen_progress.hide()
        if btn and btn_text:
            btn.setEnabled(True)
            btn.setText(btn_text)
        QApplication.processEvents()

    def _animate_loading(self):
        """Anima el texto de carga: cambia mensaje y añade puntos."""
        self._loading_dots += 1
        if self._loading_dots > 4:
            self._loading_dots = 0
            self._loading_msg_idx = (self._loading_msg_idx + 1) % len(self._loading_messages)
            base = self._loading_messages[self._loading_msg_idx]
        else:
            base = self._loading_messages[self._loading_msg_idx]
        self.gen_progress_label.setText(base + "." * self._loading_dots)

    # ── Generar calendario (con múltiples opciones) ────────────────────

    def _generate(self):
        """
        Genera múltiples opciones de calendario en un hilo separado
        para no bloquear la interfaz.
        """
        if self._solving:
            self.toast.show("Ya hay una generación en curso", "warning"); return
        # ── Validación previa ──
        val = self._validate_before_generate()
        if isinstance(val, str):
            self.toast.show(val, "warning"); return
        if isinstance(val, list):
            msg = "Problemas detectados:\n" + "\n".join(val)
            reply = QMessageBox.question(self, "⚠️ Advertencias", msg + "\n\n¿Generar de todas formas?",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.No:
                return

        if not self.exams:
            self.toast.show("Añade al menos un examen", "warning"); return
        if not self.classrooms:
            self.toast.show("Añade al menos un aula", "warning"); return
        total_slots = sum(len(c.get("time_slots", [])) for c in self.classrooms)
        if total_slots == 0:
            self.toast.show("Las aulas necesitan franjas horarias", "warning"); return

        try:
            num_options = int(self.num_options_spin.text())
            if num_options < 1:
                num_options = 5
        except ValueError:
            num_options = 5
        self.num_options_spin.setText(str(num_options))

        pname = self.project_name_input.text().strip() or "(sin nombre)"

        self._log(f"\n{'='*60}")
        self._log(f"🚀 Proyecto: {pname}")
        self._log(f"🏫 Aulas: {len(self.classrooms)} | 🗓 Franjas: {total_slots}")
        self._log(f"📋 Exámenes: {len(self.exams)} | 🔢 Opciones: {num_options}")

        # ── Lanzar solver en hilo ──
        self._solving = True
        self._start_loading(self.gen_btn)
        self.gen_btn.setText("⏳ Generando...")

        self._solver_thread = QThread(self)
        self._solver_worker = SolverWorker(self.exams, self.classrooms, num_options)
        self._solver_worker.moveToThread(self._solver_thread)
        self._solver_thread.started.connect(self._solver_worker.run)
        self._solver_worker.finished.connect(lambda sched, sols, _: self._on_generate_done(sched, sols, pname))
        self._solver_worker.error.connect(lambda msg: self._on_generate_error(msg))
        self._solver_worker.log.connect(self._log)
        self._solver_thread.finished.connect(self._solver_thread.deleteLater)
        self._solver_thread.start()

    def _on_generate_done(self, scheduler, solutions, pname):
        """Callback cuando el solver termina correctamente."""
        self._solver_thread.quit()
        self._solver_thread.wait()
        self._solver_worker.deleteLater()
        self._solving = False

        self._last_scheduler = scheduler

        # Guardar soluciones
        self.generated_solutions = solutions
        self.generated_paths = {}

        # Exportar a HTML
        out_dir = os.path.join(BASE_DIR, "output")
        os.makedirs(out_dir, exist_ok=True)
        safe = re.sub(r"[^a-zA-Z0-9_\-]", "_", pname)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        for idx, slots_used, assignment in solutions:
            filename = f"{safe}_{timestamp}_opcion{idx}.html"
            path = os.path.join(out_dir, filename)
            export_html_file(pname, scheduler.global_slots, self.exams, self.classrooms,
                             assignment, scheduler.num_slots, path)
            self.generated_paths[idx] = path
            self._log(f"   📄 Opción {idx} → {path}")

        # Mostrar primera opción
        first_idx, first_slots, first_assignment = solutions[0]
        self.last_assignment = first_assignment
        self.last_html_path = self.generated_paths[first_idx]
        self.current_option_idx = first_idx

        self._log(f"\n📊 Detalle de la opción {first_idx}:")
        self._log(f"   Franjas usadas: {first_slots} de {scheduler.num_slots}")
        for a in sorted(first_assignment, key=lambda x: (x["slot"], x["classroom"]["name"])):
            self._log(f"   🕐 {a['slot_label']} | 🏫 {a['classroom']['name']:20s} | 📝 {a['exam']['name'][:40]:40s} | 👥 {a['exam']['students']} alumnos")

        # Poblar selector
        self.option_selector.blockSignals(True)
        self.option_selector.clear()
        for idx, slots_used, _ in solutions:
            self.option_selector.addItem(f"Opción {idx} — {slots_used} franjas", idx)
        self.option_selector.setCurrentIndex(0)
        self.option_selector.setEnabled(True)
        self.option_selector.blockSignals(False)

        self._stop_loading(self.gen_btn, "🚀 Generar Calendario")
        self.tabs.setCurrentIndex(4)
        self._update_calendar_tab(first_slots, scheduler.num_slots)
        self._update_status()
        self.toast.show(f"✅ {len(solutions)} opciones generadas")

    def _on_generate_error(self, msg):
        """Callback cuando el solver falla."""
        self._solver_thread.quit()
        self._solver_thread.wait()
        self._solver_worker.deleteLater()
        self._solving = False
        self._stop_loading(self.gen_btn, "🚀 Generar Calendario")
        self._log(f"✖ {msg}")
        if msg == "Sin solución posible":
            self.toast.show("Sin solución posible. Añade más franjas o aulas.", "error")
        else:
            self.toast.show(f"Error: {msg}", "error")

    def _on_option_changed(self, index):
        """Cambia la opción de calendario mostrada cuando el usuario la selecciona."""
        if index < 0 or index >= len(self.generated_solutions):
            return
        idx, slots_used, assignment = self.generated_solutions[index]
        self.last_assignment = assignment
        self.last_html_path = self.generated_paths.get(idx, self.last_html_path)
        self.current_option_idx = idx
        self._update_calendar_tab(slots_used, None)
        self._log(f"🔀 Cambiado a Opción {idx} ({slots_used} franjas)")

    def _on_cal_filter_changed(self, text):
        """Filtra los exámenes visibles en el calendario."""
        self._update_calendar_tab()

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

        if not self.last_assignment: return

        self.open_btn.setEnabled(True)
        self.open_folder_btn.setEnabled(True)
        self.csv_btn.setEnabled(True)
        self.word_btn.setEnabled(True)
        self.md_btn.setEnabled(True)
        self.compact_view_btn.setEnabled(True)
        self.compare_view_btn.setEnabled(len(self.generated_solutions) >= 2)

        # Aplicar filtro del calendario
        ft = self.cal_filter_input.text().strip().lower() if hasattr(self, 'cal_filter_input') else ""
        self._cal_filter = ft
        a = self.last_assignment
        if ft:
            a = [x for x in a if ft in x["exam"]["name"].lower() or ft in x["exam"]["study"].lower()]
        n = slots_used or len({x["slot"] for x in a})
        studies = sorted({e["study"] for e in self.exams})
        total_students = sum(e["students"] for e in self.exams)
        self.cal_summary.setText(f"📋 {len(self.exams)} exámenes · {n} franjas · "
                                 f"🏫 {len(self.classrooms)} aulas · {total_students} alumnos · {len(studies)} estudios")

        if self._compare_view and len(self.generated_solutions) >= 2:
            self._update_compare_view()
            return

        if self._compact_view:
            self._update_calendar_tab_compact()
            return

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
            self._make_slot_drop_target(slot_card, t)
            slot_card_v.addWidget(header)

            items_frame = QFrame()
            items_frame.setStyleSheet("")
            items_lay = QVBoxLayout(items_frame)
            items_lay.setContentsMargins(0, 0, 0, 0)
            items_lay.setSpacing(4)

            for x in sorted(groups[t], key=lambda x: x["classroom"]["name"]):
                card = self._make_exam_card_detail(x, t)
                items_lay.addWidget(card)

            slot_card_v.addWidget(items_frame)
            self.cal_layout.addWidget(slot_card)

    def _toggle_compact_view(self):
        """Alterna entre vista detalle y vista compacta."""
        self._compact_view = not self._compact_view
        self._compare_view = False
        self.compact_view_btn.setText("📋 Vista detalle" if self._compact_view else "📊 Vista completa")
        self._update_calendar_tab()

    def _toggle_compare_view(self):
        """Alterna entre vista normal y comparativa lado a lado."""
        self._compare_view = not self._compare_view
        self._compact_view = False
        self.compare_view_btn.setText("📋 Vista normal" if self._compare_view else "🔀 Comparar")
        self._update_calendar_tab()

    def _update_calendar_tab_compact(self):
        """Renderiza el calendario en vista completa tipo tabla."""
        a = self.last_assignment
        if not a:
            return
        ft = self._cal_filter
        if ft:
            a = [x for x in a if ft in x["exam"]["name"].lower() or ft in x["exam"]["study"].lower()]

        # Agrupar por slot y classroom
        slot_assignments = {}
        for x in a:
            slot_assignments.setdefault(x["slot"], {}).setdefault(x["classroom"]["name"], []).append(x)

        classroom_names = list(dict.fromkeys(c["name"] for c in self.classrooms))
        used_slots = sorted({x["slot"] for x in a})

        for t in used_slots:
            slot_label = a[0]["slot_label"].split(" ")[0] if a else ""
            slot_time = a[0]["slot_label"].split(" ")[1] if a and " " in a[0]["slot_label"] else ""
            date, time_range = "", ""
            if a:
                parts = a[0]["slot_label"].split(" ", 1)
                if len(parts) == 2:
                    date, time_range = parts

            slot_card = QFrame()
            slot_card.setObjectName("card")
            slot_card.setStyleSheet("")
            slot_v = QVBoxLayout(slot_card)
            slot_v.setContentsMargins(10, 8, 10, 8)
            slot_v.setSpacing(4)

            header = QLabel(f"🕐 {a[0]['slot_label']}")
            header.setStyleSheet(f"font-weight: bold; font-size: 13px; color: {C_PRI};")
            slot_v.addWidget(header)

            exams_at_slot = slot_assignments.get(t, {})
            for cn in classroom_names:
                exams = exams_at_slot.get(cn, [])
                if exams:
                    for x in exams:
                        color = x["exam"].get("color", self._study_color(x["exam"]["study"]))
                        card = self._make_exam_card(x, t)
                        row_lay = QHBoxLayout(card)
                        row_lay.setContentsMargins(8, 2, 8, 2)
                        dot = QLabel("●")
                        dot.setStyleSheet(f"color: {color}; font-size: 14px;")
                        dot.setFixedWidth(16)
                        row_lay.addWidget(dot)
                        info = QLabel(f"<b>{cn}</b>  |  {x['exam']['name']}  👥 {x['exam']['students']}")
                        info.setTextFormat(Qt.TextFormat.RichText)
                        row_lay.addWidget(info, 1)

                        exam_idx = x["exam_idx"]
                        is_locked = exam_idx in self._locked_assignments
                        lock_lbl = QLabel("🔓" if not is_locked else "🔒")
                        lock_lbl.setFixedSize(26, 24)
                        lock_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                        lock_lbl.setStyleSheet("background:#e0f2fe; border:1px solid #38bdf8; border-radius:3px; font-size:12px;")
                        lock_lbl.mousePressEvent = lambda e, ei=exam_idx, si=t, ci=x["classroom_idx"]: self._toggle_lock(ei, si, ci)
                        row_lay.addWidget(lock_lbl)

                        slot_v.addWidget(card)
                else:
                    empty_lbl = QLabel(f"<span style='color:{C_SLATE};'>— {cn} —</span>")
                    empty_lbl.setTextFormat(Qt.TextFormat.RichText)
                    slot_v.addWidget(empty_lbl)

            self._make_slot_drop_target(slot_card, t)
            self.cal_layout.addWidget(slot_card)

    def _update_compare_view(self):
        """Muestra dos opciones lado a lado para comparar."""
        if len(self.generated_solutions) < 2:
            return

        from PyQt6.QtWidgets import QSplitter

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)

        for cmp_idx in range(min(2, len(self.generated_solutions))):
            idx, slots_used, assignment = self.generated_solutions[cmp_idx]
            ft = self._cal_filter
            if ft:
                assignment = [x for x in assignment if ft in x["exam"]["name"].lower() or ft in x["exam"]["study"].lower()]
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.Shape.NoFrame)
            container = QWidget()
            lay = QVBoxLayout(container)
            lay.setContentsMargins(8, 8, 8, 8)
            lay.setSpacing(6)

            # Header
            header = QLabel(f"📅 Opción {idx}  —  {slots_used} franjas")
            header.setStyleSheet(f"font-weight: bold; font-size: 15px; color: {C_PRI};")
            lay.addWidget(header)

            groups = {}
            for x in sorted(assignment, key=lambda x: (x["slot"], x["classroom"]["name"])):
                groups.setdefault(x["slot"], []).append(x)

            for t in sorted(groups.keys()):
                slot_card = QFrame()
                slot_card.setObjectName("card")
                slot_card.setStyleSheet("")
                card_v = QVBoxLayout(slot_card)
                card_v.setContentsMargins(8, 6, 8, 6)
                card_v.setSpacing(4)
                label_text = groups[t][0]["slot_label"]
                sh = QLabel(f"🕐 {label_text}")
                sh.setStyleSheet(f"font-weight: 600; font-size: 11px; color: {C_PRI};")
                card_v.addWidget(sh)

                for x in sorted(groups[t], key=lambda x: x["classroom"]["name"]):
                    color = x["exam"].get("color", self._study_color(x["exam"]["study"]))
                    card = self._make_exam_card(x, t)
                    rl = QHBoxLayout(card)
                    rl.setContentsMargins(6, 2, 6, 2)
                    dot = QLabel("●")
                    dot.setStyleSheet(f"color: {color}; font-size: 12px;")
                    dot.setFixedWidth(14)
                    rl.addWidget(dot)
                    info = QLabel(f"<b>{x['classroom']['name']}</b><br>{x['exam']['name']} 👥{x['exam']['students']}")
                    info.setTextFormat(Qt.TextFormat.RichText)
                    info.setStyleSheet("font-size: 11px;")
                    rl.addWidget(info, 1)
                    card_v.addWidget(card)

                self._make_slot_drop_target(slot_card, t)
                lay.addWidget(slot_card)

            lay.addStretch()
            scroll.setWidget(container)
            splitter.addWidget(scroll)

        self.cal_layout.addWidget(splitter)

    # ── Menú contextual, doble clic y drag & drop en exámenes ──────────

    def _exam_tooltip(self, x):
        """Genera un tooltip descriptivo para un examen."""
        e = x["exam"]
        lines = [
            f"📝 {e['name']}",
            f"📚 {e['study']}",
            f"👥 {e['students']} alumnos",
            f"🏫 {x['classroom']['name']}",
        ]
        if e.get("teacher"):
            lines.append(f"👨‍🏫 {e['teacher']}")
        if e.get("preferred_shift"):
            lines.append(f"⏰ Turno preferido: {'Mañana' if e['preferred_shift'] == 'morning' else 'Tarde'}")
        return "\n".join(lines)

    def _make_exam_card(self, x, slot_idx, compact=False):
        """Crea un QFrame de examen con menú contextual, doble clic y drag."""
        exam_idx = x["exam_idx"]
        classroom_idx = x["classroom_idx"]
        is_locked = exam_idx in self._locked_assignments

        card = QFrame()
        card.setObjectName("slot_row")
        if is_locked:
            card.setStyleSheet("QFrame#slot_row { background: #1e3a5f; border: 2px solid #f59e0b; border-radius: 4px; }")
        else:
            card.setStyleSheet("")
        card.setToolTip(self._exam_tooltip(x))

        card._drag_data = (exam_idx, slot_idx, classroom_idx)

        card.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        card.customContextMenuRequested.connect(
            lambda pos, ei=exam_idx, si=slot_idx, ci=classroom_idx:
                self._exam_context_menu(pos, ei, si, ci))

        original_double = card.mouseDoubleClickEvent
        def _on_double(event, ei=exam_idx):
            if event.button() == Qt.MouseButton.LeftButton:
                self._edit_exam_from_calendar(ei)
            if original_double:
                original_double(event)
        card.mouseDoubleClickEvent = _on_double

        # ── Drag source ──
        card._drag_start_pos = None
        original_press = card.mousePressEvent
        def _on_press(event, ei=exam_idx, si=slot_idx, ci=classroom_idx):
            if event.button() == Qt.MouseButton.LeftButton:
                card._drag_start_pos = event.position().toPoint()
            if original_press:
                original_press(event)
        card.mousePressEvent = _on_press

        original_move = card.mouseMoveEvent
        def _on_move(event, ei=exam_idx, si=slot_idx, ci=classroom_idx):
            if event.buttons() == Qt.MouseButton.LeftButton and card._drag_start_pos:
                dist = (event.position().toPoint() - card._drag_start_pos).manhattanLength()
                if dist > 10:
                    drag = QDrag(card)
                    mime = QMimeData()
                    mime.setData("application/x-exam", f"{ei},{si},{ci}".encode())
                    drag.setMimeData(mime)
                    drag.exec(Qt.DropAction.MoveAction)
                    card._drag_start_pos = None
                    return
            if original_move:
                original_move(event)
        card.mouseMoveEvent = _on_move

        return card

    def _make_exam_card_detail(self, x, slot_idx):
        """Crea la tarjeta completa para vista detalle."""
        card = self._make_exam_card(x, slot_idx)
        row = QHBoxLayout(card)
        row.setContentsMargins(10, 4, 10, 4)
        exam_idx = x["exam_idx"]
        is_locked = exam_idx in self._locked_assignments

        info = QLabel(f"🏫 {x['classroom']['name']:15s}  |  📝 {x['exam']['name']:35s}  |  👥 {x['exam']['students']} alumnos  |  📚 {x['exam']['study']}")
        row.addWidget(info, 1)

        lock_lbl = QLabel("🔓" if not is_locked else "🔒")
        lock_lbl.setFixedSize(30, 28)
        lock_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lock_lbl.setStyleSheet("background:#e0f2fe; border:1px solid #38bdf8; border-radius:4px; font-size:14px;")
        lock_lbl.mousePressEvent = lambda e, ei=exam_idx, si=slot_idx, ci=x["classroom_idx"]: self._toggle_lock(ei, si, ci)
        row.addWidget(lock_lbl)

        return card

    def _make_slot_drop_target(self, slot_card, slot_idx):
        """Convierte un contenedor de franja en destino de arrastre."""
        slot_card.setAcceptDrops(True)

        def drag_enter(event):
            if event.mimeData().hasFormat("application/x-exam"):
                event.acceptProposedAction()
        slot_card.dragEnterEvent = drag_enter

        def drag_move(event):
            if event.mimeData().hasFormat("application/x-exam"):
                event.acceptProposedAction()
        slot_card.dragMoveEvent = drag_move

        def drop(event):
            data = event.mimeData().data("application/x-exam").data().decode()
            parts = data.split(",")
            if len(parts) != 3:
                return
            exam_idx, old_slot, old_classroom = int(parts[0]), int(parts[1]), int(parts[2])
            if exam_idx < 0 or exam_idx >= len(self.exams):
                return
            target_slot = slot_idx
            target_classroom = old_classroom
            # Skip if dropped on same spot
            if target_slot == old_slot and target_classroom == old_classroom:
                event.acceptProposedAction()
                return
            # Check if the old classroom has a slot at this target slot index
            valid = False
            for ci, c in enumerate(self.classrooms):
                if ci == target_classroom:
                    if target_slot < len(c["time_slots"]):
                        valid = True
                    break
            if not valid:
                for ci, c in enumerate(self.classrooms):
                    if target_slot < len(c["time_slots"]):
                        target_classroom = ci
                        valid = True
                        break
            if valid:
                old_exam = self.exams[exam_idx]
                old_students = old_exam["students"]
                total_students = 0
                for a_item in self.last_assignment:
                    if a_item["slot"] == target_slot and a_item["classroom_idx"] == target_classroom and a_item["exam_idx"] != exam_idx:
                        total_students += a_item["exam"]["students"]
                if total_students + old_students <= self.classrooms[target_classroom]["capacity"]:
                    self._locked_assignments[exam_idx] = (target_slot, target_classroom)
                    self.toast.show(f"📦 {old_exam['name']} movido a nueva franja, regenerando...")
                    self._regenerate_with_locks()
                else:
                    self.toast.show(f"❌ Capacidad insuficiente en el aula de destino", "warning")
            event.acceptProposedAction()
        slot_card.dropEvent = drop

    def _exam_context_menu(self, pos, exam_idx, slot_idx, classroom_idx):
        """Muestra menú contextual sobre un examen del calendario."""
        menu = QMenu()
        exam = self.exams[exam_idx]
        is_locked = exam_idx in self._locked_assignments

        edit_action = menu.addAction("✏️ Editar examen")
        menu.addSeparator()
        move_action = menu.addAction("🔄 Mover a otra franja/aula")
        lock_action = menu.addAction("🔒 Bloquear" if not is_locked else "🔓 Desbloquear")
        menu.addSeparator()
        delete_action = menu.addAction("❌ Eliminar examen")

        action = menu.exec(self.sender().mapToGlobal(pos))
        if action == edit_action:
            self._edit_exam_from_calendar(exam_idx)
        elif action == move_action:
            self._move_exam_dialog(exam_idx, slot_idx, classroom_idx)
        elif action == lock_action:
            self._toggle_lock(exam_idx, slot_idx, classroom_idx)
        elif action == delete_action:
            self._delete_exam_from_calendar(exam_idx)

    def _edit_exam_from_calendar(self, exam_idx):
        """Diálogo para editar un examen desde el calendario."""
        if exam_idx < 0 or exam_idx >= len(self.exams):
            return
        exam = self.exams[exam_idx]

        dlg = QDialog(self)
        dlg.setWindowTitle(f"✏️ Editar: {exam['name']}")
        dlg.setMinimumWidth(400)
        dlg.setModal(True)
        # Aplicar tema
        is_dark = self._dark_mode
        bg = "#1e293b" if is_dark else "#ffffff"
        fg = "#f1f5f9" if is_dark else "#0f172a"
        dlg.setStyleSheet(f"background:{bg}; color:{fg};")

        layout = QFormLayout(dlg)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)

        name_inp = QLineEdit(exam["name"])
        students_inp = QLineEdit(str(exam["students"]))
        study_inp = QLineEdit(exam["study"])
        teacher_inp = QLineEdit(exam.get("teacher", ""))
        color_inp = QLineEdit(exam.get("color", self._study_color(exam["study"])))
        shift_inp = QComboBox()
        shift_inp.addItems(["Sin preferencia", "Mañana", "Tarde"])
        pref = exam.get("preferred_shift", "")
        shift_inp.setCurrentIndex({"morning": 1, "afternoon": 2}.get(pref, 0))

        layout.addRow("Nombre:", name_inp)
        layout.addRow("Alumnos:", students_inp)
        layout.addRow("Estudio:", study_inp)
        layout.addRow("Profesor:", teacher_inp)
        layout.addRow("Color (hex):", color_inp)
        layout.addRow("Turno pref.:", shift_inp)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        layout.addRow(btns)

        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                exam["name"] = name_inp.text().strip()
                exam["students"] = int(students_inp.text())
                exam["study"] = study_inp.text().strip()
                exam["teacher"] = teacher_inp.text().strip() or None
                color_val = color_inp.text().strip()
                if re.match(r'^#[0-9a-fA-F]{6}$', color_val):
                    exam["color"] = color_val
                shift_val = {1: "morning", 2: "afternoon"}.get(shift_inp.currentIndex(), None)
                if shift_val:
                    exam["preferred_shift"] = shift_val
                else:
                    exam.pop("preferred_shift", None)
                self.toast.show(f"✅ Examen '{exam['name']}' actualizado")
                self._update_exam_list()
                self._mark_dirty()
            except (ValueError, IndexError):
                self.toast.show("❌ Valor inválido", "warning")

    def _move_exam_dialog(self, exam_idx, slot_idx, classroom_idx):
        """Diálogo para mover un examen a otra franja/aula."""
        # Build global slot index mapping (same logic as scheduler)
        slot_key_to_idx = {}
        for c in self.classrooms:
            for ts in c.get("time_slots", []):
                key = (ts["date"], ts["start"], ts["end"])
                if key not in slot_key_to_idx:
                    slot_key_to_idx[key] = len(slot_key_to_idx)

        slots_info = []
        for c in self.classrooms:
            for ts in c["time_slots"]:
                label = f"{ts['date']} {ts['start']}-{ts['end']} — {c['name']}"
                global_slot = slot_key_to_idx[(ts["date"], ts["start"], ts["end"])]
                slots_info.append((label, global_slot, c))

        if not slots_info:
            self.toast.show("No hay franjas disponibles", "warning")
            return

        dlg = QDialog(self)
        dlg.setWindowTitle(f"🔄 Mover '{self.exams[exam_idx]['name']}'")
        dlg.setMinimumWidth(500)
        dlg.setModal(True)
        is_dark = self._dark_mode
        bg = "#1e293b" if is_dark else "#ffffff"
        fg = "#f1f5f9" if is_dark else "#0f172a"
        dlg.setStyleSheet(f"background:{bg}; color:{fg};")

        layout = QVBoxLayout(dlg)

        lbl = QLabel("Selecciona la franja y aula de destino:")
        lbl.setStyleSheet(f"font-weight: bold; color: {C_PRI};")
        layout.addWidget(lbl)

        list_widget = QListWidget()
        for label, global_slot, c in slots_info:
            capacity = c["capacity"]
            item_text = f"{label} (capacidad: {capacity})"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, (global_slot, c["name"]))
            list_widget.addItem(item)
        layout.addWidget(list_widget)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        layout.addWidget(btns)

        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)

        if dlg.exec() == QDialog.DialogCode.Accepted:
            selected = list_widget.currentItem()
            if not selected:
                return
            ts_data, classroom_name = selected.data(Qt.ItemDataRole.UserRole)
            # Buscar el classroom_idx que corresponde
            target_slot = int(ts_data)
            target_classroom = None
            for ci, c in enumerate(self.classrooms):
                if c["name"] == classroom_name:
                    target_classroom = ci
                    break
            if target_slot is not None and target_classroom is not None:
                # Bloquear en nuevo destino y regenerar
                self._toggle_lock(exam_idx, target_slot, target_classroom)
                self._regenerate_with_locks()

    def _delete_exam_from_calendar(self, exam_idx):
        """Elimina un examen del proyecto desde el calendario."""
        if exam_idx < 0 or exam_idx >= len(self.exams):
            return
        exam = self.exams[exam_idx] if hasattr(self, 'exams') else None
        if not exam:
            return
        reply = QMessageBox.question(self, "Eliminar examen",
            f"¿Eliminar '{exam['name']}' del proyecto?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.exams.pop(exam_idx)
            # Ajustar locked_assignments
            new_locks = {}
            for ei, v in self._locked_assignments.items():
                if ei < exam_idx:
                    new_locks[ei] = v
                elif ei > exam_idx:
                    new_locks[ei - 1] = v
            self._locked_assignments = new_locks
            self._update_exam_list()
            self._mark_dirty()
            self.toast.show(f"🗑️ '{exam['name']}' eliminado")

    # ── Bloquear / desbloquear asignaciones ─────────────────────────────
    
    def _toggle_lock(self, exam_idx, slot_idx, classroom_idx):
        """Bloquea o desbloquea una asignación."""
        if exam_idx in self._locked_assignments:
            del self._locked_assignments[exam_idx]
            self.toast.show(f"🔓 Asignación desbloqueada")
        else:
            self._locked_assignments[exam_idx] = (slot_idx, classroom_idx)
            self.toast.show(f"🔒 Asignación bloqueada")
        self.clear_locks_btn.setEnabled(len(self._locked_assignments) > 0)
        self.regenerate_locked_btn.setEnabled(len(self._locked_assignments) > 0 and self._last_scheduler is not None)
        self._update_calendar_tab()
        self._update_status()

    def _clear_locks(self):
        """Limpia todos los bloqueos."""
        self._locked_assignments.clear()
        self.clear_locks_btn.setEnabled(False)
        self.regenerate_locked_btn.setEnabled(False)
        self._update_calendar_tab()
        self._update_status()
        self.toast.show("🔓 Bloqueos limpiados")

    def _regenerate_with_locks(self):
        """Regenera el calendario en un hilo manteniendo las asignaciones bloqueadas."""
        if self._solving:
            self.toast.show("Ya hay una generación en curso", "warning"); return
        if not self._locked_assignments:
            self.toast.show("No hay bloqueos para mantener", "warning"); return
        if not self._last_scheduler:
            self.toast.show("Genera un calendario primero", "warning"); return

        pname = self.project_name_input.text().strip() or "(sin nombre)"
        num_options = len(self.generated_solutions) if self.generated_solutions else 5

        self._log(f"\n{'='*60}")
        self._log(f"🔒 Regenerando con {len(self._locked_assignments)} bloqueos...")

        # Lanzar solver en hilo
        self._solving = True
        self._start_loading(self.regenerate_locked_btn)
        self.regenerate_locked_btn.setText("⏳ Regenerando...")

        self._solver_thread = QThread(self)
        self._solver_worker = SolverWorker(
            self.exams, self.classrooms, num_options,
            locked_assignments=self._locked_assignments
        )
        self._solver_worker.moveToThread(self._solver_thread)
        self._solver_thread.started.connect(self._solver_worker.run)
        self._solver_worker.finished.connect(lambda s, sols, _: self._on_regenerate_done(s, sols, pname))
        self._solver_worker.error.connect(lambda msg: self._on_regenerate_error(msg))
        self._solver_worker.log.connect(self._log)
        self._solver_thread.finished.connect(self._solver_thread.deleteLater)
        self._solver_thread.start()

    def _on_regenerate_done(self, scheduler, solutions, pname):
        """Callback cuando la regeneración con bloqueos termina."""
        self._solver_thread.quit()
        self._solver_thread.wait()
        self._solver_worker.deleteLater()
        self._solving = False
        self._stop_loading(self.regenerate_locked_btn, "🔒 Regenerar con bloqueos")

        if not solutions:
            self._log("✖ Sin solución posible con los bloqueos actuales.")
            self.toast.show("Sin solución posible con esos bloqueos", "error"); return

        self._last_scheduler = scheduler
        self.generated_solutions = solutions
        self.generated_paths = {}

        out_dir = os.path.join(BASE_DIR, "output")
        os.makedirs(out_dir, exist_ok=True)
        safe = re.sub(r"[^a-zA-Z0-9_\-]", "_", pname)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        for idx, slots_used, assignment in solutions:
            filename = f"{safe}_{timestamp}_opcion{idx}.html"
            path = os.path.join(out_dir, filename)
            export_html_file(pname, scheduler.global_slots, self.exams, self.classrooms,
                             assignment, scheduler.num_slots, path)
            self.generated_paths[idx] = path

        first_idx, first_slots, first_assignment = solutions[0]
        self.last_assignment = first_assignment
        self.last_html_path = self.generated_paths[first_idx]
        self.current_option_idx = first_idx

        self.option_selector.blockSignals(True)
        self.option_selector.clear()
        for idx, slots_used, _ in solutions:
            self.option_selector.addItem(f"Opción {idx} — {slots_used} franjas", idx)
        self.option_selector.setCurrentIndex(0)
        self.option_selector.setEnabled(True)
        self.option_selector.blockSignals(False)

        self._update_calendar_tab(first_slots, scheduler.num_slots)
        self._update_status()
        self._log(f"✅ {len(solutions)} opciones generadas con bloqueos")
        self.toast.show(f"✅ {len(solutions)} opciones con bloqueos")

    def _on_regenerate_error(self, msg):
        """Callback cuando la regeneración con bloqueos falla."""
        self._solver_thread.quit()
        self._solver_thread.wait()
        self._solver_worker.deleteLater()
        self._solving = False
        self._stop_loading(self.regenerate_locked_btn, "🔒 Regenerar con bloqueos")
        self._log(f"✖ {msg}")
        self.toast.show(f"Error: {msg}", "error")

    # ── Abrir HTML ─────────────────────────────────────────────────────

    def _open_html(self):
        """Abre el HTML generado en el navegador web."""
        if self.last_html_path and os.path.exists(self.last_html_path):
            webbrowser.open(f"file://{os.path.abspath(self.last_html_path)}")

    def _open_folder(self):
        """Abre la carpeta que contiene el HTML generado."""
        if self.last_html_path:
            os.startfile(os.path.dirname(os.path.abspath(self.last_html_path)))
