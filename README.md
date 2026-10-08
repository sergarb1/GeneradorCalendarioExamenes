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
- **Duración configurable** — cada examen dura N horas y ocupa franjas encadenadas del mismo día
- **Ordenadores** — exámenes que necesitan PCs solo van a aulas con suficientes ordenadores libres
- **Franjas reservadas** — puedes reservar franjas de un aula para que queden vacías
- **Múltiples opciones** — genera N calendarios alternativos y cambia entre ellos libremente
- **Proyectos** — guarda y carga configuraciones completas (exámenes, aulas, franjas)
- **Importar/Exportar** — importa y exporta exámenes y aulas por separado o todo el proyecto
- **Calendario portable** — exporta el calendario generado (todas las opciones + bloqueos) a JSON autocontenido y lo restaura en otra sesión
- **Optimiza** usando el mínimo de franjas necesario

## ✨ Características principales

| Característica | Descripción |
|---|---|
| 📋 **Exámenes por estudio** | Agrupa exámenes por ciclo formativo |
| 🏫 **Aulas con capacidad** | Define aulas y su aforo máximo |
| 🕐 **Franjas por aula** | Cada aula tiene su propio horario disponible |
| ⏱️ **Duración por examen** | Horas por examen; ocupa franjas encadenadas contiguas |
| 💻 **Ordenadores** | Suma de PCs por (franja, aula) ≤ PCs del aula |
| 🔒 **Franjas reservadas** | 🔒 en el panel del aula: la franja queda sin exámenes |
| 🔒 **Bloquear visibles** | Bloquea de golpe todos los exámenes filtrados |
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
| 📊 **Estadísticas** | Resumen: alumnos por estudio, 💻 PCs pedidos/disponibles y 🔒 franjas reservadas |
| 💾 **Auto-guardado** | Cada 5 minutos si hay cambios |
| 📋 **Exportar CSV** | Calendario a CSV |
| 📄 **Exportar Word** | Documento .docx con tabla de asignaciones |
| 📝 **Exportar MD** | Markdown del calendario y lista de exámenes |
| 📤 **Calendario JSON** | Exporta **todas las opciones + opción actual + bloqueos** en un JSON autocontenido; `📥 Importar JSON` lo restaura (y pregunta si convertir las asignaciones en bloqueos si el archivo no los trae) |
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
| 🔤 **Tipografía legible** | Fuente base 11 pt (Qt trae 9 pt) y tamaños +2 px en toda la interfaz |
| 🎯 **Estados visibles** | Hover/focus/disabled en todos los botones, inputs y combos; texto secundario con contraste WCAG (4.8:1 claro · 7:1 oscuro) |

## 📦 Instalación

```bash
pip install -r requirements.txt
```

## 🖥️ Uso

```bash
python main.py
```

- **Windows:** doble clic en `lanzar.bat`
- **Linux/macOS:** `./lanzar.sh`
- **Primera vez:** en 🏠 Proyecto pulsa **"📂 Cargar datos de ejemplo"** (8 aulas, 34 exámenes) para probar al instante.

### Flujo de trabajo

1. **🏠 Proyecto** — Crea o selecciona un proyecto. Auto-guardado cada 5 min. Deshacer/Rehacer.
2. **📋 Exámenes** — Añade exámenes: nombre, alumnos, estudio, profesor, color, preferencia de turno, **duración en horas** y **ordenadores necesarios**. Importa/exporta JSON.
3. **🏫 Aulas** — Define aulas con capacidad, **ordenadores** y franjas. Reserva franjas con 🔒 para que queden libres. Guarda/carga plantillas de horarios. Importa/exporta.
4. **⚙️ Generar** — Configura N opciones y pulsa generar. Validación previa de coherencia de datos (capacidad, duración, ordenadores, franjas reservadas). Barra de progreso mientras el solver trabaja.
5. **📅 Calendario** — Cambia entre opciones, bloquea asignaciones (o **🔒 Bloquear visibles** de golpe) y regenera con bloqueos, alterna vista completa/detalle, compara dos opciones lado a lado, arrastra exámenes entre franjas. Exporta a HTML, Word, MD, CSV o **JSON autocontenido (📤 JSON)** y lo vuelves a importar con **📥 Importar JSON**.

### Datos de ejemplo

Incluye datos de ejemplo con **5 días laborables de junio 2026**:

- **8 aulas** (5 aulas/salones + **3 aulas con ordenadores**: 2 laboratorios y Aula 4 con PCs parciales)
- **34 exámenes** de 6 Ciclos Formativos de Grado Superior
- **95 franjas** en total, incluidas franjas **encadenadas de 1 h** (para un examen de **3 h**) y **1 franja reservada**
- 5 exámenes que necesitan **ordenadores**, repartidos en **3 ciclos distintos** (la restricción de suma de PCs decide)
- Nombres con **apellidos inventados** (Alumnez, Profesorez, etc.)

> Los campos nuevos (`duration_hours`, `computers`, `reserved`) son **opcionales**: los proyectos JSON guardados con versiones anteriores se cargan igual (defaults 2 h, 0 PCs, franja libre).

## 🧠 Solver

Usa **Google OR-Tools CP-SAT** para optimización combinatoria:

```
Variables:  x[e, b] = 1 si examen e → bloque b (franja de inicio + franjas
                       consecutivas que cubren su duration_hours)
Restricciones:
  • Cada examen → exactamente un bloque (franjas encadenadas del mismo día)
  • Mismo estudio → no solaparse en ninguna franja
  • Mismo profesor → no solaparse en ninguna franja
  • Alumnos en (franja, aula) ≤ capacidad del aula
  • Ordenadores en (franja, aula) ≤ ordenadores del aula
  • Aula solo disponible en sus franjas permitidas (las reservadas no se usan)
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
2. O usa **🔒 Bloquear visibles** para bloquear de golpe todos los exámenes que se ven (tras filtrar con la lupa)
3. Pulsa **Regenerar con bloqueos** para re-ejecutar el solver
4. El solver mantiene fijas las asignaciones bloqueadas y recoloca el resto
5. Los exámenes bloqueados se muestran con borde dorado en el calendario
6. Usa **Limpiar bloqueos** para desbloquear todos

Esto permite ajustar manualmente el calendario cuando hay preferencias específicas.
Si un bloqueo deja de ser válido (p. ej. cambias la duración), la app te lo avisa.

## 👨‍🏫 Restricción de profesor

Cada examen puede tener un **profesor** asignado (campo opcional). El solver garantiza que:

- Un mismo profesor **no puede estar en dos exámenes** que coincidan en la misma franja horaria
- Esto funciona **entre estudios diferentes** (un profesor puede impartir en varios ciclos)
- Si no se asigna profesor, no hay restricción

## ⏱️ Duración de los exámenes

Cada examen tiene un campo **`duration_hours`** (horas, por defecto 2.0):

- El examen ocupa **varias franjas encadenadas** del mismo día: la `end` de una debe coincidir con la `start` de la siguiente (sin huecos ni descansos)
- Ej.: 3 h con franjas 09:00-10:00, 10:00-11:00 y 11:00-12:00 → ocupa las tres
- Si no existe una cadena lo bastante larga en esa aula/día, el examen no se puede colocar allí
- En el calendario la primera franja muestra la **tarjeta** y las siguientes muestran `↳ … (continúa)`

## 💻 Ordenadores

Tanto el examen (`computers`) como el aula (`computers`) pueden indicar **número de ordenadores**:

- La suma de PCs de los exámenes asignados a la misma **(franja, aula)** nunca puede superar los PCs del aula
- Un examen con `computers: 0` (default) puede ir a cualquier aula
- En la tabla HTML y en las exportaciones se muestra el símbolo 💻 con los PCs

## 🔒 Franjas reservadas

En el panel de franjas de cada aula, el botón 🔒 **reserva** una franja:

- El solver **nunca** asigna exámenes a una franja reservada
- Una franja reservada **rompe las cadenas**: no sirve para cubrir la duración de un examen largo
- Hay botones para **reservar todas** / **liberar todas** las franjas del aula
- En las estadísticas se cuenta cuántas franjas están reservadas

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
├── md_exporter.py       # Exportación a Markdown
├── word_exporter.py     # Exportación a Word (.docx)
├── calendar_io.py       # Export/import del calendario a JSON autocontenido
├── seed_data.py         # Datos de ejemplo ficticios
├── tests/               # Tests unitarios (unittest)
├── run_tests.py         # Runner de tests
├── index.html           # Página de documentación
├── manual.html          # Manual de usuario
├── prompts_generar_examenes_aulas_JSON.md  # Prompts para generar datos/JSON
├── AGENTS.md            # Guía para IA sobre el modelo de datos
├── requirements.txt     # Dependencias
├── lanzar.bat           # Script de lanzamiento rápido (Windows)
├── lanzar.sh            # Script de lanzamiento rápido (Linux/macOS)
├── projects/            # Proyectos guardados (JSON)
└── output/              # HTML generados
```

### Archivos clave

| Archivo | Descripción |
|---|---|
| `main.py` | Punto de entrada — configura la app PyQt6 y lanza la ventana |
| `gui.py` | Toda la interfaz gráfica: pestañas, formularios, import/export |
| `scheduler.py` | Modelo CP-SAT con bloques, restricciones y objetivo |
| `html_exporter.py` | Genera HTML profesional del calendario con tabla y leyenda |
| `md_exporter.py` / `word_exporter.py` | Exportación del calendario a Markdown y .docx |
| `calendar_io.py` | Export/import del calendario generado (todas las opciones + bloqueos) a JSON autocontenido |
| `seed_data.py` | Datos ficticios de ejemplo para pruebas |
| `tests/test_scheduler.py` | Tests del motor (restricciones, duración, PCs, reservas, bloqueos) |
| `tests/test_calendar_io.py` | Tests del formato de calendario JSON (roundtrip, omisiones, bloqueos) |
| `manual.html` | Manual interactivo (presentación reveal.js) |
| `index.html` | Página de documentación del proyecto |

## ✅ Tests

```bash
python run_tests.py          # o: venv/bin/python run_tests.py
```

57 tests unittest: 33 del scheduler (restricciones básicas, duración en horas,
ordenadores —incluida la casuística cap-OK/PCs-KO—, franjas reservadas,
bloqueos, preferencia de turno y solubilidad de los datos de ejemplo) y 24
del formato de calendario JSON (`calendar_io.py`: roundtrip, omisiones,
avisos y bloqueos) (~60 s; los que resuelven el seed completo con CP-SAT).

## 🌐 Enlaces

| Recurso | URL |
|---|---|
| 🌐 GitHub Pages | [https://sergarb1.github.io/GeneradorCalendarioExamenes/](https://sergarb1.github.io/GeneradorCalendarioExamenes/) |
| 📘 Manual interactivo | [https://sergarb1.github.io/GeneradorCalendarioExamenes/manual.html](https://sergarb1.github.io/GeneradorCalendarioExamenes/manual.html) |
| 🐙 Repositorio GitHub | [https://github.com/sergarb1/GeneradorCalendarioExamenes](https://github.com/sergarb1/GeneradorCalendarioExamenes) |

## 📄 Licencia

GNU Affero General Public License v3.0 — ver el archivo [LICENSE](LICENSE) para más detalles.
