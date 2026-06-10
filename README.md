# 📅🎓 Generador de Calendario de Exámenes ⚡

**Generador inteligente de calendarios de exámenes mediante optimización CP-SAT.**

![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)
![OR-Tools](https://img.shields.io/badge/OR--Tools-CP--SAT-EA4335?logo=google&logoColor=white)
![PyQt6](https://img.shields.io/badge/UI-PyQt6-6366f1)
![License](https://img.shields.io/badge/License-GPLv3-blue.svg)

---

## 🚀 ¿Qué hace?

Planifica exámenes en aulas respetando restricciones reales de centros educativos:

- **Mismo estudio ≠ misma franja** — exámenes del mismo ciclo no pueden coincidir
- **Aulas compartidas** — diferentes estudios usan el mismo aula si hay capacidad
- **Disponibilidad real** — cada aula tiene franjas concretas donde está disponible
- **Franjas con fecha/hora** — slots con fecha real (YYYY-MM-DD) y hora de inicio/fin
- **Múltiples opciones** — genera hasta 5 calendarios alternativos y elige el que prefieras
- **Proyectos** — guarda y carga configuraciones completas (exámenes, aulas, franjas)
- **Optimiza** usando el mínimo de franjas necesario

## ✨ Características principales

| Característica | Descripción |
|---|---|
| 📋 **Exámenes por estudio** | Agrupa exámenes por ciclo formativo |
| 🏫 **Aulas con capacidad** | Define aulas y su aforo máximo |
| 🕐 **Franjas por aula** | Cada aula tiene su propio horario disponible |
| 🧠 **Solver CP-SAT** | Optimización combinatoria de Google OR-Tools |
| 🔀 **Múltiples soluciones** | Genera varias opciones y elige la mejor |
| 💾 **Proyectos guardables** | Persistencia en JSON |
| 🖨️ **Imprimible como PDF** | Exporta el calendario a HTML/PDF |
| 🌗 **Tema claro/oscuro** | Interfaz adaptable |

## 📦 Instalación

```bash
pip install -r requirements.txt
```

## 🖥️ Uso

```bash
python main.py
```

### Flujo de trabajo

1. **🏠 Proyecto** — Crea o selecciona un proyecto (se guardan automáticamente como JSON)
2. **📋 Exámenes** — Añade exámenes: nombre, alumnos y estudio
3. **🏫 Aulas** — Define aulas con capacidad y franjas de disponibilidad
4. **⚙️ Generar** — El solver CP-SAT asigna todo respetando restricciones
5. **🔀 Elegir opción** — Selecciona entre múltiples calendarios generados
6. **📅 Calendario** — Abre el HTML en el navegador e imprime como PDF

### Datos de ejemplo

Incluye datos de ejemplo con **5 días laborables de junio 2026**:

- **6 aulas** con diferente disponibilidad
- **16 exámenes** de 4 Ciclos Formativos de Grado Superior
- **15 franjas** (3 por día, 5 días)

## 🧠 Solver

Usa **Google OR-Tools CP-SAT** para optimización combinatoria:

```
Variables:  x[e, t, c] = 1 si examen e → franja t → aula c
Restricciones:
  • Cada examen → exactamente una (franja, aula)
  • Mismo estudio → franjas diferentes
  • Alumnos en (franja, aula) ≤ capacidad del aula
  • Aula solo disponible en sus franjas permitidas
Objetivo:  minimizar número de franjas usadas
```

### Generación de múltiples soluciones

El algoritmo genera opciones diversas añadiendo **restricciones de bloqueo** incrementales:

1. Resuelve el modelo base (solución óptima)
2. Añade una restricción que bloquea la combinación exacta de asignaciones anteriores
3. Vuelve a resolver forzando una distribución diferente
4. Repite hasta obtener el número deseado de opciones (máx. 5)

## 🗂️ Estructura del proyecto

```
📁 GeneradorHorariosExamenes/
├── main.py              # Punto de entrada
├── gui.py               # Interfaz PyQt6
├── scheduler.py         # Solver CP-SAT
├── html_exporter.py     # Exportador HTML
├── seed_data.py         # Datos de ejemplo
├── index.html           # Página de inicio
├── requirements.txt     # Dependencias
└── lanzar.bat           # Script de lanzamiento
```

## 📄 Licencia

GNU General Public License v3.0 — ver el archivo [LICENSE](LICENSE) para más detalles.
