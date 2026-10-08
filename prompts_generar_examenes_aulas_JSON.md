# 🤖 Prompts para generar exámenes y aulas en JSON

Fichero con prompts listos para copiar y pegar en una IA (ChatGPT, Claude,
opencode…) y que te devuelva **datos de ejemplo importables** en la app
`Generador de Calendario de Exámenes`.

Cada prompt es autocontenido: incluye el modelo de datos, las restricciones
del solver y las reglas de realismo, para que la IA no necesite leer el
código del proyecto.

---

## 📥 Cómo importar el resultado en la app

La app acepta 3 formatos (menú según dónde lo pegues):

| Formato | Estructura JSON | Dónde importar |
|---|---|---|
| **Proyecto completo** | `{"project_name": "...", "classrooms": [...], "exams": [...]}` | Pestaña **Proyecto → 📥 Importar proyecto** |
| **Solo exámenes** | `[ {...}, {...} ]` (lista) | Pestaña **📋 Exámenes → Importar** |
| **Solo aulas** | `[ {...}, {...} ]` (lista) | Pestaña **🏫 Aulas → Importar** |

> Guarda la respuesta de la IA en un `.json` (UTF-8) y impórtalo.
> **Ojo:** «Importar proyecto» **sustituye** los datos actuales; «Importar»
> en Exámenes/Aulas **añade** a los existentes.

> 📤 Hay un **4.º formato** que la IA no suele generar porque lo crea la propia
> app: el **calendario generado** (`📅 Calendario → 📤 JSON`), con formato
> `{"format": "calendario-examenes", "version": 1, ...}`. Se restaura con
> `📥 Importar JSON` (junto a los bloqueos), **no** con «Importar proyecto».
> Ver el **PROMPT 7**.

---

## 🧩 Modelo de datos (referencia)

### Examen

```json
{
  "name": "Nombre del Examen (Apellido Inventado)",
  "students": 25,
  "study": "Ciclo Formativo (GS)",
  "color": "#6366f1",
  "preferred_shift": "morning",
  "teacher": "Profesorez Nombre",
  "duration_hours": 2.0,
  "computers": 25
}
```

- `name` (obligatorio), `students` (obligatorio, entero), `study` (obligatorio)
- `color` (opcional): hex `#rrggbb`
- `preferred_shift` (opcional): `"morning"` o `"afternoon"`
- `teacher` (opcional): mismo nombre = mismo profesor (no puede solapar)
- `duration_hours` (opcional, default `2.0`): horas; ocupa franjas
  **consecutivas y contiguas** del mismo día, sin huecos
- `computers` (opcional, default `0`): ordenadores que necesita

### Aula

```json
{
  "name": "Nombre del Aula",
  "capacity": 30,
  "computers": 15,
  "time_slots": [
    {"date": "2026-06-15", "start": "09:00", "end": "11:00"},
    {"date": "2026-06-15", "start": "16:00", "end": "18:00", "reserved": true}
  ]
}
```

- `capacity` (obligatorio): aforo en alumnos
- `computers` (opcional, default `0`): ordenadores del aula
- `time_slots`: fechas `YYYY-MM-DD`, horas `HH:MM` 24 h
- `reserved: true` (opcional): franja bloqueada (no recibe exámenes y
  rompe cadenas de encadenamiento)

### Restricciones que el solver exige

1. Cada examen va a **exactamente un bloque** de franjas consecutivas del
   mismo día que cubra su `duration_hours` (si no existe hueco → no colocable).
2. Mismo `study` → nunca solapan. Mismo `teacher` → nunca solapan.
3. Suma de `students` en (franja, aula) ≤ `capacity` del aula.
4. Suma de `computers` en (franja, aula) ≤ `computers` del aula.
5. Solo se usan franjas definidas; `reserved: true` no se usa.

---

## 📋 PROMPT 1 — Proyecto completo (el más usado)

```text
Genera un proyecto de ejemplo JSON completo para una app que programa
exámenes con OR-Tools CP-SAT. Devuelve SOLO el JSON, sin explicaciones,
sin comentarios y sin ```.

FORMATO DE SALIDA (claves exactas):
{
  "project_name": "Nombre del Proyecto",
  "classrooms": [ ...aulas... ],
  "exams": [ ...exámenes... ]
}

CONTEXTO: Ciclos Formativos de Grado Superior, periodo de exámenes del
15 al 19 de junio de 2026 (5 días laborables).

EXÁMENES — esquema de cada uno:
{
  "name": "Nombre (Apellido Inventado)",
  "students": <15-35>,
  "study": "<ciclo> (GS)",
  "color": "<hex>",
  "preferred_shift": "morning" | "afternoon",   // opcional
  "teacher": "Profesorez <Nombre>",             // opcional
  "duration_hours": <1.0 | 2.0 | 3.0>,          // opcional, default 2.0
  "computers": <0 o más>                        // opcional, default 0
}

AULAS — esquema de cada una:
{
  "name": "<nombre>",
  "capacity": <25-100>,
  "computers": <0 o más>,
  "time_slots": [
    {"date": "2026-06-15", "start": "09:00", "end": "11:00"},
    {"date": "2026-06-15", "start": "16:00", "end": "18:00", "reserved": true}
  ]
}

CANTIDADES: 30-40 exámenes, 7-9 aulas, 90-110 franjas en total.
Ratio ~3-4 exámenes por aula.

REGLAS DE REALISMO (obligatorias):
- Apellidos claramente inventados (Alumnez, Profesorez, Estudiantez,
  Pérez inventado...) para no confundir con personas reales.
- 4-6 ciclos formativos distintos (ej: Administración y Finanzas (GS),
  Informática (GS), Turismo (GS), Comercio Internacional (GS),
  Integración Social (GS), Educación Infantil (GS)).
- Alumnos por examen: 15-35. Colores hex distintos por ciclo
  (ej #6366f1, #ef4444, #10b981, #8b5cf6, #f59e0b, #06b6d4).
- Franjas típicas: 09:00-11:00, 11:30-13:30 (mañana); 16:00-18:00 (tarde).
- Algunos exámenes con preferred_shift (mañana o tarde, sin exagerar).
- Profesores repetidos entre 2-4 exámenes del mismo ciclo.

CASUÍSTICA OBLIGATORIA (debe poder comprobarse en tus datos):
a) DURACIÓN: al menos un examen con duration_hours 3.0, y al menos un aula
   con franjas encadenadas de 1 h (09:00-10:00, 10:00-11:00, 11:00-12:00)
   que permita colocarlo. Ningún examen de 2 h debe caer en un aula cuyo
   hueco libre sea solo de 1 h si eso lo haría no colocable.
b) RESERVADAS: al menos 2 franjas con "reserved": true en aulas distintas.
c) ORDENADORES: 3 aulas con "computers" > 0 y ratios distintos
   (ej: capacity 30/computers 15, 32/30, 45/25 — la última es clave:
   capacidad alta pero pocos PCs).
d) ORDENADORES: 5 exámenes con "computers" > 0 repartidos en al menos
   3 ciclos distintos (NO solo Informática). Debe existir:
   - un examen con menos ordenadores que alumnos (ej 24 alumnos, 15 PCs)
   - un examen que quepa por alumnos en el aula grande pero cuya suma
     con otro de distinto ciclo NO quepa por PCs (capacidad OK / PCs KO)
e) CAPACIDAD: ningún examen con más alumnos que la mayor capacidad.
   La capacidad total de cada franja debe superar cómodamente la suma
   de alumnos de los exámenes que podrían ir ahí.

AUTOCOMPROBACIÓN ANTES DE RESPONDER (no la incluyas en la salida):
1. JSON válido (json.load sin errores), UTF-8, sin trailing commas.
2. Suma total de alumnos de todos los exámenes < suma de capacities de
   TODAS las franjas (margen mínimo 1.5x).
3. Cada examen con computers>0 tiene al menos un aula con computers >= su
   valor en alguna fecha.
4. El examen de 3 h existe y su aula tiene 3 franjas de 1 h encadenadas
   el mismo día.
5. Nº de reserved: true >= 2.
6. 5 examenes con computers>0 en >= 3 studies distintos.
```

---

## 📋 PROMPT 2 — Solo exámenes (para importar en 📋 Exámenes)

```text
Genera SOLO una lista JSON de exámenes (sin aulas) para una app que
programa exámenes con un solver CP-SAT. Devuelve únicamente el JSON
en forma de lista [ ... ], sin explicaciones ni ```.

CADA EXAMEN:
{
  "name": "Nombre (Apellido Inventado)",
  "students": <15-35>,
  "study": "<ciclo> (GS)",
  "color": "<hex>",
  "preferred_shift": "morning",     // opcional
  "teacher": "Profesorez <Nombre>", // opcional
  "duration_hours": 2.0,            // opcional
  "computers": 0                    // opcional
}

CANTIDAD: 25-35 exámenes en 4-6 ciclos distintos (mismo color por ciclo).
REALISMO: apellidos claramente inventados; profesores repetidos en 2-4
exámenes del mismo ciclo; alumnos 15-35; algún examen de 1.0 h, alguno
de 3.0 h, y 5 exámenes con computers>0 repartidos en >= 3 ciclos
(incluye uno con menos PCs que alumnos).
SIN aulas: solo la lista de exámenes.
```

---

## 📋 PROMPT 3 — Solo aulas (para importar en 🏫 Aulas)

```text
Genera SOLO una lista JSON de aulas (sin exámenes) para una app que
programa exámenes con un solver CP-SAT. Devuelve únicamente el JSON en
forma de lista [ ... ], sin explicaciones ni ```.

CADA AULA:
{
  "name": "<nombre descriptivo>",
  "capacity": <25-100>,
  "computers": <0 o más>,
  "time_slots": [
    {"date": "2026-06-15", "start": "09:00", "end": "11:00"},
    ...
  ]
}

CONTEXTO: exámenes del 15 al 19 de junio de 2026 (lun-vie).
CANTIDAD: 7-9 aulas, 90-110 franjas en total (3-15 franjas por aula).
FRANJAS típicas: 09:00-11:00, 11:30-13:30, 16:00-18:00. Formato de fecha
"YYYY-MM-DD" y horas "HH:MM" 24 h.

OBLIGATORIO:
- 3 aulas con "computers" > 0 con ratios distintos: p.ej. (30, 15),
  (32, 30) y (45, 25) — la última debe tener capacidad ALTA y pocos PCs.
- Un aula con franjas encadenadas de 1 h (09:00-10:00, 10:00-11:00,
  11:00-12:00) en un mismo día para un examen largo de 3 h.
- Al menos 2 franjas con "reserved": true en aulas distintas.
- 1 franja por tarde de algún día solo de 16:00-18:00.
- Ninguna aula con capacidad < 25.
```

---

## 📋 PROMPT 4 — Ampliar un proyecto existente

```text
Tengo este proyecto JSON de exámenes y aulas:

<PEGA_AQUÍ_EL_JSON>

Añade 8-10 exámenes NUEVOS y 1-2 aulas nuevas manteniendo el mismo formato
y las mismas reglas de los datos existentes (mismos ciclos, mismos
profesores existentes si encajan, misma paleta de colores por ciclo,
mismas franjas horarias). No modifiques ni dupliques los datos que ya
existen. Devuelve SOLO el JSON completo resultante (claves project_name,
classrooms, exams), sin explicaciones ni ```.

REQUISitos de los datos nuevos: alumnos 15-35, al menos un examen con
computers>0 en un ciclo que ya tenga exámenes sin computers, y al menos
un examen de 1.0 h que quepa en las franjas de 1 h si las hay.
```

---

## 📋 PROMPT 5 — Validar / diagnosticar un JSON

```text
Analiza este proyecto JSON de un planificador de exámenes y dime si el
solver CP-SAT podrá colocarlo todo. Devuelve una lista de problemas
concretos (o "SIN PROBLEMAS") y, si hace falta, el JSON corregido.

<PEGA_AQUÍ_EL_JSON>

Comprueba:
1. ¿Algún examen con más students que la capacity de TODAS las aulas?
2. ¿Algún examen con computers>0 al que ninguna aula con computers>=su
   valor tenga franjas en las mismas fechas?
3. ¿Algún examen de duration_hours N que no tenga N franjas consecutivas
   y contiguas (mismo día, sin huecos, sin reserved) en alguna aula?
4. ¿Suma de students de todos los exámenes < 1.5x suma total de
   capacities de todas las franjas?
5. ¿Formatos correctos: fechas YYYY-MM-DD, horas HH:MM 24h, hex #rrggbb,
   preferred_shift solo "morning"/"afternoon"?
6. ¿Franjas con start >= end? ¿Franjas solapadas dentro de la misma aula?
7. ¿nombres de aula duplicados?
```

---

## 📋 PROMPT 6 — Casuística concreta (tests / demo puntual)

```text
Genera un JSON MINIMO (lista de aulas o proyecto, indícalo) que demuestre
esta casuística concreta de restricción de ordenadores. Solo JSON:

- Un aula A: capacity 30, computers 15
- Un aula B (laboratorio): capacity 45, computers 25
- Examen X: 20 alumnos, 20 computers, ciclo "Informática (GS)"
- Examen Y: 24 alumnos, 15 computers, ciclo "Administración y Finanzas (GS)"
- Examen Z: 12 alumnos, 0 computers, ciclo "Turismo (GS)"

Con una franja por aula el mismo día, de modo que:
* X no puede ir a A (20 > 15 PCs) aunque cabe por alumnos (20 <= 30)
* X e Y caben juntos por alumnos en B (44 <= 45) pero NO por PCs (35 > 25),
  así que deben ir en franjas distintas o aulas distintas
* Y tiene menos PCs que alumnos (15 < 24)
* Z puede ir a cualquier aula
Añade una segunda franja por aula para que el solver tenga alternativas.
```

---

## 📋 PROMPT 7 — Casuística de calendario JSON (📅 → 📤 JSON / 📥 Importar JSON)

```text
Genera un JSON de CALENDARIO con formato "calendario-examenes" (NO un JSON
de proyecto), para probar el botón 📥 Importar JSON de la pestaña 📅
Calendario. Solo JSON, UTF-8, sin comentarios:

{
  "format": "calendario-examenes",
  "version": 1,
  "project_name": "Casuistica Calendario (Alumnez)",
  "current_option": 1,
  "exams": [ ... ],          // opcional: mismo modelo que PROMPT 1
  "classrooms": [ ... ],     // opcional: mismo modelo que PROMPT 1
  "options": [
    { "idx": 1, "slots_used": 4,
      "assignments": [
        { "exam": "<nombre EXACTO de exams[]>",
          "classroom": "<nombre EXACTO de classrooms[]>",
          "slots": [ { "date": "YYYY-MM-DD", "start": "HH:MM", "end": "HH:MM" },
                     ... ] }   // TODAS las franjas del bloque, en orden
      ] },
    { "idx": 2, ... }
  ],
  "locks": [ { "exam": "...", "classroom": "...",
               "date": "YYYY-MM-DD", "start": "HH:MM", "end": "HH:MM" } ]
}

Casuística que debe cubrir este JSON:
- 2-3 opciones para probar el selector de opción actual (current_option).
- 1 franja de cada assignment que NO exista en classrooms[].time_slots
  (ej. "2026-06-20" o una hora inventada) → la app debe OMITIR esa
  asignación y explicarlo.
- 1 assignment cuyo "exam" no exista en exams[] → se omite igualmente.
- 1 assignment que sí encaje pero supere capacity en su franja → la app
  lo CONSERVA con ⚠️ aviso y pregunta si importar de todos modos.
- "locks" con 1-2 entradas para restaurar bloqueos directamente
  (date+start+end deben coincidir con una franja de ese aula).

Si además quieres probar el caso "archivo sin bloqueos", genera una
SEGUNDA copia del mismo JSON sin la clave "locks": al importarla la app
debe preguntar "¿convertir las N asignaciones en bloqueos?".
```

---

## ✅ Checklist rápida (pégale esto a la IA si dudas de su salida)

```text
Antes de darme el JSON, verifica internamente:
- json.load lo parsea sin errores (sin comas finales, comillas dobles)
- 30-40 exams / 7-9 classrooms / 90-110 slots (o lo que te pedí)
- 5 exams con computers>0 en >= 3 studies
- 3 classrooms con computers>0 con ratios distintos
- >= 1 examen con computers < students
- >= 1 pareja de studies distintos que quepa por alumnos en un aula
  con PCs pero no por la suma de PCs
- >= 1 examen de 3.0 h con aula que tenga 3 franjas de 1 h encadenadas
- >= 2 franjas reserved: true
- capacity total por franja >= 1.5 x suma de students de los exámenes
  que podrían usar esa franja
- fechas 2026-06-15..2026-06-19, horas HH:MM, colores hex válidos
Responde SOLO con el JSON.
```

---

## 💡 Variantes útiles

- **Más difícil para el solver**: sube a 45-50 exámenes y reduce a 7 aulas,
  o pon varios exámenes del mismo estudio con `preferred_shift` opuesto.
- **Más realista (examen largo)**: `duration_hours: 3.0` en un ciclo y
  franjas encadenadas solo en un aula → el solver tiene que "encajar".
- **Modo estrés de PCs**: 8 exámenes con `computers` y solo 2 aulas con
  PCs → casi todo el mundo compite por los laboratorios.
- **Para probar reservas**: 3-4 franjas `reserved: true` en las horas
  punta para ver cómo el solver esquiva huecos.
- **Datos de un centro real**: sustituye nombres por los tuyos, pero
  conserva los rangos (15-35 alumnos, capacity 25-100) para que sea
  colocable.
