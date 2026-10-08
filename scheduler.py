# -*- coding: utf-8 -*-
# Copyright (C) 2026 Sergi Albuixech
# SPDX-License-Identifier: AGPL-3.0-or-later
"""
SCHEDULER - Motor de optimizacion CP-SAT

Este modulo contiene el "cerebro" de la aplicacion.
Usa Google OR-Tools (CP-SAT) para asignar examenes a franjas y aulas.

RESTRICCIONES:
1. Cada examen -> un BLOQUE de franjas encadenadas + aula
2. Mismo estudio NO puede solaparse en la misma franja
3. Mismo profesor NO puede solaparse en la misma franja
4. Suma de alumnos que ocupan (franja, aula) <= capacidad del aula
5. Suma de ordenadores que ocupan (franja, aula) <= ordenadores del aula
6. Aula solo disponible en sus franjas (las reservadas quedan excluidas)
7. Un examen solo ocupa bloques con duracion total >= su duration_hours
8. Franjas encadenables: mismo dia y fin de una == inicio de la siguiente
9. Objetivo: minimizar el numero de franjas usadas

SOPORTE ADICIONAL:
- Franjas marcadas como "reserved" en el aula no reciben ningun examen.
- Los bloqueos del usuario fijan examen -> (franja de inicio, aula).
"""

from ortools.sat.python import cp_model


# ──────────────────────────────────────────────────────────────────────────
# Helpers puros (reutilizados por la GUI: drag&drop, mover, validacion)
# ──────────────────────────────────────────────────────────────────────────

def _minutes(hhmm):
    """'09:30' -> 570"""
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def slot_minutes(global_slot):
    """Duracion en minutos de una franja global (date, start, end)."""
    _, start, end = global_slot
    return _minutes(end) - _minutes(start)


def build_global_pool(classrooms):
    """
    Construye el pool global de franjas (unifica (date, start, end) de
    todas las aulas).

    Devuelve:
        (global_slots, slot_key_to_idx, classroom_global_slots)
        global_slots:          [(date, start, end), ...]
        slot_key_to_idx:       {key: idx}
        classroom_global_slots: por aula, set de indices de franja validos
                                (excluye las franjas reservadas)
    """
    global_slots = []
    slot_key_to_idx = {}
    classroom_global_slots = []
    for c in classrooms:
        valid = set()
        for ts in c.get("time_slots", []):
            key = (ts["date"], ts["start"], ts["end"])
            if key not in slot_key_to_idx:
                slot_key_to_idx[key] = len(global_slots)
                global_slots.append(key)
            if not ts.get("reserved"):
                valid.add(slot_key_to_idx[key])
        classroom_global_slots.append(valid)
    return global_slots, slot_key_to_idx, classroom_global_slots


def exam_duration_minutes(exam):
    """Duracion requerida de un examen en minutos (minimo 1)."""
    try:
        dur = float(exam.get("duration_hours", 2.0) or 2.0)
    except (TypeError, ValueError):
        dur = 2.0
    return max(1, int(round(dur * 60)))


def classroom_chains(classroom, slot_key_to_idx):
    """
    Cadenas de franjas encadenables de un aula.

    Una cadena es una serie de franjas del mismo dia donde la fin de una
    coincide exactamente con el inicio de la siguiente (encadenado estricto).
    Las franjas reservadas no se incluyen y rompen la cadena.

    Devuelve: lista de cadenas, cada una una lista de indices de franja
    global ordenados cronologicamente.
    """
    entries = []
    for ts in classroom.get("time_slots", []):
        if ts.get("reserved"):
            continue
        key = (ts["date"], ts["start"], ts["end"])
        idx = slot_key_to_idx.get(key)
        if idx is None:
            continue
        entries.append((ts["date"], ts["start"], ts["end"], idx))
    entries.sort(key=lambda e: (e[0], e[1], e[2]))

    chains = []
    current = []
    prev_date = None
    prev_end = None
    for date, start, end, idx in entries:
        if current and date == prev_date and start == prev_end:
            current.append(idx)
        else:
            if current:
                chains.append(current)
            current = [idx]
        prev_date, prev_end = date, end
    if current:
        chains.append(current)
    return chains


def enumerate_blocks(exam, classroom, global_slots, slot_key_to_idx):
    """
    Enumera los bloques candidatos de UN examen en UN aula.

    Un bloque es la sub-cadena MAS CORTA que parte de una franja de
    inicio y cuya duracion total cubre la duracion del examen.
    Solo se genera el bloque minimal por posicion de inicio (ampliar
    nunca mejora la factibilidad).

    Devuelve lista de dicts: {"start": t, "slots": [...], "minutes": int}
    """
    need = int(exam.get("computers", 0) or 0)
    if need > int(classroom.get("computers", 0) or 0):
        # La suma de ordenadores de cualquier combinacion seria mayor
        return []

    dur = exam_duration_minutes(exam)
    blocks = []
    for chain in classroom_chains(classroom, slot_key_to_idx):
        mins = [slot_minutes(global_slots[t]) for t in chain]
        prefix = [0]
        for m in mins:
            prefix.append(prefix[-1] + m)
        for i in range(len(chain)):
            j = i
            while j < len(chain) and (prefix[j + 1] - prefix[i]) < dur:
                j += 1
            if j >= len(chain):
                # Desde esta posicion (y cualquier posterior) no se cubre
                break
            blocks.append({
                "start": chain[i],
                "slots": list(chain[i:j + 1]),
                "minutes": prefix[j + 1] - prefix[i],
            })
    return blocks


def block_for_start(exam, classroom, start_slot, global_slots, slot_key_to_idx):
    """
    Devuelve las franjas del bloque que empieza en `start_slot` para ese
    examen en ese aula, o None si no es posible (duración no cabe o
    franja reservada). Usado por la GUI (drag & drop, mover examen).
    """
    for blk in enumerate_blocks(exam, classroom, global_slots, slot_key_to_idx):
        if blk["start"] == start_slot:
            return blk["slots"]
    return None


class ExamScheduler:
    """
    Planificador de examenes usando CP-SAT.

    Variables de decision:
      x[examen, bloque] = 1 si el examen ocupa ese bloque de franjas

    Tambien soporta generar MULTIPLES soluciones alternativas para
    que el usuario pueda elegir la que mas le guste.
    """

    def __init__(self, exams, classrooms):
        """
        Constructor: guarda datos y construye el pool global de franjas.

        El pool global unifica franjas con misma (fecha, inicio, fin)
        de todas las aulas. Esto permite que examenes en distintas
        aulas puedan estar en la misma franja horaria.
        """
        self.exams = exams
        self.classrooms = classrooms

        # Modelo CP-SAT (se construye en build_model)
        self.model = cp_model.CpModel()

        # Diccionario de variables de decision
        # clave: (exam_idx, block_idx) -> BoolVar
        self.x = {}

        # Bloques candidatos (se rellenan en build_model)
        self.blocks = []            # [{"classroom", "start", "slots", "minutes"}, ...]
        self.exam_blocks = []       # por examen: [block_idx, ...]

        # Asignacion de la ultima solucion
        self.last_assignment = None

        # --- Pool global de franjas ---
        (self.global_slots,
         self.slot_key_to_idx,
         self.classroom_global_slots) = build_global_pool(classrooms)

        # Duracion de cada franja global en minutos
        self.slot_minutes = [slot_minutes(s) for s in self.global_slots]

    @property
    def num_slots(self):
        """Numero de franjas unicas en el pool global."""
        return len(self.global_slots)

    # ── Modelo ─────────────────────────────────────────────────────────

    def _build_blocks(self):
        """Enumera los bloques candidatos de cada examen en cada aula."""
        self.blocks = []
        self.exam_blocks = []
        for e, exam in enumerate(self.exams):
            mine = []
            for c, classroom in enumerate(self.classrooms):
                for blk in enumerate_blocks(
                    exam, classroom, self.global_slots, self.slot_key_to_idx
                ):
                    blk["classroom"] = c
                    blk["slot_set"] = frozenset(blk["slots"])
                    mine.append(len(self.blocks))
                    self.blocks.append(blk)
            self.exam_blocks.append(mine)

    def _active_vars(self, e, t):
        """Variables x del examen e cuyo bloque cubre la franja global t."""
        return [
            self.x[(e, b)]
            for b in self.exam_blocks[e]
            if t in self.blocks[b]["slot_set"]
        ]

    def build_model(self):
        """
        Construye el modelo matematico:
        1. Variables booleanas x[e][bloque]
        2. Restricciones (examen unico, mismo estudio/profesor,
           capacidad, ordenadores, duracion)
        3. Objetivo: minimizar franjas usadas

        Solo se crean variables para bloques validos.
        """
        self._build_blocks()

        E = range(len(self.exams))
        T = range(self.num_slots)
        C = range(len(self.classrooms))

        # --- Variables de decision ---
        for e in E:
            for b in self.exam_blocks[e]:
                self.x[(e, b)] = self.model.NewBoolVar(f"x_e{e}_b{b}")

        # --- Restriccion 1: cada examen -> exactamente un bloque ---
        for e in E:
            candidates = [self.x[(e, b)] for b in self.exam_blocks[e]]
            if not candidates:
                # No hay ninguna (franja, aula) que admita este examen:
                # modelo deliberadamente infactible (la validacion de la
                # GUI avisa antes de llegar aqui).
                dummy = self.model.NewBoolVar(f"no_block_e{e}")
                self.model.Add(dummy == 1)
                self.model.Add(dummy == 0)
                continue
            self.model.Add(sum(candidates) == 1)

        # --- Restriccion 2: mismo estudio -> sin solapes ---
        studies = {e["study"] for e in self.exams}
        for study in studies:
            same_study = [i for i, e in enumerate(self.exams) if e["study"] == study]
            for t in T:
                vars_at_t = [
                    v for e in same_study for v in self._active_vars(e, t)
                ]
                if len(vars_at_t) > 1:
                    self.model.Add(sum(vars_at_t) <= 1)

        # --- Restriccion: mismo profesor -> sin solapes ---
        teachers = {e.get("teacher", "") for e in self.exams if e.get("teacher")}
        for teacher in teachers:
            same_teacher = [
                i for i, e in enumerate(self.exams)
                if e.get("teacher", "") == teacher
            ]
            for t in T:
                vars_at_t = [
                    v for e in same_teacher for v in self._active_vars(e, t)
                ]
                if len(vars_at_t) > 1:
                    self.model.Add(sum(vars_at_t) <= 1)

        # --- Restriccion 3: capacidad del aula (por franja) ---
        for t in T:
            for c in C:
                terms = []
                for e in E:
                    vs = [
                        self.x[(e, b)]
                        for b in self.exam_blocks[e]
                        if self.blocks[b]["classroom"] == c
                        and t in self.blocks[b]["slot_set"]
                    ]
                    if vs:
                        terms.append(self.exams[e]["students"] * sum(vs))
                if terms:
                    self.model.Add(
                        sum(terms) <= self.classrooms[c]["capacity"]
                    )

        # --- Restriccion: ordenadores del aula (por franja) ---
        for t in T:
            for c in C:
                terms = []
                for e in E:
                    need = int(self.exams[e].get("computers", 0) or 0)
                    if not need:
                        continue
                    vs = [
                        self.x[(e, b)]
                        for b in self.exam_blocks[e]
                        if self.blocks[b]["classroom"] == c
                        and t in self.blocks[b]["slot_set"]
                    ]
                    if vs:
                        terms.append(need * sum(vs))
                if terms:
                    available = int(self.classrooms[c].get("computers", 0) or 0)
                    self.model.Add(sum(terms) <= available)

        # --- Variables auxiliares: franja usada? ---
        slot_used = [self.model.NewBoolVar(f"slot_used_{t}") for t in T]
        for t in T:
            total = sum(
                v for e in E for v in self._active_vars(e, t)
            )
            self.model.Add(total >= 1).OnlyEnforceIf(slot_used[t])
            self.model.Add(total == 0).OnlyEnforceIf(slot_used[t].Not())

        # --- Preferencia de turno (manana/tarde) sobre la franja de inicio ---
        preference_violations = []
        for e_idx, exam in enumerate(self.exams):
            pref = exam.get("preferred_shift", "")
            if pref not in ("morning", "afternoon"):
                continue
            for b in self.exam_blocks[e_idx]:
                start_hour = int(
                    self.global_slots[self.blocks[b]["start"]][1].split(":")[0]
                )
                is_morning = start_hour < 14
                is_match = (
                    (pref == "morning" and is_morning)
                    or (pref == "afternoon" and not is_morning)
                )
                if not is_match:
                    preference_violations.append(self.x[(e_idx, b)])

        # --- Objetivo: minimizar franjas usadas + violaciones de preferencia ---
        if preference_violations:
            self.model.Minimize(
                sum(slot_used) + sum(preference_violations) * 100
            )
        else:
            self.model.Minimize(sum(slot_used))

        # Guardamos referencia a slot_used para usarlo despues
        self._slot_used = slot_used

    def solve(self, time_limit=15):
        """
        Resuelve el modelo con un limite de tiempo.

        Devuelve el estado: OPTIMAL, FEASIBLE, INFEASIBLE, etc.
        """
        self.solver = cp_model.CpSolver()
        self.solver.parameters.max_time_in_seconds = time_limit
        self.solver.parameters.num_search_workers = 4
        return self.solver.Solve(self.model)

    def extract_assignment(self):
        """
        Extrae la asignacion de la solucion actual del solver.

        Devuelve lista de diccionarios:
        {
            "exam":          datos del examen
            "exam_idx":      indice del examen en self.exams
            "block":         indice del bloque ocupado
            "slot":          franja global de INICIO (compatibilidad)
            "slots":         todas las franjas globales ocupadas
            "slot_end":      ultima franja global ocupada
            "slot_label":    texto legible (fecha inicio-fin)
            "classroom":     datos del aula
            "classroom_idx": indice del aula en self.classrooms
        }
        """
        if not hasattr(self, 'solver') or self.solver is None:
            return []

        self.last_assignment = []
        for e, exam in enumerate(self.exams):
            for b in self.exam_blocks[e]:
                var = self.x.get((e, b))
                if var is not None and self.solver.Value(var) == 1:
                    blk = self.blocks[b]
                    first = self.global_slots[blk["slots"][0]]
                    last = self.global_slots[blk["slots"][-1]]
                    self.last_assignment.append({
                        "exam": exam,
                        "exam_idx": e,
                        "block": b,
                        "slot": blk["start"],
                        "slots": list(blk["slots"]),
                        "slot_end": blk["slots"][-1],
                        "slot_label": f"{first[0]} {first[1]}-{last[2]}",
                        "classroom": self.classrooms[blk["classroom"]],
                        "classroom_idx": blk["classroom"],
                    })
                    break
        return self.last_assignment

    def get_slots_used(self):
        """Numero de franjas distintas ocupadas en la asignacion actual."""
        if self.last_assignment is None:
            return 0
        used = set()
        for a in self.last_assignment:
            used.update(a.get("slots", [a["slot"]]))
        return len(used)

    def generate_multiple_solutions(self, num_options=3, time_limit=15):
        """
        Genera MULTIPLES soluciones alternativas para que el usuario elija.

        Funcionamiento:
        1. Resuelve el modelo y extrae la solucion
        2. Anade una restriccion que BLOQUEA la solucion encontrada
        3. Resuelve de nuevo (encuentra una solucion diferente)
        4. Repite hasta tener num_options soluciones o hasta que no
           haya mas soluciones posibles

        La restriccion de bloqueo dice: "al menos un examen debe
        asignarse de forma distinta a como estaba en la solucion anterior".
        Esto fuerza al solver a buscar una configuracion diferente.

        Parametros:
            num_options: numero maximo de opciones a generar (default: 3)
            time_limit:  segundos maximo para CADA solucion (default: 15)

        Devuelve:
            Lista de tuplas (indice, slots_usados, asignacion)
            Cada asignacion es una lista de diccionarios.
        """
        solutions = []  # Lista de (indice, slots_usados, asignacion)

        for i in range(num_options):
            # Creamos un solver nuevo para cada iteracion
            # (CP-SAT permite modificar el modelo entre solves)
            solver = cp_model.CpSolver()
            solver.parameters.max_time_in_seconds = time_limit
            solver.parameters.num_search_workers = 4
            # Semilla aleatoria diferente para cada opcion
            # Esto ayuda a que el solver explore distintas ramas
            solver.parameters.random_seed = (i + 1) * 100
            # Logging del solver (lo desactivamos para no saturar)
            solver.parameters.log_search_progress = False

            status = solver.Solve(self.model)

            if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
                # Extraemos la asignacion de este solver
                self.solver = solver  # Temporal para extract_assignment
                assignment = self.extract_assignment()
                slots_used = self.get_slots_used()

                # Guardamos la solucion
                solutions.append((i + 1, slots_used, assignment))

                # Anadimos restriccion de bloqueo para la siguiente iteracion
                # Si es la ultima iteracion, no hace falta
                if i < num_options - 1:
                    self._add_blocking_constraint(assignment)
            else:
                # No hay mas soluciones posibles, salimos
                break

        return solutions

    def add_locked_assignments(self, locks):
        """
        Fija asignaciones de examenes especificos a (franja de inicio, aula).

        locks: dict {exam_idx: (slot_idx_inicio, classroom_idx)}
        Estos examenes se asignaran forzosamente a esos bloques.

        Lanza ValueError si el bloque no existe (la duracion del examen
        no cabe empezando ahi, el aula no tiene ordenadores suficientes
        o la franja esta reservada).
        """
        for exam_idx, (slot_idx, classroom_idx) in locks.items():
            found = None
            for b in self.exam_blocks[exam_idx]:
                blk = self.blocks[b]
                if blk["start"] == slot_idx and blk["classroom"] == classroom_idx:
                    found = b
                    break
            if found is None:
                name = self.exams[exam_idx].get("name", f"#{exam_idx}")
                raise ValueError(
                    f"No se puede bloquear «{name}»: no cabe empezando en esa "
                    f"franja de ese aula (duración, ordenadores o franja reservada)"
                )
            self.model.Add(self.x[(exam_idx, found)] == 1)

    def _add_blocking_constraint(self, assignment):
        """
        Anade una restriccion al modelo para que la SIGUIENTE solucion
        sea DIFERENTE de la que acabamos de encontrar.

        La restriccion dice: la suma de las variables que coinciden
        con la asignacion actual debe ser <= (numero_de_examenes - 1).
        Es decir, al menos un examen debe cambiar de (franja, aula).

        Esto se conoce como "no-good cut" o "blocking constraint".
        """
        # Recogemos las variables de decision que estan a 1 en esta
        # asignacion (es decir, las que representan esta solucion)
        matching_vars = []
        for a in assignment:
            e = a["exam_idx"]
            b = a.get("block")
            if b is None:
                # Compatibilidad con asignaciones antiguas
                for cand in self.exam_blocks[e]:
                    blk = self.blocks[cand]
                    if (blk["start"] == a["slot"]
                            and blk["classroom"] == a["classroom_idx"]):
                        b = cand
                        break
            if b is not None and (e, b) in self.x:
                matching_vars.append(self.x[(e, b)])

        if matching_vars:
            # Forzamos que al menos UNA de estas variables sea 0
            # Es decir: no todas pueden ser 1 simultaneamente
            # Esto equivale a: suma(vars) <= len(vars) - 1
            self.model.Add(sum(matching_vars) <= len(matching_vars) - 1)
