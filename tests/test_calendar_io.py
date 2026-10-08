# -*- coding: utf-8 -*-
"""Tests de exportación/importación del calendario (calendar_io)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from calendar_io import (
    build_calendar_export, parse_calendar, restore_calendar,
    names_match, classrooms_match,
    FORMAT_NAME, FORMAT_VERSION,
)
from scheduler import ExamScheduler
from ortools.sat.python import cp_model


# ── Fixtures ligeras ────────────────────────────────────────────────────
EXAMS = [
    {"name": "Programacion (Alumnez)", "students": 20, "study": "Informatica",
     "teacher": "Profesorez Uno", "duration_hours": 2.0, "computers": 0,
     "color": "#6366f1"},
    {"name": "Finanzas (Estudiantez)", "students": 15, "study": "Administracion",
     "teacher": "Profesorez Dos", "duration_hours": 2.0, "computers": 0,
     "color": "#ef4444"},
]

CLASSROOMS = [
    {
        "name": "Aula Normal",
        "capacity": 30,
        "time_slots": [
            {"date": "2026-06-15", "start": "09:00", "end": "11:00"},
            {"date": "2026-06-15", "start": "11:30", "end": "13:30"},
        ],
    },
    {
        "name": "Aula Grande",
        "capacity": 50,
        "time_slots": [
            {"date": "2026-06-15", "start": "09:00", "end": "11:00"},
            {"date": "2026-06-16", "start": "09:00", "end": "11:00"},
        ],
    },
]


def _solve():
    """Resuelve la fixture y devuelve (solutions, global_slots)."""
    s = ExamScheduler([dict(e) for e in EXAMS],
                      [dict(c, time_slots=[dict(t) for t in c["time_slots"]])
                       for c in CLASSROOMS])
    s.build_model()
    status = s.solve(time_limit=10)
    assert status in (cp_model.OPTIMAL, cp_model.FEASIBLE), \
        f"solver no factible: {status}"
    sols = s.generate_multiple_solutions(num_options=2, time_limit=5)
    return sols, s.global_slots


class TestBuildExport(unittest.TestCase):
    """Construcción del dict de exportación."""

    @classmethod
    def setUpClass(cls):
        cls.solutions, cls.global_slots = _solve()

    def _export(self, locks=None):
        return build_calendar_export(
            "Proyecto Test", EXAMS, CLASSROOMS, self.solutions,
            self.solutions[0][0], locks or {}, self.global_slots,
        )

    def test_export_structure(self):
        d = self._export()
        self.assertEqual(d["format"], FORMAT_NAME)
        self.assertEqual(d["version"], FORMAT_VERSION)
        self.assertEqual(d["project_name"], "Proyecto Test")
        self.assertEqual(len(d["options"]), len(self.solutions))
        self.assertIn("exams", d)
        self.assertIn("classrooms", d)
        self.assertIn("exported_at", d)

    def test_export_all_options_and_current(self):
        d = self._export()
        idxs = [o["idx"] for o in d["options"]]
        self.assertEqual(idxs, [i for i, _, _ in self.solutions])
        self.assertEqual(d["current_option"], self.solutions[0][0])
        for opt in d["options"]:
            self.assertTrue(opt["assignments"])

    def test_export_assignments_use_names_and_dates(self):
        d = self._export()
        a = d["options"][0]["assignments"][0]
        self.assertIn(a["exam"], [e["name"] for e in EXAMS])
        self.assertIn(a["classroom"], [c["name"] for c in CLASSROOMS])
        for s in a["slots"]:
            self.assertCountEqual(list(s.keys()), ["date", "start", "end"])

    def test_export_locks_by_name(self):
        # Primer examen de la primera opción, franja inicial
        _, _, assignment = self.solutions[0]
        first = assignment[0]
        locks = {first["exam_idx"]: (first["slot"], first["classroom_idx"])}
        d = self._export(locks=locks)
        self.assertEqual(len(d["locks"]), 1)
        self.assertEqual(d["locks"][0]["exam"], first["exam"]["name"])
        self.assertEqual(d["locks"][0]["classroom"], first["classroom"]["name"])
        self.assertEqual(d["locks"][0]["date"],
                         self.global_slots[first["slot"]][0])
        self.assertEqual(d["locks"][0]["start"],
                         self.global_slots[first["slot"]][1])


class TestParse(unittest.TestCase):
    """Validación del JSON importado."""

    def _valid(self):
        return {
            "format": FORMAT_NAME, "version": FORMAT_VERSION,
            "project_name": "P", "current_option": 1,
            "exams": EXAMS, "classrooms": CLASSROOMS,
            "options": [{"idx": 1, "slots_used": 1, "assignments": [
                {"exam": "Programacion (Alumnez)", "classroom": "Aula Normal",
                 "slots": [{"date": "2026-06-15", "start": "09:00",
                            "end": "11:00"}]},
            ]}],
            "locks": [],
        }

    def test_valid_calendar_parses(self):
        d = parse_calendar(self._valid())
        self.assertEqual(d["format"], FORMAT_NAME)

    def test_rejects_non_dict(self):
        with self.assertRaises(ValueError):
            parse_calendar([1, 2, 3])

    def test_rejects_project_json(self):
        with self.assertRaises(ValueError) as ctx:
            parse_calendar({"project_name": "P", "exams": [],
                            "classrooms": []})
        self.assertIn("PROYECTO", str(ctx.exception))

    def test_rejects_unknown_format(self):
        d = self._valid()
        d["format"] = "otra-cosa"
        with self.assertRaises(ValueError):
            parse_calendar(d)

    def test_rejects_future_version(self):
        d = self._valid()
        d["version"] = FORMAT_VERSION + 1
        with self.assertRaises(ValueError) as ctx:
            parse_calendar(d)
        self.assertIn("Versión", str(ctx.exception))

    def test_rejects_empty_options(self):
        d = self._valid()
        d["options"] = []
        with self.assertRaises(ValueError):
            parse_calendar(d)

    def test_rejects_assignment_without_slots(self):
        d = self._valid()
        d["options"][0]["assignments"][0]["slots"] = []
        with self.assertRaises(ValueError) as ctx:
            parse_calendar(d)
        self.assertIn("slots", str(ctx.exception))

    def test_rejects_slot_missing_keys(self):
        d = self._valid()
        d["options"][0]["assignments"][0]["slots"] = [
            {"date": "2026-06-15", "start": "09:00"}]
        with self.assertRaises(ValueError):
            parse_calendar(d)


class TestRestore(unittest.TestCase):
    """Restauración de soluciones y bloqueos desde el JSON."""

    @classmethod
    def setUpClass(cls):
        cls.solutions, cls.global_slots = _solve()
        cls.export = build_calendar_export(
            "Proyecto Test", EXAMS, CLASSROOMS, cls.solutions,
            cls.solutions[0][0], {}, cls.global_slots,
        )
        parse_calendar(cls.export)

    def _restore(self, parsed=None, exams=None, classrooms=None):
        return restore_calendar(parsed or self.export,
                                exams or EXAMS,
                                classrooms or CLASSROOMS)

    def test_roundtrip_assignments(self):
        solutions, locks, warnings, skipped = self._restore()
        self.assertEqual(len(solutions), len(self.solutions))
        for (i1, n1, a1), (i2, n2, a2) in zip(solutions, self.solutions):
            self.assertEqual(i1, i2)
            self.assertEqual(n1, n2)
            self.assertEqual(len(a1), len(a2))
            # Comparar como conjunto: el orden puede variar
            key = lambda x: (x["exam"]["name"], x["classroom"]["name"])
            for x, y in zip(sorted(a1, key=key), sorted(a2, key=key)):
                self.assertEqual(x["exam"]["name"], y["exam"]["name"])
                self.assertEqual(x["classroom"]["name"], y["classroom"]["name"])
                self.assertEqual(x["slots"], y["slots"])
                self.assertEqual(x["exam_idx"], y["exam_idx"])
                self.assertEqual(x["classroom_idx"], y["classroom_idx"])
        self.assertEqual(skipped, [])

    def test_roundtrip_no_warnings_for_solver_output(self):
        _, _, warnings, _ = self._restore()
        self.assertEqual(warnings, [],
                         f"El output del solver no debe generar avisos: {warnings}")

    def test_unknown_exam_skipped(self):
        import copy
        bad = copy.deepcopy(self.export)
        bad["options"][0]["assignments"][0]["exam"] = "No Existe (Nadie)"
        solutions, _, _, skipped = self._restore(parsed=bad)
        self.assertTrue(any("no existe" in s for s in skipped))
        total = sum(len(a) for _, _, a in solutions)
        self.assertEqual(total,
                         sum(len(a) for _, _, a in self.solutions) - 1)

    def test_unknown_slot_skipped(self):
        import copy
        bad = copy.deepcopy(self.export)
        bad["options"][0]["assignments"][0]["slots"][0]["start"] = "23:00"
        _, _, _, skipped = self._restore(parsed=bad)
        self.assertTrue(any("23:00" in s for s in skipped))

    def test_invalid_block_skipped(self):
        # Examen de 2h en una sola franja de 1h → bloque no encajable
        parsed = {
            "format": FORMAT_NAME, "version": FORMAT_VERSION,
            "current_option": 1, "exams": EXAMS, "classrooms": CLASSROOMS,
            "options": [{"idx": 1, "assignments": [
                {"exam": "Programacion (Alumnez)", "classroom": "Aula Normal",
                 "slots": [{"date": "2026-06-15", "start": "09:00",
                            "end": "11:00"}]}]}],
            "locks": [],
        }
        # 09:00-11:00 ES 2h, así que sí encaja: probamos con 11:30-13:30
        # encadenado mal (hueco). Usamos duration 3h para que no quepa.
        parsed["exams"] = [dict(EXAMS[0], duration_hours=3.0)]
        _, _, _, skipped = restore_calendar(parsed, parsed["exams"], CLASSROOMS)
        self.assertTrue(skipped, "Una asignación no encajable debe omitirse")

    def test_capacity_violation_warns_but_keeps(self):
        # Determinista: dos exámenes en Aula Normal (cap 30), misma franja
        parsed = {
            "format": FORMAT_NAME, "version": FORMAT_VERSION,
            "current_option": 1, "exams": EXAMS, "classrooms": CLASSROOMS,
            "options": [{"idx": 1, "assignments": [
                {"exam": "Programacion (Alumnez)", "classroom": "Aula Normal",
                 "slots": [{"date": "2026-06-15", "start": "09:00",
                            "end": "11:00"}]},
                {"exam": "Finanzas (Estudiantez)", "classroom": "Aula Normal",
                 "slots": [{"date": "2026-06-15", "start": "09:00",
                            "end": "11:00"}]},
            ]}],
            "locks": [],
        }
        solutions, _, warnings, skipped = restore_calendar(
            parsed, EXAMS, CLASSROOMS)
        self.assertEqual(skipped, [])
        self.assertTrue(any("alumnos" in w for w in warnings),
                        f"Debe avisar de capacidad: {warnings}")
        self.assertEqual(len(solutions[0][2]), 2, "Se conserva la asignación")

    def test_locks_roundtrip(self):
        _, _, assignment = self.solutions[0]
        first = assignment[0]
        locks = {first["exam_idx"]: (first["slot"], first["classroom_idx"])}
        exp = build_calendar_export(
            "P", EXAMS, CLASSROOMS, self.solutions,
            self.solutions[0][0], locks, self.global_slots)
        _, restored_locks, _, skipped = restore_calendar(exp, EXAMS, CLASSROOMS)
        self.assertEqual(restored_locks,
                         {first["exam_idx"]: (first["slot"],
                                              first["classroom_idx"])})
        self.assertEqual(skipped, [])

    def test_invalid_lock_skipped(self):
        exp = dict(self.export)
        exp["locks"] = [{"exam": "Programacion (Alumnez)",
                         "classroom": "Aula Normal",
                         "date": "2026-06-16", "start": "09:00"}]
        # 2026-06-16 09:00 no existe en Aula Normal (sí en Aula Grande):
        # el bloque no es válido para esa combinación → omitido
        _, locks, _, skipped = restore_calendar(exp, EXAMS, CLASSROOMS)
        self.assertEqual(locks, {})
        self.assertTrue(skipped, "El bloqueo inválido debe omitirse")


class TestNameMatching(unittest.TestCase):
    """Comparación de nombres para decidir reemplazo de datos."""

    def test_names_match(self):
        self.assertTrue(names_match(EXAMS, [dict(e) for e in EXAMS]))

    def test_names_differ(self):
        other = [dict(EXAMS[0], name="Otro")]
        self.assertFalse(names_match(EXAMS, other))

    def test_empty_is_false(self):
        self.assertFalse(names_match([], EXAMS))
        self.assertFalse(names_match(EXAMS, []))

    def test_classrooms_match(self):
        self.assertTrue(classrooms_match(CLASSROOMS,
                                         [dict(c) for c in CLASSROOMS]))
        self.assertFalse(classrooms_match(CLASSROOMS, []))


if __name__ == "__main__":
    unittest.main(verbosity=2)
