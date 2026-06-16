# AGENTS — Generador de Calendario de Exámenes

## Resumen del proyecto

App Python (PyQt6) que usa Google OR-Tools CP-SAT para asignar exámenes a franjas horarias y aulas, respetando restricciones de capacidad y estudios simultáneos.

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
html_exporter.py   — Generación de HTML del calendario
seed_data.py       — Datos de ejemplo ficticios
index.html         — Página de documentación
AGENTS.md          — Esta guía para IA
lanzar.bat         — Script de lanzamiento rápido (Windows)
projects/          — Proyectos guardados (JSON)
output/            — HTML generados
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
  "teacher": "Nombre del Profesor"
}
```

- `name`: nombre del examen
- `students`: número entero de alumnos
- `study`: nombre del estudio / ciclo formativo
- `color`: (opcional) color personalizado en hex. Si no se especifica, se asigna automáticamente según el estudio.
- `preferred_shift`: (opcional) `"morning"` o `"afternoon"`. El solver lo respeta si es posible (penalización en objetivo).
- `teacher`: (opcional) nombre del profesor. El solver evita que un mismo profesor tenga dos exámenes en la misma franja.

### Aula (`classrooms` en JSON)

```json
{
  "name": "Nombre del aula",
  "capacity": 30,
  "time_slots": [
    {"date": "2026-06-15", "start": "09:00", "end": "11:00"},
    {"date": "2026-06-15", "start": "11:30", "end": "13:30"}
  ]
}
```

- `name`: identificador único del aula
- `capacity`: capacidad máxima de alumnos
- `time_slots`: lista de franjas disponibles (cada una con date, start, end)

### Franja horaria (`time_slot`)

- `date`: formato `YYYY-MM-DD`
- `start`: formato HH:MM (24h)
- `end`: formato HH:MM (24h)

## Restricciones del solver

1. Cada examen se asigna a exactamente una (franja, aula)
2. Exámenes del mismo estudio NO pueden coincidir en la misma franja
3. Exámenes del mismo profesor NO pueden coincidir en la misma franja
4. Suma de alumnos en (franja, aula) ≤ capacidad del aula
5. Aula solo disponible en sus franjas definidas
6. Objetivo: minimizar el número de franjas utilizadas

## Funcionalidades implementadas

| Funcionalidad | Descripción |
|---|---|---|
| 🔀 **Múltiples opciones** | Genera N opciones (configurable, default 5) y permite cambiar entre ellas |
| 📤 **Importar/Exportar** | Exporta e importa exámenes, aulas o proyecto completo en JSON |
| 🎨 **Colores personalizados** | Cada examen puede tener un color hex personalizado |
| 🔍 **Filtros** | Filtra en tiempo real la lista de exámenes y aulas |
| 💾 **Auto-guardado** | Guarda el proyecto automáticamente cada 5 minutos |
| ↩️ **Deshacer/Rehacer** | Pila de hasta 50 estados para deshacer/rehacer cambios |
| ✅ **Validación previa** | Comprueba coherencia de datos antes de generar (alumnos vs capacidad, etc.) |
| 📋 **Exportar CSV** | Exporta el calendario generado a CSV |
| 📄 **Exportar Word** | Exporta el calendario y exámenes a .docx |
| 📝 **Exportar MD** | Exporta el calendario y exámenes a Markdown |
| 📅 **Exportar ICS** | Exporta el calendario a iCalendar (.ics) para Google Calendar, Outlook, etc. |
| 🗃️ **Plantillas** | Guarda/carga plantillas de franjas horarias |
| 📊 **Estadísticas** | Diálogo con resumen de exámenes, aulas, alumnos por estudio |
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
| ✅ **Tests unitarios** | 15 tests del scheduler (restricciones, bloqueos, turno, datos semilla) |

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

### Formato de seed_data.py

```python
SEED_PROJECT_NAME = "Nombre del Proyecto"

SEED_CLASSROOMS = [
    {
        "name": "Aula 1",
        "capacity": 30,
        "time_slots": [
            {"date": "2026-06-15", "start": "09:00", "end": "11:00"},
        ],
    },
]

SEED_EXAMS = [
    {"name": "Mi Examen (Alumnez Apellido)", "students": 25, "study": "Mi Ciclo (GS)", "color": "#6366f1", "preferred_shift": "morning", "teacher": "Nombre del Profesor"},
]

def get_seed_data():
    return {
        "project_name": SEED_PROJECT_NAME,
        "classrooms": [dict(c) for c in SEED_CLASSROOMS],
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

## Patrones UI

- Los botones de borrar (X roja) usan **QLabel** con `mousePressEvent` en lugar de QPushButton para evitar doble renderizado del emoji ❌.
- Los estilos `cursor:pointer` en QSS/Qt Style Sheets NO funcionan (Qt no soporta `cursor` en CSS). Usar `setCursor()` en su lugar.
- La pestaña Proyecto usa `_mkbtn()` como helper para crear botones (no cierra sobre vars del closure).
- Para layouts que desbordan en 1280×720: dividir filas largas en múltiples filas, combinar secciones relacionadas (filtro + export/import en una fila, presets + plantillas en una fila).
- Los botónes de borrar en listas usan QLabel con fondo `#fee2e2`, borde `#ef4444`, size 28×24px, font-size 13px.
