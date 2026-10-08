# AGENTS — Generador de Calendario de Exámenes

## Resumen del proyecto

App Python (PyQt6) que usa Google OR-Tools CP-SAT para asignar exámenes a **bloques de franjas horarias** y aulas, respetando restricciones de capacidad, ordenadores, duración, estudios y profesores simultáneos, y franjas reservadas.

## Stack

- Python 3.11+
- PyQt6 (interfaz gráfica)
- OR-Tools CP-SAT 9.8+ (solver de optimización combinatoria)
- HTML/CSS embebido (exportación a HTML imprimible)

## Estructura

```
main.py            — Punto de entrada
gui.py             — Interfaz PyQt6 (pestañas, formularios, lógica)
scheduler.py       — Motor CP-SAT (modelo matemático + solver)
html_exporter.py   — Generación de HTML del calendario (tabla + cuadrante)
md_exporter.py     — Exportación a Markdown
word_exporter.py   — Exportación a Word (.docx)
calendar_io.py     — Export/import del calendario generado a JSON autocontenido
seed_data.py       — Datos de ejemplo ficticios
tests/             — Tests unitarios (unittest)
run_tests.py       — Runner de tests
requirements.txt   — Dependencias (PyQt6, ortools, python-docx)
index.html         — Página de documentación
manual.html        — Manual de usuario (reveal.js)
prompts_generar_examenes_aulas_JSON.md — Prompts para generar datos/JSON (incl. formato de calendario)
AGENTS.md          — Esta guía para IA
lanzar.bat         — Script de lanzamiento rápido (Windows)
lanzar.sh          — Script de lanzamiento rápido (Linux/macOS)
projects/          — Proyectos guardados (JSON)
output/            — HTML, CSV, MD y Word generados
config.json        — Configuración persistente (tema), se crea solo
```

## Modelo de datos

### Examen (`exams` en JSON)

```json
{
  "name": "Nombre del Examen",
  "students": 25,
  "study": "Ciclo Formativo (Nivel)",
  "color": "#6366f1",
  "preferred_shift": "morning",
  "teacher": "Nombre del Profesor",
  "duration_hours": 2.0,
  "computers": 25
}
```

- `name`: nombre del examen
- `students`: número entero de alumnos
- `study`: nombre del estudio / ciclo formativo
- `color`: (opcional) color personalizado en hex. Si no se especifica, se asigna automáticamente según el estudio.
- `preferred_shift`: (opcional) `"morning"` o `"afternoon"`. El solver lo respeta si es posible (penalización en objetivo).
- `teacher`: (opcional) nombre del profesor. El solver evita que un mismo profesor tenga dos exámenes en la misma franja.
- `duration_hours`: (opcional, default `2.0`) duración en **horas**. El examen ocupa varias franjas consecutivas contiguas del mismo día (`fin == inicio` de la siguiente); no se saltan huecos ni descansos. Si no caben franjas encadenadas, el examen no es colocable.
- `computers`: (opcional, default `0`) número de ordenadores que necesita el examen. Suma de `computers` de los exámenes asignados a la misma (franja, aula) ≤ `computers` del aula.

### Aula (`classrooms` en JSON)

```json
{
  "name": "Nombre del aula",
  "capacity": 30,
  "computers": 30,
  "time_slots": [
    {"date": "2026-06-15", "start": "09:00", "end": "11:00"},
    {"date": "2026-06-15", "start": "11:30", "end": "13:30"},
    {"date": "2026-06-15", "start": "16:00", "end": "18:00", "reserved": true}
  ]
}
```

- `name`: identificador único del aula
- `capacity`: capacidad máxima de alumnos
- `computers`: (opcional, default `0`) número de ordenadores disponibles en el aula
- `time_slots`: lista de franjas disponibles (cada una con date, start, end)

### Franja horaria (`time_slot`)

- `date`: formato `YYYY-MM-DD`
- `start`: formato HH:MM (24h)
- `end`: formato HH:MM (24h)
- `reserved`: (opcional, default `false`) franja **reservada**: el solver nunca asigna exámenes a ella y **rompe las cadenas** de encadenamiento (no sirve para cubrir la duración de un examen largo). Se alterna con 🔒 en el panel de franjas del aula.

## Restricciones del solver

1. Cada examen se asigna a exactamente un **bloque**: una franja de inicio + las franjas consecutivas que cubre su `duration_hours` (mismo día, encadenadas estrictamente)
2. Exámenes del mismo estudio NO pueden solaparse en ninguna franja
3. Exámenes del mismo profesor NO pueden solaparse en ninguna franja
4. Suma de alumnos en (franja, aula) ≤ capacidad del aula (en cada franja del bloque)
5. Suma de `computers` de exámenes en (franja, aula) ≤ `computers` del aula (en cada franja del bloque)
6. Aula solo disponible en sus franjas definidas; las franjas con `reserved: true` no se usan ni para empezar ni para ocupar (y rompen las cadenas de encadenamiento)
7. Objetivo: minimizar el número de franjas utilizadas (+ penalización por incumplir `preferred_shift`)

> Nota: `scheduler.py` expone `build_global_pool`, `classroom_chains`, `enumerate_blocks`, `exam_duration_minutes` y `block_for_start` como helpers de módulo.

## Funcionalidades implementadas

| Funcionalidad | Descripción |
|---|---|---|
| 🔀 **Múltiples opciones** | Genera N opciones (configurable, default 5) y permite cambiar entre ellas |
| 📤 **Importar/Exportar** | Exporta e importa exámenes, aulas o proyecto completo en JSON |
| 🎨 **Colores personalizados** | Cada examen puede tener un color hex personalizado |
| 🔍 **Filtros** | Filtra en tiempo real la lista de exámenes y aulas |
| 💾 **Auto-guardado** | Guarda el proyecto automáticamente cada 5 minutos |
| ↩️ **Deshacer/Rehacer** | Pila de hasta 50 estados para deshacer/rehacer cambios |
| ✅ **Validación previa** | Comprueba coherencia de datos antes de generar: alumnos vs capacidad, duración encadenable, ordenadores suficientes |
| 📋 **Exportar CSV** | Exporta el calendario generado a CSV |
| 📄 **Exportar Word** | Exporta el calendario y exámenes a .docx |
| 📝 **Exportar MD** | Exporta el calendario y exámenes a Markdown |
| 🗃️ **Plantillas** | Guarda/carga plantillas de franjas horarias |
| 📊 **Estadísticas** | Diálogo con resumen de exámenes, aulas, alumnos por estudio, 💻 ordenadores pedidos/disponibles y 🔒 franjas reservadas |
| 🖨️ **Exportar HTML** | HTML imprimible con colores por estudio y leyenda |
| 👤 **Preferencia de turno** | Exámenes pueden preferir mañana o tarde; el solver lo respeta si es posible |
| 🔒 **Bloquear asignaciones** | Bloquea un examen a una franja/aula y regenera manteniendo fijas esas asignaciones |
| 📅 **Vista semanal completa** | Alterna entre vista detalle (tarjetas) y vista completa (tabla) |
| 👨‍🏫 **Profesor por examen** | Cada examen puede tener un profesor; el solver evita solapamientos |
| 🔀 **Comparativa** | Muestra dos opciones lado a lado para comparar distribución |
| ⏳ **Indicador de carga** | Barra de progreso + botón deshabilitado mientras el solver trabaja (generar y regenerar con bloqueos) |
| 🖱️ **Menú contextual** | Clic derecho en exámenes del calendario: editar, mover, bloquear, eliminar |
| ✏️ **Editar con doble clic** | Doble clic en examen del calendario para modificar sus datos |
| 🔄 **Drag & drop** | Arrastra exámenes entre franjas; se bloquean y regeneran automáticamente |
| ⌨️ **Atajos de teclado** | Ctrl+Z, Ctrl+Y, Ctrl+Shift+Z, Ctrl+S, Ctrl+G, Ctrl+N, Ctrl+1-5, Ctrl+E, Ctrl+A, F1 |
| 📊 **Barra de estado** | Información en tiempo real (exámenes, aulas, alumnos, opciones, dirty flag) |
| 🔍 **Filtro en calendario** | Busca exámenes por nombre o estudio en el calendario generado |
| 🌙 **Tema persistente** | 3 modos (claro/oscuro/alto contraste ♿) recordados entre sesiones (config.json) |
| 💬 **Tooltips** | Todos los botones e inputs tienen tooltips descriptivos |
| 🎉 **Diálogo de bienvenida** | Guía interactiva en primer inicio con checkbox "No mostrar al inicio" |
| 📋 **Duplicar examen** | Botón 📋 junto a cada examen para duplicarlo con nombre único |
| 📋 **Duplicar aula** | Botón 📋 junto a cada aula para duplicarla con sus franjas |
| 📋 **Duplicar franjas a otro día** | Copia todas las franjas de un día a otro en el aula seleccionada |
| 🟫 **Botones CTA** | Estilo beige para acciones destacadas (regenerar con bloqueos) |
| 🗂️ **Toolbar agrupada** | Botones del calendario organizados en grupos con supertítulo (Acciones · Exportar · Bloqueos) |
| ⏱️ **Duración por examen** | `duration_hours` (horas, default 2.0): el examen ocupa varias franjas encadenadas del mismo día |
| 💻 **Ordenadores** | Examen y aula tienen `computers`; la suma por (franja, aula) no puede superar los del aula |
| 🔒 **Franjas reservadas** | Marcar franjas de un aula como reservadas (🔒 en el panel) para que no reciban exámenes |
| 🔒 **Bloquear visibles** | Botón del calendario que bloquea de golpe todos los exámenes filtrados/visibles y regenera |
| 📤 **Exportar/Importar calendario JSON** | `📤 JSON` exporta **todas las opciones + opción actual + bloqueos + exámenes + aulas** en un fichero autocontenido; `📥 Importar JSON` lo restaura (bloqueos incluidos) y, si el archivo no trae bloqueos, pregunta si quiere convertir las asignaciones importadas en bloqueos para poder regenerar con bloqueos |
| ✅ **Tests unitarios** | 57 tests: 33 del scheduler (restricciones, duración, ordenadores —incluida la casuística cap-OK/PCs-KO—, reservas, bloqueos, turno, datos semilla) + 24 del formato de calendario JSON (`calendar_io.py`) |

## Guía para generar datos de seed

### Reglas para nombres

- Usa apellidos claramente inventados (Alumnez, Profesorez, Estudiantez, etc.) para evitar confusiones con personas reales
- Nombres de exámenes descriptivos pero cortos

### Para generar datos realistas

- **Estudios:** Ciclos Formativos de Grado Superior (GS). Ej: "Administración y Finanzas (GS)", "Informática (GS)", "Turismo (GS)", "Comercio Internacional (GS)"
- **Alumnos por examen:** entre 15 y 35 para GS
- **Aulas:** capacidad entre 25 y 100 según el espacio
- **Franjas por aula:** entre 3 y 15 franjas. Fechas en periodo de exámenes (ej: junio)
- **Franjas típicas:** mañana 09:00-11:00, 11:30-13:30; tarde 16:00-18:00
- **Ratio exámenes/aulas:** aprox 2-4 exámenes por aula para que el solver tenga trabajo
- **Al menos 3-4 estudios diferentes** para que las restricciones de solapamiento tengan sentido
- **Colores:** usa códigos hex como `#6366f1`, `#ef4444`, `#10b981`, `#8b5cf6`, etc.
- **Ordenadores:** añade 2-3 aulas con `computers` de ratios distintos (p.ej. capacidad 30/PCs 15, 32/30, 45/25) y exámenes con `computers` **repartidos en al menos 3 estudios** (no solo Informatica, para que la restricción de suma tenga efecto). Casos que debe cubrir: **aula con capacidad suficiente pero pocos PCs** (capacidad OK / PCs KO), **examen con menos PCs que alumnos**, y **una pareja de distinto estudio que quepa por alumnos en el aula grande pero no por la suma de PCs**
- **Franjas encadenadas:** incluye franjas de 1h contiguas (09:00-10:00, 10:00-11:00, 11:00-12:00) en algún aula para poder colocar un examen largo de 3 h
- **Franjas reservadas:** marca al menos una franja como `reserved: true` para probar esa restricción
- **Examen largo:** un examen con `duration_hours: 3.0` en una franja encadenada

### Formato de seed_data.py

```python
SEED_PROJECT_NAME = "Nombre del Proyecto"

SEED_CLASSROOMS = [
    {
        "name": "Laboratorio 1",
        "capacity": 32,
        "computers": 30,
        "time_slots": [
            {"date": "2026-06-15", "start": "09:00", "end": "11:00"},
            {"date": "2026-06-18", "start": "09:00", "end": "10:00"},
            {"date": "2026-06-18", "start": "10:00", "end": "11:00"},
            {"date": "2026-06-15", "start": "16:00", "end": "18:00", "reserved": True},
        ],
    },
]

SEED_EXAMS = [
    {"name": "Mi Examen (Alumnez Apellido)", "students": 25, "study": "Mi Ciclo (GS)",
     "color": "#6366f1", "preferred_shift": "morning", "teacher": "Profesorez Nombre",
     "duration_hours": 2.0, "computers": 25},
]

def get_seed_data():
    import copy
    return {
        "project_name": SEED_PROJECT_NAME,
        # deepcopy de time_slots: si no, mutar `reserved` en la app
        # alteraría las constantes del módulo
        "classrooms": [dict(c, time_slots=copy.deepcopy(c["time_slots"]))
                       for c in SEED_CLASSROOMS],
        "exams": [dict(e) for e in SEED_EXAMS],
    }
```

## Notas para la IA

- El campo `color` en exámenes es **opcional**. Si no se incluye, se asigna automáticamente según el estudio.
- El proyecto guarda automáticamente en `projects/` como JSON y exporta HTML, Word y MD a `output/`.
- El solver usa CP-SAT con restricciones de no-good cuts para generar opciones diversas.
- Los filtros de búsqueda son case-insensitive y buscan en nombre y estudio.
- El auto-guardado ocurre cada 5 minutos solo si hay cambios sin guardar.
- La **configuración persistente** (modo oscuro) se guarda en `config.json` junto al proyecto.
- Los **atajos de teclado** usan `QShortcut` con `QKeySequence` (Ctrl+Z, Ctrl+S, Ctrl+G, Ctrl+1-5, etc.).
- La **barra de estado** se actualiza via `_update_status()` cada vez que cambian los datos.
- Los **placeholders** de pestañas vacías se gestionan con `setVisible()` según el contenido.
- El **filtro del calendario** filtra las asignaciones antes de renderizar (detalle, completa y comparativa).
- **python-docx** es ahora dependencia obligatoria para exportar a Word.
- **PNG** fue reemplazado por **Markdown** como formato de exportación ligero.
- Los campos nuevos (`duration_hours`, `computers` en examen/aula, `reserved` en franja) son **opcionales**: proyectos JSON antiguos se cargan sin cambios (defaults 2.0 h, 0 PCs, franja libre).
- El **calendario exportado con 📤 JSON** (`calendar_io.py`) usa formato `{"format": "calendario-examenes", "version": 1, ...}` con **referencias por nombre/fecha** (no índices internos): `options[]` con todas las opciones (`slots_used` + `assignments[]` de `{exam, classroom, slots[]}`), `current_option`, `locks[]` (`{exam, classroom, date, start, end}`) y, opcionalmente, `exams`/`classrooms` completos. `parse_calendar()` rechaza el JSON de **proyecto** (`{"project_name", ...}`) con un mensaje indicando usar 📥 Importar de la pestaña Proyecto. Si el archivo no trae `locks`, la GUI pregunta si convertir las asignaciones de la opción actual en bloqueos.
- Tests: `venv/bin/python run_tests.py` (unittest, ~60 s; los de datos semilla resuelven el CP-SAT completo).
- Cada asignación del calendario lleva `slots` (lista de franjas del bloque), `slot_label` (`"YYYY-MM-DD HH:MM-HH:MM"` real) y `exam_idx`/`block` para edición posterior.
- En la vista completa, un examen de varias horas aparece con la tarjeta en su franja de inicio y `↳ <examen> (continúa)` en las siguientes; el HTML usa `↳ continua:` en la celda.
- La **estadística** y la **barra de estado** muestran 💻 `pedidos/disponibles` (suma sobre todos los exámenes) y 🔒 nº de franjas reservadas.

## Patrones UI

- **Tamaño de fuente global**: `BASE_FONT_PT = 11` (gui.py) sube la base de 9 pt (default Qt) — se aplica en `ensure_emoji_fonts()` al arrancar — y **todos** los literales `font-size: Npx` del QSS/estilos inline están a **+2 px** respecto al original. Al re-tocar fuentes: comprobar que ninguna fila de botones desborde (medir `layout.minimumSize().width()` vs viewport, o que aparezca un `QScrollBar` horizontal visible con `maximum() > 0`) a **1280×720**. Por eso la toolbar del calendario está en **3 filas** (acciones · vista · bloqueos) y el formulario de exámenes en 2 (turno + botón en la 2.ª); con la fuente antigua cabía en menos filas.
- **Iconos = emoji**: la app usa emoji como iconos. Sin familia de emoji explícita, fontconfig ordena fuentes monócromas (Symbola / Noto Sans Symbols2) antes que `Noto Color Emoji` y los iconos salen en negro → invisibles en el tema oscuro. `ensure_emoji_fonts()` (gui.py) añade las familias de emoji al final de la lista global de la aplicación, y todo `font-family` de QSS debe llevar la lista completa (ej. `Consolas, 'Noto Color Emoji', Symbola`), porque un `font-family` de una sola familia rompe el fallback de emoji de ese widget.
- Los botones de borrar (X roja) usan **QLabel** con `mousePressEvent` en lugar de QPushButton para evitar doble renderizado del emoji ❌.
- Los estilos `cursor:pointer` en QSS/Qt Style Sheets NO funcionan (Qt no soporta `cursor` en CSS). Usar `setCursor()` en su lugar.
- La pestaña Proyecto usa `_mkbtn()` como helper para crear botones (no cierra sobre vars del closure).
- Para layouts que desbordan en 1280×720: dividir filas largas en múltiples filas, combinar secciones relacionadas (filtro + export/import en una fila, presets + plantillas en una fila).
- **Estados de control en QSS**: todo control interactivo tiene `:hover`, `:pressed` y **`:focus`** con `border-color` de acento (ancho fijo a 1 px en todos los estados para que el foco **no desplace el layout**) y `:disabled` con fondo/gris legibles (`#e2e8f0`/`#64748b` en claro, `#1e293b`/`#94a3b8` en oscuro). No usar `border: none` en QPushButton primario: llevar `border: 1px solid transparent` para que el resto de estados solo cambien color.
- **Contraste del texto secundario**: `C_SLATE_L = "#64748b"` en claro (4.8:1) y `C_SLATE = "#94a3b8"` en oscuro (7:1); se elige con `App._slate()`. `_apply_theme()` llama a `_restyle_secondary_labels()` para repintar placeholders/resúmenes (y `_update_calendar_tab()` si hay calendario, porque sus labels RichText se pintan al renderizar). Si un label ya fue destruido, `setStyleSheet` lanza `RuntimeError`: se captura y se anula el atributo.
- **Labels de una línea en RichText** (tarjetas del calendario, `_make_exam_card_detail` y el `info` de la vista compacta) sin `setWordWrap(True)` imponen `minimumSizeHint().width()` = ancho total del texto y provocan un `QScrollBar` horizontal en la pestaña Calendario; llevar siempre `setWordWrap(True)` + `setMinimumWidth(0)` en esos labels.
- Los botónes de borrar en listas usan QLabel con fondo `#fee2e2`, borde `#ef4444`, size 28×24px, font-size 13px.
