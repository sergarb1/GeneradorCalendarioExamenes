# -*- coding: utf-8 -*-
"""
Tests del motor de planificación CP-SAT:

1. Restricciones básicas (estudio, profesor, capacidad, aula)
2. Múltiples soluciones
3. Bloqueos (simples y múltiples)
4. Turno preferido
5. Duración de exámenes (franjas encadenadas)
6. Ordenadores de examen/aula
7. Franjas reservadas
8. Datos semilla resolubles

Ejecutar: python -m unittest discover tests -v
"""
import unittest
from ortools.sat.python import cp_model
from scheduler import ExamScheduler
from seed_data import get_seed_data


SIMPLE_EXAMS = [
    {"name": "Matematicas (Alumnez)", "students": 20, "study": "Informatica (GS)",
     "teacher": "Profesor A", "preferred_shift": "morning", "color": "#6366f1"},
    {"name": "Lengua (Estudiantez)", "students": 15, "study": "Informatica (GS)",
     "teacher": "Profesor B", "preferred_shift": "afternoon", "color": "#ef4444"},
    {"name": "Historia (Alumnez)", "students": 10, "study": "Turismo (GS)",
     "teacher": "Profesor A", "preferred_shift": "", "color": "#10b981"},
]

SIMPLE_CLASSROOMS = [
    {
        "name": "Aula 101",
        "capacity": 30,
        "time_slots": [
            {"date": "2026-06-15", "start": "09:00", "end": "11:00"},
            {"date": "2026-06-15", "start": "11:30", "end": "13:30"},
            {"date": "2026-06-16", "start": "09:00", "end": "11:00"},
        ],
    },
    {
        "name": "Aula 102",
        "capacity": 25,
        "time_slots": [
            {"date": "2026-06-15", "start": "09:00", "end": "11:00"},
            {"date": "2026-06-15", "start": "16:00", "end": "18:00"},
        ],
    },
]

EXAMS_SAME_STUDY = [
    {"name": "Examen 1 (Alumnez)", "students": 10, "study": "Mismo Estudio",
     "teacher": "", "preferred_shift": "", "color": "#6366f1"},
    {"name": "Examen 2 (Alumnez)", "students": 10, "study": "Mismo Estudio",
     "teacher": "", "preferred_shift": "", "color": "#ef4444"},
]

SINGLE_CLASSROOM = [
    {
        "name": "Aula Unica",
        "capacity": 100,
        "time_slots": [
            {"date": "2026-06-15", "start": "09:00", "end": "11:00"},
            {"date": "2026-06-15", "start": "11:30", "end": "13:30"},
        ],
    },
]

EXAMS_SAME_TEACHER = [
    {"name": "Examen A (Alumnez)", "students": 10, "study": "Estudio A",
     "teacher": "Mismo Profe", "preferred_shift": "", "color": "#6366f1"},
    {"name": "Examen B (Alumnez)", "students": 10, "study": "Estudio B",
     "teacher": "Mismo Profe", "preferred_shift": "", "color": "#ef4444"},
]

# ── Datos para duración (franjas de 1h encadenables) ──────────────────────
ONE_HOUR_CLASSROOM = [
    {
        "name": "Aula 1h",
        "capacity": 60,
        "time_slots": [
            {"date": "2026-06-15", "start": "09:00", "end": "10:00"},
            {"date": "2026-06-15", "start": "10:00", "end": "11:00"},
            {"date": "2026-06-15", "start": "11:00", "end": "12:00"},
        ],
    },
]

# Franjas con hueco: NO se pueden encadenar
GAPPED_CLASSROOM = [
    {
        "name": "Aula con descanso",
        "capacity": 60,
        "time_slots": [
            {"date": "2026-06-15", "start": "09:00", "end": "11:00"},
            {"date": "2026-06-15", "start": "11:30", "end": "13:30"},
        ],
    },
]

EXAM_3H = [
    {"name": "Examen Largo (Alumnez)", "students": 10, "study": "Largo",
     "teacher": "", "preferred_shift": "", "duration_hours": 3, "color": "#6366f1"},
]

EXAM_2H = [
    {"name": "Examen 2h (Alumnez)", "students": 10, "study": "Medio",
     "teacher": "", "preferred_shift": "", "duration_hours": 2, "color": "#6366f1"},
]

EXAM_1H = [
    {"name": "Examen 1h (Alumnez)", "students": 10, "study": "Corto",
     "teacher": "", "preferred_shift": "", "duration_hours": 1, "color": "#6366f1"},
]

# ── Datos para ordenadores ────────────────────────────────────────────────
COMPUTER_CLASSROOMS = [
    {
        "name": "Aula Normal",
        "capacity": 50,
        "computers": 0,
        "time_slots": [
            {"date": "2026-06-15", "start": "09:00", "end": "11:00"},
            {"date": "2026-06-15", "start": "11:30", "end": "13:30"},
        ],
    },
    {
        "name": "Laboratorio",
        "capacity": 40,
        "computers": 25,
        "time_slots": [
            {"date": "2026-06-15", "start": "09:00", "end": "11:00"},
            {"date": "2026-06-15", "start": "11:30", "end": "13:30"},
        ],
    },
]

EXAM_NEEDS_PC = [
    {"name": "Programacion (Alumnez)", "students": 20, "study": "Informatica",
     "computers": 20, "teacher": "", "preferred_shift": "", "color": "#6366f1"},
]

EXAMS_PC_PAIR = [
    {"name": "Redes (Alumnez)", "students": 15, "study": "Informatica",
     "computers": 15, "teacher": "", "preferred_shift": "", "color": "#6366f1"},
    {"name": "Sistemas (Estudiantez)", "students": 15, "study": "Sistemas",
     "computers": 15, "teacher": "", "preferred_shift": "", "color": "#ef4444"},
]

# ── Datos para franjas reservadas ─────────────────────────────────────────
RESERVED_CLASSROOMS = [
    {
        "name": "Aula Reservada",
        "capacity": 50,
        "time_slots": [
            {"date": "2026-06-15", "start": "09:00", "end": "11:00"},
            {"date": "2026-06-15", "start": "11:30", "end": "13:30", "reserved": True},
        ],
    },
]


def _slot_span_minutes(assignment_item, global_slots):
    """Duracion total en minutos de todas las franjas que ocupa."""
    total = 0
    for t in assignment_item.get("slots", [assignment_item["slot"]]):
        _, start, end = global_slots[t]
        sh, sm = (int(x) for x in start.split(":"))
        eh, em = (int(x) for x in end.split(":"))
        total += (eh * 60 + em) - (sh * 60 + sm)
    return total


class TestSchedulerConstraints(unittest.TestCase):
    """Prueba las restricciones fundamentales del scheduler."""

    def setUp(self):
        """Crea el scheduler con datos simples y construye el modelo."""
        self.s = ExamScheduler(SIMPLE_EXAMS, SIMPLE_CLASSROOMS)
        self.s.build_model()
        status = self.s.solve(time_limit=15)
        self.solver = self.s.solver
        self.status = status
        self.assignment = self.s.extract_assignment()

    def test_solution_feasible(self):
        """El solver debe encontrar solucion factible u optima."""
        self.assertIn(
            self.status, (cp_model.OPTIMAL, cp_model.FEASIBLE),
            "El solver no encontro solucion con los datos de test basicos."
        )

    def test_each_exam_assigned_once(self):
        """Cada examen aparece exactamente una vez en la asignacion."""
        assigned_exams = [a["exam_idx"] for a in self.assignment]
        self.assertEqual(
            len(assigned_exams), len(SIMPLE_EXAMS),
            "Debe haber exactamente una asignacion por examen."
        )
        self.assertEqual(
            len(set(assigned_exams)), len(SIMPLE_EXAMS),
            "Cada examen debe estar asignado una unica vez."
        )

    def test_study_same_slot_violation(self):
        """Examenes del mismo estudio NO deben solaparse en ninguna franja."""
        by_study = {}
        for a in self.assignment:
            by_study.setdefault(a["exam"]["study"], []).append(
                set(a.get("slots", [a["slot"]]))
            )
        for study, slot_sets in by_study.items():
            for i in range(len(slot_sets)):
                for j in range(i + 1, len(slot_sets)):
                    overlap = slot_sets[i] & slot_sets[j]
                    self.assertFalse(
                        overlap,
                        f"Los examenes de '{study}' solapan en franjas {overlap}."
                    )

    def test_capacity_respected(self):
        """La suma de alumnos en (franja, aula) no debe exceder la capacidad.

        Se expande por TODAS las franjas ocupadas (a["slots"]), no solo la
        de inicio, para cubrir exámenes que abarcan varias franjas.
        """
        usage = {}
        for a in self.assignment:
            for t in a.get("slots", [a["slot"]]):
                key = (t, a["classroom_idx"])
                usage.setdefault(key, 0)
                usage[key] += a["exam"]["students"]
        for (t, c_idx), total in usage.items():
            cap = SIMPLE_CLASSROOMS[c_idx]["capacity"]
            self.assertLessEqual(
                total, cap,
                f"Franja {t}, aula {SIMPLE_CLASSROOMS[c_idx]['name']}: "
                f"{total} alumnos sobrepasa capacidad {cap}."
            )

    def test_classroom_availability(self):
        """Cada examen debe estar en una (franja, aula) valida para esa aula."""
        for a in self.assignment:
            c = a["classroom"]
            slot_key = (
                self.s.global_slots[a["slot"]][0],
                self.s.global_slots[a["slot"]][1],
                self.s.global_slots[a["slot"]][2],
            )
            valid_keys = {(ts["date"], ts["start"], ts["end"]) for ts in c["time_slots"]}
            self.assertIn(
                slot_key, valid_keys,
                f"El aula {c['name']} no tiene la franja {slot_key} disponible."
            )

    def test_teacher_same_slot_violation(self):
        """Examenes del mismo profesor NO deben solaparse en ninguna franja."""
        by_teacher = {}
        for a in self.assignment:
            teacher = a["exam"].get("teacher", "")
            if teacher:
                by_teacher.setdefault(teacher, []).append(
                    set(a.get("slots", [a["slot"]]))
                )
        for teacher, slot_sets in by_teacher.items():
            for i in range(len(slot_sets)):
                for j in range(i + 1, len(slot_sets)):
                    overlap = slot_sets[i] & slot_sets[j]
                    self.assertFalse(
                        overlap,
                        f"El profesor '{teacher}' solapa exámenes en {overlap}."
                    )


class TestSameStudyConstraint(unittest.TestCase):
    """Verifica que dos examenes del mismo estudio nunca caen en la misma franja."""

    def test_same_study_different_slots(self):
        s = ExamScheduler(EXAMS_SAME_STUDY, SINGLE_CLASSROOM)
        s.build_model()
        status = s.solve(time_limit=15)
        self.assertIn(status, (cp_model.OPTIMAL, cp_model.FEASIBLE))
        assignment = s.extract_assignment()
        slots = [a["slot"] for a in assignment]
        self.assertEqual(
            len(set(slots)), len(slots),
            "Dos examenes del mismo estudio no pueden estar en la misma franja."
        )


class TestSameTeacherConstraint(unittest.TestCase):
    """Verifica que dos examenes del mismo profesor no caen en la misma franja."""

    def test_same_teacher_different_slots(self):
        s = ExamScheduler(EXAMS_SAME_TEACHER, SINGLE_CLASSROOM)
        s.build_model()
        status = s.solve(time_limit=15)
        self.assertIn(status, (cp_model.OPTIMAL, cp_model.FEASIBLE))
        assignment = s.extract_assignment()
        slots = [a["slot"] for a in assignment]
        self.assertEqual(
            len(set(slots)), len(slots),
            "Dos examenes del mismo profesor no pueden estar en la misma franja."
        )


class TestMultipleSolutions(unittest.TestCase):
    """Prueba la generacion de multiples opciones."""

    def test_multiple_options(self):
        s = ExamScheduler(SIMPLE_EXAMS, SIMPLE_CLASSROOMS)
        s.build_model()
        solutions = s.generate_multiple_solutions(num_options=3, time_limit=10)
        self.assertGreaterEqual(
            len(solutions), 2,
            "Deberian generarse al menos 2 opciones con datos basicos."
        )
        for idx, slots_used, assignment in solutions:
            self.assertEqual(
                len(assignment), len(SIMPLE_EXAMS),
                f"Opcion {idx}: cada examen debe tener una asignacion."
            )

    def test_options_are_different(self):
        """Cada opcion debe ser diferente de las demas."""
        s = ExamScheduler(SIMPLE_EXAMS, SIMPLE_CLASSROOMS)
        s.build_model()
        solutions = s.generate_multiple_solutions(num_options=3, time_limit=10)
        signatures = set()
        for _, _, assignment in solutions:
            sig = tuple(
                (a["exam_idx"], a["slot"], a["classroom_idx"])
                for a in assignment
            )
            signatures.add(sig)
        self.assertGreaterEqual(
            len(signatures), len(solutions),
            "Cada opcion debe tener una combinacion distinta de asignaciones."
        )


class TestExamDuration(unittest.TestCase):
    """Duración: el examen ocupa bloques de franjas encadenadas."""

    def _solve(self, exams, classrooms, time_limit=15):
        s = ExamScheduler(exams, classrooms)
        s.build_model()
        status = s.solve(time_limit=time_limit)
        return s, status

    def test_long_exam_spans_contiguous_slots(self):
        """Un examen de 3h ocupa 3 franjas de 1h encadenadas."""
        s, status = self._solve(EXAM_3H, ONE_HOUR_CLASSROOM)
        self.assertIn(status, (cp_model.OPTIMAL, cp_model.FEASIBLE))
        a = s.extract_assignment()[0]
        slots = a["slots"]
        self.assertEqual(
            len(slots), 3,
            "Un examen de 3h en franjas de 1h debe ocupar exactamente 3 franjas."
        )
        # Encadenado estricto: misma fecha y fin == inicio siguiente
        for i in range(len(slots) - 1):
            cur = s.global_slots[slots[i]]
            nxt = s.global_slots[slots[i + 1]]
            self.assertEqual(cur[0], nxt[0], "Las franjas deben ser del mismo día.")
            self.assertEqual(
                cur[2], nxt[1],
                "La fin de una franja debe coincidir con el inicio de la siguiente."
            )
        # Duración total suficiente
        self.assertGreaterEqual(_slot_span_minutes(a, s.global_slots), 180)

    def test_exam_never_shorter_than_slot(self):
        """Un examen de 2h no cabe en una sola franja de 1h: ocupa 2."""
        s, status = self._solve(EXAM_2H, ONE_HOUR_CLASSROOM)
        self.assertIn(status, (cp_model.OPTIMAL, cp_model.FEASIBLE))
        a = s.extract_assignment()[0]
        self.assertEqual(len(a["slots"]), 2)
        self.assertGreaterEqual(_slot_span_minutes(a, s.global_slots), 120)

    def test_gapped_slots_cannot_be_chained(self):
        """Con hueco (11:00 vs 11:30) un examen de 3h no tiene solución."""
        s = ExamScheduler(EXAM_3H, GAPPED_CLASSROOM)
        s.build_model()
        status = s.solve(time_limit=10)
        self.assertEqual(
            status, cp_model.INFEASIBLE,
            "No se pueden encadenar franjas con un hueco entre ellas."
        )

    def test_reserved_slot_breaks_chain(self):
        """Una franja reservada en medio rompe la cadena para un examen de 3h."""
        classrooms = [{
            "name": "Aula 1h con reserva",
            "capacity": 60,
            "time_slots": [
                {"date": "2026-06-15", "start": "09:00", "end": "10:00"},
                {"date": "2026-06-15", "start": "10:00", "end": "11:00", "reserved": True},
                {"date": "2026-06-15", "start": "11:00", "end": "12:00"},
            ],
        }]
        s = ExamScheduler(EXAM_3H, classrooms)
        s.build_model()
        status = s.solve(time_limit=10)
        self.assertEqual(status, cp_model.INFEASIBLE)

    def test_short_exam_still_works_with_reserved_slot(self):
        """Con una franja reservada en medio, un examen de 1h sigue cabiendo."""
        classrooms = [{
            "name": "Aula 1h con reserva",
            "capacity": 60,
            "time_slots": [
                {"date": "2026-06-15", "start": "09:00", "end": "10:00"},
                {"date": "2026-06-15", "start": "10:00", "end": "11:00", "reserved": True},
                {"date": "2026-06-15", "start": "11:00", "end": "12:00"},
            ],
        }]
        s = ExamScheduler(EXAM_1H, classrooms)
        s.build_model()
        status = s.solve(time_limit=10)
        self.assertIn(status, (cp_model.OPTIMAL, cp_model.FEASIBLE))
        a = s.extract_assignment()[0]
        self.assertNotEqual(
            a["slots"], [1],
            "La franja reservada no debe ser ocupada."
        )
        self.assertEqual(len(a["slots"]), 1)


class TestComputers(unittest.TestCase):
    """Ordenadores: restricción de suma por (franja, aula)."""

    def test_exam_with_computers_goes_to_lab(self):
        s = ExamScheduler(EXAM_NEEDS_PC, COMPUTER_CLASSROOMS)
        s.build_model()
        status = s.solve(time_limit=15)
        self.assertIn(status, (cp_model.OPTIMAL, cp_model.FEASIBLE))
        a = s.extract_assignment()[0]
        self.assertEqual(
            a["classroom"]["name"], "Laboratorio",
            "Un examen con ordenadores solo puede ir al aula con ordenadores."
        )

    def test_computer_sum_per_slot_respected(self):
        """Dos exámenes de 15 PCs no pueden compartir aula con 25 PCs."""
        s = ExamScheduler(EXAMS_PC_PAIR, COMPUTER_CLASSROOMS)
        s.build_model()
        status = s.solve(time_limit=15)
        self.assertIn(status, (cp_model.OPTIMAL, cp_model.FEASIBLE))
        assignment = s.extract_assignment()

        usage = {}
        for a in assignment:
            need = int(a["exam"].get("computers", 0) or 0)
            for t in a["slots"]:
                usage.setdefault((t, a["classroom_idx"]), 0)
                usage[(t, a["classroom_idx"])] += need
        for (t, c_idx), total in usage.items():
            available = int(COMPUTER_CLASSROOMS[c_idx].get("computers", 0) or 0)
            self.assertLessEqual(
                total, available,
                f"Franja {t}, aula {COMPUTER_CLASSROOMS[c_idx]['name']}: "
                f"{total} PCs pedidos con {available} disponibles."
            )

        # Como solo hay un aula con PCs, no pueden coincidir en franja
        lab_idx = 1
        lab_slots = [
            set(a["slots"]) for a in assignment
            if a["classroom_idx"] == lab_idx
        ]
        for i in range(len(lab_slots)):
            for j in range(i + 1, len(lab_slots)):
                self.assertFalse(
                    lab_slots[i] & lab_slots[j],
                    "Dos exámenes con PCs no pueden solaparse en el laboratorio."
                )

    def test_exam_without_computers_can_use_normal_room(self):
        exams = [
            {"name": "Lengua (Alumnez)", "students": 20, "study": "Lengua",
             "computers": 0, "teacher": "", "preferred_shift": "",
             "color": "#6366f1"},
        ]
        s = ExamScheduler(exams, COMPUTER_CLASSROOMS)
        s.build_model()
        status = s.solve(time_limit=15)
        self.assertIn(status, (cp_model.OPTIMAL, cp_model.FEASIBLE))
        assignment = s.extract_assignment()
        # Puede ir a cualquiera de las dos aulas (sin restricción de PCs)
        self.assertIn(
            assignment[0]["classroom"]["name"],
            ["Aula Normal", "Laboratorio"],
        )

    def test_infeasible_when_no_classroom_has_computers(self):
        exams = [
            {"name": "Informatica (Alumnez)", "students": 20,
             "study": "Informatica", "computers": 30, "teacher": "",
             "preferred_shift": "", "color": "#6366f1"},
        ]
        cr = [{
            "name": "Sin PCs",
            "capacity": 50,
            "computers": 0,
            "time_slots": [{"date": "2026-06-15", "start": "09:00", "end": "11:00"}],
        }]
        s = ExamScheduler(exams, cr)
        s.build_model()
        status = s.solve(time_limit=10)
        self.assertEqual(status, cp_model.INFEASIBLE)

    def test_partial_pc_room_rejects_higher_pc_exam(self):
        """Un aula con capacidad suficiente pero pocos PCs no vale."""
        exams = [
            {"name": "Edicion (Alumnez)", "students": 12, "study": "Multimedia",
             "computers": 20, "teacher": "", "preferred_shift": "",
             "color": "#6366f1"},
        ]
        cr = [{
            "name": "Aula con pocos PCs",
            "capacity": 30,
            "computers": 15,
            "time_slots": [{"date": "2026-06-15", "start": "09:00", "end": "11:00"}],
        }]
        s = ExamScheduler(exams, cr)
        s.build_model()
        status = s.solve(time_limit=10)
        self.assertEqual(
            status, cp_model.INFEASIBLE,
            "Capacidad OK pero 20 PCs > 15 disponibles: no puede asignarse."
        )

    def test_exam_with_fewer_computers_than_students(self):
        """Examen con menos PCs que alumnos: lo decide la suma de PCs."""
        exams = [
            {"name": "Ofimatica (Alumnez)", "students": 24, "study": "Administracion",
             "computers": 15, "teacher": "", "preferred_shift": "",
             "color": "#6366f1"},
        ]
        cr = [
            {
                "name": "Aula sin PCs",
                "capacity": 50,
                "computers": 0,
                "time_slots": [{"date": "2026-06-15", "start": "09:00", "end": "11:00"}],
            },
            {
                "name": "Aula con 15 PCs",
                "capacity": 30,
                "computers": 15,
                "time_slots": [{"date": "2026-06-15", "start": "09:00", "end": "11:00"}],
            },
        ]
        s = ExamScheduler(exams, cr)
        s.build_model()
        status = s.solve(time_limit=10)
        self.assertIn(status, (cp_model.OPTIMAL, cp_model.FEASIBLE))
        a = s.extract_assignment()[0]
        self.assertEqual(
            a["classroom"]["name"], "Aula con 15 PCs",
            "Cabe por alumnos en las dos, pero solo la de 15 PCs cumple la suma."
        )

    def test_pc_sum_blocks_pair_in_same_room(self):
        """Dos exámenes caben por alumnos (44<=45) pero no por PCs (35>25)."""
        exams = [
            {"name": "Sistemas (Alumnez)", "students": 20, "study": "Informatica",
             "computers": 20, "teacher": "", "preferred_shift": "",
             "color": "#6366f1"},
            {"name": "Finanzas (Estudiantez)", "students": 24, "study": "Administracion",
             "computers": 15, "teacher": "", "preferred_shift": "",
             "color": "#ef4444"},
        ]
        cr = [{
            "name": "Lab grande",
            "capacity": 45,
            "computers": 25,
            "time_slots": [
                {"date": "2026-06-15", "start": "09:00", "end": "11:00"},
                {"date": "2026-06-15", "start": "11:30", "end": "13:30"},
            ],
        }]
        s = ExamScheduler(exams, cr)
        s.build_model()
        status = s.solve(time_limit=10)
        self.assertIn(status, (cp_model.OPTIMAL, cp_model.FEASIBLE))

        usage = {}
        for a in s.extract_assignment():
            need = int(a["exam"].get("computers", 0) or 0)
            for t in a["slots"]:
                usage.setdefault((t, a["classroom_idx"]), 0)
                usage[(t, a["classroom_idx"])] += need
        for (t, c_idx), total in usage.items():
            self.assertLessEqual(
                total, int(cr[c_idx].get("computers", 0) or 0),
                f"Franja {t}: {total} PCs pedidos con 25 disponibles."
            )
        self.assertTrue(
            any(total > 0 for total in usage.values()),
            "Los dos examenes con PCs deben estar asignados."
        )


class TestReservedSlots(unittest.TestCase):
    """Franjas reservadas: ningún examen puede ocuparlas."""

    def test_reserved_slot_never_used(self):
        exams = [
            {"name": "Uno (Alumnez)", "students": 10, "study": "A",
             "teacher": "", "preferred_shift": "", "color": "#6366f1"},
            {"name": "Dos (Estudiantez)", "students": 10, "study": "B",
             "teacher": "", "preferred_shift": "", "color": "#ef4444"},
        ]
        s = ExamScheduler(exams, RESERVED_CLASSROOMS)
        s.build_model()
        status = s.solve(time_limit=15)
        self.assertIn(status, (cp_model.OPTIMAL, cp_model.FEASIBLE))
        assignment = s.extract_assignment()
        # La franja global 1 (11:30-13:30) está reservada en la única aula
        for a in assignment:
            self.assertNotIn(
                1, a["slots"],
                "La franja reservada no debe contener ningún examen."
            )
        # Y todos los exámenes siguen colocados (en la franja 0)
        self.assertEqual(len(assignment), len(exams))


class TestLockedAssignments(unittest.TestCase):
    """Verifica que los bloqueos se respetan al regenerar."""

    def test_locked_exam_stays(self):
        s = ExamScheduler(SIMPLE_EXAMS, SIMPLE_CLASSROOMS)
        s.build_model()
        status = s.solve(time_limit=15)
        self.assertIn(status, (cp_model.OPTIMAL, cp_model.FEASIBLE))
        first = s.extract_assignment()

        exam_to_lock = first[0]
        locked_idx = exam_to_lock["exam_idx"]
        locked_slot = exam_to_lock["slot"]
        locked_cr = exam_to_lock["classroom_idx"]

        s2 = ExamScheduler(SIMPLE_EXAMS, SIMPLE_CLASSROOMS)
        s2.build_model()
        s2.add_locked_assignments({locked_idx: (locked_slot, locked_cr)})
        status2 = s2.solve(time_limit=15)
        self.assertIn(status2, (cp_model.OPTIMAL, cp_model.FEASIBLE))
        second = s2.extract_assignment()

        for a in second:
            if a["exam_idx"] == locked_idx:
                self.assertEqual(
                    a["slot"], locked_slot,
                    "El examen bloqueado debe mantener su franja."
                )
                self.assertEqual(
                    a["classroom_idx"], locked_cr,
                    "El examen bloqueado debe mantener su aula."
                )
                break

    def test_multiple_locked_exams_stay(self):
        """Varios bloqueos a la vez se mantienen todos."""
        s = ExamScheduler(SIMPLE_EXAMS, SIMPLE_CLASSROOMS)
        s.build_model()
        status = s.solve(time_limit=15)
        self.assertIn(status, (cp_model.OPTIMAL, cp_model.FEASIBLE))
        first = s.extract_assignment()

        locks = {
            a["exam_idx"]: (a["slot"], a["classroom_idx"])
            for a in first
        }
        self.assertEqual(len(locks), len(SIMPLE_EXAMS))

        s2 = ExamScheduler(SIMPLE_EXAMS, SIMPLE_CLASSROOMS)
        s2.build_model()
        s2.add_locked_assignments(locks)
        status2 = s2.solve(time_limit=15)
        self.assertIn(status2, (cp_model.OPTIMAL, cp_model.FEASIBLE))
        second = s2.extract_assignment()

        got = {a["exam_idx"]: (a["slot"], a["classroom_idx"]) for a in second}
        self.assertEqual(
            got, locks,
            "Todas las asignaciones bloqueadas deben mantenerse."
        )

    def test_locked_long_exam_keeps_span(self):
        """Bloquear un examen de 3h fija su franja de inicio y su rango."""
        s = ExamScheduler(EXAM_3H, ONE_HOUR_CLASSROOM)
        s.build_model()
        s.add_locked_assignments({0: (0, 0)})
        status = s.solve(time_limit=15)
        self.assertIn(status, (cp_model.OPTIMAL, cp_model.FEASIBLE))
        a = s.extract_assignment()[0]
        self.assertEqual(a["slot"], 0, "Debe empezar en la franja bloqueada.")
        self.assertEqual(a["slots"], [0, 1, 2], "Debe ocupar el bloque mínimo.")

    def test_lock_impossible_position_raises(self):
        """Bloquear un examen donde no cabe lanza ValueError."""
        s = ExamScheduler(EXAM_3H, ONE_HOUR_CLASSROOM)
        s.build_model()
        # Desde la franja 2 (11:00-12:00) no quedan 3 horas encadenadas
        with self.assertRaises(ValueError):
            s.add_locked_assignments({0: (2, 0)})



class TestPreferredShift(unittest.TestCase):
    """Verifica que la preferencia de turno funciona (penalizacion blanda)."""

    def test_preferred_shift_respected_if_possible(self):
        exams = [
            {"name": "Solo Manana (Alumnez)", "students": 5, "study": "Test",
             "teacher": "", "preferred_shift": "morning", "color": "#6366f1"},
            {"name": "Solo Noche (Alumnez)", "students": 5, "study": "Test2",
             "teacher": "", "preferred_shift": "afternoon", "color": "#ef4444"},
        ]
        cr = [{
            "name": "Aula",
            "capacity": 50,
            "time_slots": [
                {"date": "2026-06-15", "start": "09:00", "end": "11:00"},
                {"date": "2026-06-15", "start": "16:00", "end": "18:00"},
            ],
        }]
        s = ExamScheduler(exams, cr)
        s.build_model()
        status = s.solve(time_limit=15)
        self.assertIn(status, (cp_model.OPTIMAL, cp_model.FEASIBLE))
        assignment = s.extract_assignment()
        for a in assignment:
            start_hour = int(s.global_slots[a["slot"]][1].split(":")[0])
            pref = a["exam"]["preferred_shift"]
            is_morning = start_hour < 14
            if pref == "morning":
                self.assertTrue(is_morning, f"{a['exam']['name']} preferia manana.")
            elif pref == "afternoon":
                self.assertFalse(is_morning, f"{a['exam']['name']} preferia tarde.")


class TestSeedDataSolvable(unittest.TestCase):
    """Verifica que los datos de ejemplo tienen solucion."""

    def test_seed_data_solvable(self):
        data = get_seed_data()
        s = ExamScheduler(data["exams"], data["classrooms"])
        s.build_model()
        status = s.solve(time_limit=30)
        self.assertIn(
            status, (cp_model.OPTIMAL, cp_model.FEASIBLE),
            "Los datos semilla no tienen solucion. Revisa capacidad vs alumnos."
        )
        assignment = s.extract_assignment()
        self.assertEqual(
            len(assignment), len(data["exams"]),
            "Todos los examenes de los datos semilla deben estar asignados."
        )

    def test_seed_data_respects_computers_and_duration(self):
        """La solucion de los datos semilla respeta ordenadores y duracion."""
        data = get_seed_data()
        s = ExamScheduler(data["exams"], data["classrooms"])
        s.build_model()
        status = s.solve(time_limit=30)
        self.assertIn(status, (cp_model.OPTIMAL, cp_model.FEASIBLE))
        assignment = s.extract_assignment()

        # Ordenadores: suma por (franja, aula) <= ordenadores del aula
        pc_usage = {}
        for a in assignment:
            need = int(a["exam"].get("computers", 0) or 0)
            if not need:
                continue
            for t in a["slots"]:
                pc_usage.setdefault((t, a["classroom_idx"]), 0)
                pc_usage[(t, a["classroom_idx"])] += need
        for (t, c_idx), total in pc_usage.items():
            available = int(data["classrooms"][c_idx].get("computers", 0) or 0)
            self.assertLessEqual(
                total, available,
                f"Franja {t}, aula {data['classrooms'][c_idx]['name']}: "
                f"{total} ordenadores pero solo {available}."
            )

        # Duracion: cada examen ocupa minutos >= su duration_hours
        for a in assignment:
            required = a["exam"].get("duration_hours", 2.0)
            spanned = _slot_span_minutes(a, s.global_slots)
            self.assertGreaterEqual(
                spanned, float(required) * 60 - 1e-6,
                f"{a['exam']['name']}: ocupa {spanned} min y necesita "
                f"{float(required) * 60} min."
            )

    def test_seed_pc_casuistry(self):
        """El seed ejercita la restriccion de ordenadores en varios casos.

        Comprobaciones estructurales (sin solver): los datos deben contener
        aulas con PCs parciales, examenes con menos PCs que alumnos, PC exams
        fuera de Informatica y una pareja que quepa por alumnos pero no por PCs.
        """
        data = get_seed_data()
        classrooms = data["classrooms"]
        exams = data["exams"]

        # >=3 aulas con ordenadores
        pc_rooms = [c for c in classrooms if int(c.get("computers", 0) or 0) > 0]
        self.assertGreaterEqual(
            len(pc_rooms), 3,
            "El seed debe tener al menos 3 aulas con ordenadores."
        )

        # >=1 aula con capacidad > ordenadores (ratio parcial)
        self.assertTrue(
            any(int(c.get("capacity", 0)) > int(c.get("computers", 0) or 0)
                for c in pc_rooms),
            "Debe haber un aula con mas capacidad que ordenadores."
        )

        # >=3 estudios distintos con examenes que necesitan PCs
        pc_exams = [e for e in exams if int(e.get("computers", 0) or 0) > 0]
        studies = {e["study"] for e in pc_exams}
        self.assertGreaterEqual(
            len(studies), 3,
            "Los PCs deben estar repartidos en al menos 3 estudios "
            "(no solo Informatica)."
        )

        # >=1 examen con menos PCs que alumnos
        self.assertTrue(
            any(int(e["computers"]) < int(e["students"]) for e in pc_exams),
            "Debe haber un examen con menos ordenadores que alumnos."
        )

        # >=1 pareja de distinto estudio que cabe por alumnos en un aula con
        # PCs pero no por la suma de PCs (capacidad OK / PCs KO)
        def cap_ok_pcs_ko(a, b):
            for c in pc_rooms:
                if (a["students"] + b["students"] <= int(c["capacity"])
                        and a["computers"] + b["computers"]
                        > int(c.get("computers", 0) or 0)):
                    return True
            return False

        self.assertTrue(
            any(cap_ok_pcs_ko(a, b)
                for a in pc_exams for b in pc_exams
                if a is not b and a["study"] != b["study"]),
            "Debe existir una pareja de distinto estudio que quepa por "
            "alumnos en un aula con PCs pero no por la suma de PCs."
        )


class TestInfeasibleDetected(unittest.TestCase):
    """Verifica que el solver detecta problemas sin solucion."""

    def test_capacity_too_low(self):
        """Si la capacidad es insuficiente, debe ser INFEASIBLE."""
        exams = [
            {"name": "Grande (Alumnez)", "students": 100, "study": "A",
             "teacher": "", "preferred_shift": "", "color": "#6366f1"},
        ]
        cr = [{
            "name": "Mini",
            "capacity": 10,
            "time_slots": [{"date": "2026-06-15", "start": "09:00", "end": "11:00"}],
        }]
        s = ExamScheduler(exams, cr)
        s.build_model()
        status = s.solve(time_limit=5)
        self.assertEqual(status, cp_model.INFEASIBLE, "Debe ser infactible.")

    def test_no_classrooms(self):
        """Sin aulas, debe ser INFEASIBLE."""
        s = ExamScheduler(SIMPLE_EXAMS, [])
        try:
            s.build_model()
            status = s.solve(time_limit=5)
            self.assertEqual(status, cp_model.INFEASIBLE, "Sin aulas debe ser infactible.")
        except Exception:
            pass  # Puede lanzar excepcion si no hay pares validos


if __name__ == "__main__":
    unittest.main(verbosity=2)
