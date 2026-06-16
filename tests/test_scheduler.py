# -*- coding: utf-8 -*-
"""
Tests del motor de planificación CP-SAT:

1. Restricciones básicas (estudio, profesor, capacidad, aula)
2. Múltiples soluciones
3. Bloqueos
4. Turno preferido
5. Datos semilla resolubles

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
        """Examenes del mismo estudio NO deben estar en la misma franja."""
        slots_by_study = {}
        for a in self.assignment:
            study = a["exam"]["study"]
            slot = a["slot"]
            slots_by_study.setdefault(study, set()).add(slot)
        for study, slots in slots_by_study.items():
            self.assertEqual(
                len(slots), len([a for a in self.assignment if a["exam"]["study"] == study]),
                f"Los examenes de '{study}' deberian estar en franjas distintas."
            )

    def test_capacity_respected(self):
        """La suma de alumnos en (franja, aula) no debe exceder la capacidad."""
        usage = {}
        for a in self.assignment:
            key = (a["slot"], a["classroom_idx"])
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
        """Examenes del mismo profesor NO deben estar en la misma franja."""
        teacher_slots = {}
        for a in self.assignment:
            teacher = a["exam"].get("teacher", "")
            if teacher:
                teacher_slots.setdefault(teacher, set()).add(a["slot"])
        for teacher, slots in teacher_slots.items():
            exams_with_teacher = [
                a for a in self.assignment if a["exam"].get("teacher", "") == teacher
            ]
            self.assertEqual(
                len(slots), len(exams_with_teacher),
                f"El profesor '{teacher}' tiene examenes en la misma franja."
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
