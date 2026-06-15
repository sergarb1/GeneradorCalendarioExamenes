# 📅🎓 Generador de Calendario de Exámenes ⚡

**Generador inteligente de calendarios de exámenes mediante optimización CP-SAT.**

[🌐 GitHub Pages](https://sergarb1.github.io/GeneradorCalendarioExamenes/) |
[📘 Manual interactivo](https://sergarb1.github.io/GeneradorCalendarioExamenes/manual.html) |
[🐙 Repositorio](https://github.com/sergarb1/GeneradorCalendarioExamenes)

![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)
![OR-Tools](https://img.shields.io/badge/OR--Tools-CP--SAT-EA4335?logo=google&logoColor=white)
![PyQt6](https://img.shields.io/badge/UI-PyQt6-6366f1)
![License](https://img.shields.io/badge/License-AGPLv3-blue.svg)

---

## 🚀 ¿Qué hace?

Planifica exámenes en aulas respetando restricciones reales de centros educativos:

- **Mismo estudio ≠ misma franja** — exámenes del mismo ciclo no pueden coincidir
- **Aulas compartidas** — diferentes estudios usan el mismo aula si hay capacidad
- **Disponibilidad real** — cada aula tiene franjas concretas donde está disponible
- **Franjas con fecha/hora** — slots con fecha real (YYYY-MM-DD) y hora de inicio/fin
- **Múltiples opciones** — genera N calendarios alternativos y cambia entre ellos libremente
- **Proyectos** — guarda y carga configuraciones completas (exámenes, aulas, franjas)
- **Importar/Exportar** — importa y exporta exámenes y aulas por separado o todo el proyecto
- **Optimiza** usando el mínimo de franjas necesario

## ✨ Características principales

| Característica | Descripción |
|---|---|
| 📋 **Exámenes por estudio** | Agrupa exámenes por ciclo formativo |
| 🏫 **Aulas con capacidad** | Define aulas y su aforo máximo |
| 🕐 **Franjas por aula** | Cada aula tiene su propio horario disponible |
| 🧠 **Solver CP-SAT** | Optimización combinatoria de Google OR-Tools |
| 🔀 **Múltiples soluciones** | Genera N opciones y cambia entre ellas sin perder ninguna |
| 💾 **Proyectos guardables** | Persistencia en JSON (projects/) |
| 📤 **Importar/Exportar** | Importa y exporta exámenes, aulas o el proyecto completo |
| 🖨️ **Imprimible como PDF** | Exporta el calendario a HTML/PDF |
| 🌗 **Tema claro/oscuro** | Interfaz adaptable |
| 🎨 **Colores personalizados** | Color hex por examen con selector |
| 👤 **Preferencia de turno** | Exámenes prefieren mañana o tarde |
| 🔒 **Bloquear asignaciones** | Fija un examen a franja/aula y regenera |
| 🔍 **Filtros** | Búsqueda en tiempo real en listas |
| ↩️ **Deshacer/Rehacer** | Pila de 50 estados |
| 📊 **Estadísticas** | Diálogo con resumen alumnos/estudio |
| 💾 **Auto-guardado** | Cada 5 minutos si hay cambios |
| 📋 **Exportar CSV** | Calendario a CSV |
| 📄 **Exportar Word** | Documento .docx con tabla de asignaciones |
| 📝 **Exportar MD** | Markdown del calendario y lista de exámenes |
| 🗃️ **Plantillas de franjas** | Guarda/carga patrones de horarios |
| 📅 **Vista semanal completa** | Alterna detalle ↔ tabla |
| 👨‍🏫 **Profesor por examen** | Asigna profesor; el solver evita solapamientos |
| 🔀 **Comparativa** | Dos opciones lado a lado |
| ⏳ **Indicador de carga** | Barra de progreso mientras el solver trabaja |
| 🖱️ **Menú contextual** | Clic derecho sobre exámenes: editar, mover, bloquear, eliminar |
| ✏️ **Editar con doble clic** | Doble clic en examen del calendario para editarlo |
| 🔄 **Drag & drop** | Arrastra exámenes entre franjas, se bloquean y regeneran |
| ⌨️ **Atajos de teclado** | Ctrl+Z, Ctrl+S, Ctrl+G, Ctrl+1-5, Ctrl+E, Ctrl+A |
| 📊 **Barra de estado** | Info en tiempo real: exámenes, aulas, alumnos, opciones |
| 🔍 **Filtro en calendario** | Busca exámenes por nombre/estudio en el calendario |
| 🌙 **Tema persistente** | Modo oscuro recordado entre sesiones |

## 📦 Instalación

```bash
pip install -r requirements.txt
```

## 🖥️ Uso

```bash
python main.py
```

### Flujo de trabajo

1. **🏠 Proyecto** — Crea o selecciona un proyecto. Auto-guardado cada 5 min. Deshacer/Rehacer.
2. **📋 Exámenes** — Añade exámenes: nombre, alumnos, estudio, profesor, color y preferencia de turno. Importa/exporta JSON.
3. **🏫 Aulas** — Define aulas con capacidad y franjas. Guarda/carga plantillas de horarios. Importa/exporta.
4. **⚙️ Generar** — Configura N opciones y pulsa generar. Validación previa de coherencia de datos. Barra de progreso mientras el solver trabaja.
5. **📅 Calendario** — Cambia entre opciones, bloquea asignaciones y regenera con bloqueos, alterna vista completa/detalle, compara dos opciones lado a lado, arrastra exámenes entre franjas. Exporta a HTML, Word, MD, CSV o PNG.

### Datos de ejemplo

Incluye datos de ejemplo con **5 días laborables de junio 2026**:

- **6 aulas** con diferente disponibilidad
- **33 exámenes** de 5 Ciclos Formativos de Grado Superior
- **15 franjas** (3 por día, 5 días)
- Nombres con **apellidos inventados** (Alumnez, Profesorez, etc.)

## 🧠 Solver

Usa **Google OR-Tools CP-SAT** para optimización combinatoria:

```
Variables:  x[e, t, c] = 1 si examen e → franja t → aula c
Restricciones:
  • Cada examen → exactamente una (franja, aula)
  • Mismo estudio → franjas diferentes
  • Mismo profesor → franjas diferentes
  • Alumnos en (franja, aula) ≤ capacidad del aula
  • Aula solo disponible en sus franjas permitidas
  • Preferencia de turno (blanda, penalización ×100)
Objetivo:  minimizar número de franjas usadas + violaciones de preferencia
```

### Generación de múltiples soluciones

El algoritmo genera opciones diversas añadiendo **restricciones de bloqueo** incrementales:

1. Resuelve el modelo base (solución óptima)
2. Añade una restricción que bloquea la combinación exacta de asignaciones anteriores
3. Vuelve a resolver forzando una distribución diferente
4. Repite hasta obtener el número deseado de opciones (configurable)
5. Todas las opciones se exportan a HTML y se pueden consultar en cualquier momento

## 🔐 Bloqueo de asignaciones

Puedes **bloquear** un examen a una franja y aula concretos desde la vista del calendario:

1. Pulsa el botón 🔓 junto a un examen para **bloquearlo** a su franja/aula actual (cambia a 🔒)
2. Pulsa **Regenerar con bloqueos** para re-ejecutar el solver
3. El solver mantiene fijas las asignaciones bloqueadas y recoloca el resto
4. Los exámenes bloqueados se muestran con borde dorado en el calendario
5. Usa **Limpiar bloqueos** para desbloquear todos

Esto permite ajustar manualmente el calendario cuando hay preferencias específicas.

## 👨‍🏫 Restricción de profesor

Cada examen puede tener un **profesor** asignado (campo opcional). El solver garantiza que:

- Un mismo profesor **no puede estar en dos exámenes** que coincidan en la misma franja horaria
- Esto funciona **entre estudios diferentes** (un profesor puede impartir en varios ciclos)
- Si no se asigna profesor, no hay restricción

## ⏳ Indicador de carga

Cuando el solver está trabajando:
- El botón de generar se deshabilita y muestra "⏳ Generando..."
- Aparece una **barra de progreso indeterminada**
- También funciona al **regenerar con bloqueos**
- Al terminar (éxito o fallo), se restaura el botón y se oculta la barra

## 🗂️ Estructura del proyecto

```
📁 GeneradorCalendarioExamenes/
├── main.py              # Punto de entrada
├── gui.py               # Interfaz PyQt6 (pestañas, formularios, lógica)
├── scheduler.py         # Motor CP-SAT (modelo matemático + solver)
├── html_exporter.py     # Generación de HTML del calendario
├── seed_data.py         # Datos de ejemplo ficticios
├── index.html           # Página de documentación
├── AGENTS.md            # Guía para IA sobre el modelo de datos
├── requirements.txt     # Dependencias
├── lanzar.bat           # Script de lanzamiento rápido (Windows)
├── projects/            # Proyectos guardados (JSON)
└── output/              # HTML generados
```

### Archivos clave

| Archivo | Descripción |
|---|---|
| `main.py` | Punto de entrada — configura la app PyQt6 y lanza la ventana |
| `gui.py` | Toda la interfaz gráfica: pestañas, formularios, import/export |
| `scheduler.py` | Modelo CP-SAT con variables, restricciones y objetivo |
| `html_exporter.py` | Genera HTML profesional del calendario con tabla y leyenda |
| `seed_data.py` | Datos ficticios de ejemplo para pruebas |
| `manual.html` | Manual interactivo (presentación reveal.js) |
| `index.html` | Página de documentación del proyecto |

## 🌐 Enlaces

| Recurso | URL |
|---|---|
| 🌐 GitHub Pages | [https://sergarb1.github.io/GeneradorCalendarioExamenes/](https://sergarb1.github.io/GeneradorCalendarioExamenes/) |
| 📘 Manual interactivo | [https://sergarb1.github.io/GeneradorCalendarioExamenes/manual.html](https://sergarb1.github.io/GeneradorCalendarioExamenes/manual.html) |
| 🐙 Repositorio GitHub | [https://github.com/sergarb1/GeneradorCalendarioExamenes](https://github.com/sergarb1/GeneradorCalendarioExamenes) |

## 📄 Licencia

GNU Affero General Public License v3.0 — ver el archivo [LICENSE](LICENSE) para más detalles.
