# -*- coding: utf-8 -*-
"""
SCHEDULER - Motor de optimizacion CP-SAT

Este modulo contiene el "cerebro" de la aplicacion.
Usa Google OR-Tools (CP-SAT) para asignar examenes a franjas y aulas.

RESTRICCIONES:
1. Cada examen -> una (franja + aula)
2. Mismo estudio NO puede coincidir en la misma franja
3. Alumnos en (franja, aula) <= capacidad del aula
4. Aula solo disponible en sus franjas

OBJETIVO: minimizar el numero de franjas usadas
"""

from ortools.sat.python import cp_model


class ExamScheduler:
    """
    Planificador de examenes usando CP-SAT.
    
    Variables de decision:
      x[examen, franja, aula] = 1 si examen e va a franja t en aula c
    
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
        # clave: (exam_idx, slot_idx, classroom_idx) -> BoolVar
        self.x = {}
        
        # Asignacion de la ultima solucion
        self.last_assignment = None
        
        # --- Pool global de franjas ---
        # Unifica franjas con misma (date, start, end) de todas las aulas
        self.global_slots = []            # [(date, start, end), ...]
        self.slot_key_to_idx = {}          # (date,start,end) -> indice
        self.classroom_global_slots = []   # por aula: set de indices validos
        
        for c in classrooms:
            valid = set()
            for ts in c.get("time_slots", []):
                key = (ts["date"], ts["start"], ts["end"])
                if key not in self.slot_key_to_idx:
                    self.slot_key_to_idx[key] = len(self.global_slots)
                    self.global_slots.append(key)
                valid.add(self.slot_key_to_idx[key])
            self.classroom_global_slots.append(valid)

    @property
    def num_slots(self):
        """Numero de franjas unicas en el pool global."""
        return len(self.global_slots)

    def build_model(self):
        """
        Construye el modelo matematico:
        1. Variables booleanas x[e][t][c]
        2. Restricciones (examen unico, mismo estudio, capacidad)
        3. Objetivo: minimizar franjas usadas
        
        Solo se crean variables para combinaciones (t, c) validas.
        """
        E = range(len(self.exams))
        T = range(self.num_slots)
        C = range(len(self.classrooms))

        # --- Pares validos (franja, aula) ---
        self._valid_pairs = []
        for t in T:
            for c in C:
                if t in self.classroom_global_slots[c]:
                    self._valid_pairs.append((t, c))

        # --- Variables de decision ---
        for e in E:
            for t, c in self._valid_pairs:
                self.x[(e, t, c)] = self.model.NewBoolVar(f"x_e{e}_t{t}_c{c}")

        # --- Restriccion 1: cada examen -> exactamente una (franja, aula) ---
        for e in E:
            candidates = [self.x[(e, t, c)] for t, c in self._valid_pairs]
            self.model.Add(sum(candidates) == 1)

        # --- Restriccion 2: mismo estudio -> franjas distintas ---
        studies = {e["study"] for e in self.exams}
        for study in studies:
            same_study = [i for i, e in enumerate(self.exams) if e["study"] == study]
            for t in T:
                vars_at_t = [
                    self.x[(e, t, c)] for e in same_study
                    for c in C if (t, c) in self._valid_pairs and (e, t, c) in self.x
                ]
                if vars_at_t:
                    self.model.Add(sum(vars_at_t) <= 1)

        # --- Restriccion 3: capacidad del aula ---
        for t, c in self._valid_pairs:
            self.model.Add(
                sum(
                    self.x[(e, t, c)] * self.exams[e]["students"]
                    for e in E if (e, t, c) in self.x
                )
                <= self.classrooms[c]["capacity"]
            )

        # --- Variables auxiliares: franja usada? ---
        slot_used = [self.model.NewBoolVar(f"slot_used_{t}") for t in T]
        for t in T:
            total = sum(self.x.get((e, t, c), 0) for e in E for c in C)
            self.model.Add(total >= 1).OnlyEnforceIf(slot_used[t])
            self.model.Add(total == 0).OnlyEnforceIf(slot_used[t].Not())

        # --- Objetivo: minimizar franjas usadas ---
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
            "slot":          indice de la franja global
            "slot_label":    texto legible (fecha hora)
            "classroom":     datos del aula
            "classroom_idx": indice del aula en self.classrooms
        }
        """
        if not hasattr(self, 'solver') or self.solver is None:
            return []
        
        self.last_assignment = []
        for e, exam in enumerate(self.exams):
            for t, c in self._valid_pairs:
                if self.x.get((e, t, c)) is not None and self.solver.Value(self.x[(e, t, c)]) == 1:
                    global_slot = self.global_slots[t]
                    self.last_assignment.append({
                        "exam": exam,
                        "exam_idx": e,
                        "slot": t,
                        "slot_label": f"{global_slot[0]} {global_slot[1]}-{global_slot[2]}",
                        "classroom": self.classrooms[c],
                        "classroom_idx": c,
                    })
                    break
        return self.last_assignment

    def get_slots_used(self):
        """Numero de franjas distintas usadas en la asignacion actual."""
        if self.last_assignment is None:
            return 0
        return len({a["slot"] for a in self.last_assignment})

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
            t = a["slot"]
            c = a["classroom_idx"]
            if (e, t, c) in self.x:
                matching_vars.append(self.x[(e, t, c)])
        
        if matching_vars:
            # Forzamos que al menos UNA de estas variables sea 0
            # Es decir: no todas pueden ser 1 simultaneamente
            # Esto equivale a: suma(vars) <= len(vars) - 1
            self.model.Add(sum(matching_vars) <= len(matching_vars) - 1)
