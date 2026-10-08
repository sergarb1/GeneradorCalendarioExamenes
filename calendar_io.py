# -*- coding: utf-8 -*-
"""
Exportación e importación del CALENDARIO generado a/from JSON.

A diferencia de la exportación de proyecto (solo exámenes + aulas), este
formato es AUTOCONTENIDO: incluye los datos del proyecto, TODAS las
opciones generadas, la opción seleccionada y los bloqueos activos, de
forma que se puede compartir un fichero y regenerar con bloqueos al
importarlo.

Referencias por NOMBRE/FECHA (no por índices internos): cada asignación
se describe por nombre de examen, nombre de aula y la lista de franjas
(date, start, end) que ocupa. Así el JSON es estable, editable a mano
y utilizable por una IA (ver prompts_generar_examenes_aulas_JSON.md).

Formato:
{
  "format": "calendario-examenes",
  "version": 1,
  "project_name": "...",
  "exported_at": "ISO-8601",
  "current_option": 1,
  "exams": [...], "classrooms": [...],
  "options": [{"idx": 1, "slots_used": 34,
               "assignments": [{"exam": "...", "classroom": "...",
                                "slots": [{"date","start","end"}, ...]}]}],
  "locks": [{"exam": "...", "classroom": "...", "date": "...", "start": "..."}]
}
"""
from __future__ import annotations

from datetime import datetime

from scheduler import build_global_pool, block_for_start

FORMAT_NAME = "calendario-examenes"
FORMAT_VERSION = 1


# ── Exportación ─────────────────────────────────────────────────────────

def build_calendar_export(project_name, exams, classrooms, solutions,
                          current_option, locks, global_slots):
    """
    Construye el dict JSON de calendario.

    solutions:    lista de (idx, slots_used, assignment) del solver
    current_option: idx de la opción visible
    locks:        {exam_idx: (start_slot_idx, classroom_idx)}
    global_slots: [(date, start, end), ...] del scheduler
    """
    name_of_exam = {i: e.get("name", f"Examen {i}") for i, e in enumerate(exams)}

    options = []
    for idx, slots_used, assignment in solutions:
        assigns = []
        for a in assignment:
            slots = []
            for t in a.get("slots", [a["slot"]]):
                date, start, end = global_slots[t]
                slots.append({"date": date, "start": start, "end": end})
            assigns.append({
                "exam": a["exam"].get("name", ""),
                "classroom": a["classroom"].get("name", ""),
                "slots": slots,
            })
        options.append({"idx": idx, "slots_used": slots_used,
                        "assignments": assigns})

    lock_list = []
    for exam_idx, (start_slot, classroom_idx) in (locks or {}).items():
        if exam_idx not in name_of_exam:
            continue
        if start_slot < 0 or start_slot >= len(global_slots):
            continue
        date, start, end = global_slots[start_slot]
        cname = (classrooms[classroom_idx].get("name", "")
                 if 0 <= classroom_idx < len(classrooms) else "")
        lock_list.append({"exam": name_of_exam[exam_idx], "classroom": cname,
                          "date": date, "start": start, "end": end})

    return {
        "format": FORMAT_NAME,
        "version": FORMAT_VERSION,
        "project_name": project_name or "",
        "exported_at": datetime.now().isoformat(timespec="seconds"),
        "current_option": current_option,
        "exams": exams,
        "classrooms": classrooms,
        "options": options,
        "locks": lock_list,
    }


# ── Validación / parseo ─────────────────────────────────────────────────

def parse_calendar(data):
    """
    Valida la estructura del JSON importado y devuelve el dict.

    Lanza ValueError con un mensaje claro si no es un calendario válido.
    """
    if not isinstance(data, dict):
        raise ValueError("El JSON debe ser un objeto con 'options' y 'exams'")

    if "options" not in data:
        if "exams" in data and "classrooms" in data:
            raise ValueError(
                "Esto es un JSON de PROYECTO (exámenes/aulas), no de "
                "calendario. Usa 📥 Importar todo en la pestaña Proyecto."
            )
        raise ValueError("El JSON no contiene 'options' (opciones de calendario)")

    fmt = data.get("format")
    if fmt is not None and fmt != FORMAT_NAME:
        raise ValueError(
            f"Formato desconocido: «{fmt}» (se espera «{FORMAT_NAME}»)"
        )

    version = data.get("version", FORMAT_VERSION)
    try:
        version = int(version)
    except (TypeError, ValueError):
        raise ValueError(f"Versión inválida: {version!r}")
    if version > FORMAT_VERSION:
        raise ValueError(
            f"Versión {version} no soportada (máxima {FORMAT_VERSION})"
        )

    options = data["options"]
    if not isinstance(options, list) or not options:
        raise ValueError("'options' debe ser una lista no vacía de opciones")

    for i, opt in enumerate(options):
        if not isinstance(opt, dict):
            raise ValueError(f"Opción {i}: debe ser un objeto")
        if not isinstance(opt.get("assignments"), list):
            raise ValueError(f"Opción {i}: falta 'assignments' (lista)")
        for j, a in enumerate(opt["assignments"]):
            if not isinstance(a, dict):
                raise ValueError(f"Opción {i}, asignación {j}: debe ser un objeto")
            if not a.get("exam"):
                raise ValueError(f"Opción {i}, asignación {j}: falta 'exam'")
            if not isinstance(a.get("slots"), list) or not a["slots"]:
                raise ValueError(
                    f"Opción {i}, asignación «{a.get('exam')}»: "
                    "'slots' debe ser una lista no vacía"
                )
            for s in a["slots"]:
                if not isinstance(s, dict) or not all(
                        k in s for k in ("date", "start", "end")):
                    raise ValueError(
                        f"Opción {i}, asignación «{a.get('exam')}»: "
                        "cada slot necesita 'date', 'start' y 'end'"
                    )

    locks = data.get("locks", [])
    if not isinstance(locks, list):
        raise ValueError("'locks' debe ser una lista")

    return data


def names_match(file_exams, current_exams):
    """True si ambos conjuntos de exámenes tienen los mismos nombres."""
    if not file_exams or not current_exams:
        return False
    return {e.get("name") for e in file_exams} == \
           {e.get("name") for e in current_exams}


def classrooms_match(file_classrooms, current_classrooms):
    """True si ambos conjuntos de aulas tienen los mismos nombres."""
    if not file_classrooms or not current_classrooms:
        return False
    return {c.get("name") for c in file_classrooms} == \
           {c.get("name") for c in current_classrooms}


# ── Restauración ────────────────────────────────────────────────────────

def restore_calendar(parsed, exams, classrooms):
    """
    Reconstruye soluciones y bloqueos a partir del JSON ya parseado.

    Devuelve (solutions, locks, warnings, skipped):
      solutions: [(idx, slots_used, assignment), ...] con assignment en
                 el mismo formato que ExamScheduler.extract_assignment()
      locks:     {exam_idx: (start_slot_idx, classroom_idx)}
      warnings:  [str] violaciones de capacidad/PCs/solape (se conservan)
      skipped:   [str] asignaciones/bloqueos omitidos (no reconstruibles)
    """
    global_slots, key_to_idx, class_valid = build_global_pool(classrooms)
    exam_by_name = {}
    for i, e in enumerate(exams):
        exam_by_name.setdefault(e.get("name"), i)
    class_by_name = {}
    for i, c in enumerate(classrooms):
        class_by_name.setdefault(c.get("name"), i)

    solutions = []
    skipped = []
    warnings = []

    for opt in parsed["options"]:
        idx = opt.get("idx", len(solutions) + 1)
        assignment = []
        seen_exams = set()

        for a in opt["assignments"]:
            ename = a["exam"]
            cname = a.get("classroom", "")
            tag = f"Opción {idx} · «{ename}»"

            e_idx = exam_by_name.get(ename)
            if e_idx is None:
                skipped.append(f"{tag}: el examen no existe en el proyecto")
                continue
            if e_idx in seen_exams:
                skipped.append(f"{tag}: examen repetido en la misma opción")
                continue

            c_idx = class_by_name.get(cname)
            if c_idx is None:
                skipped.append(f"{tag}: el aula «{cname}» no existe")
                continue

            # Claves (date,start,end) -> índices globales
            slot_idxs = []
            ok = True
            for s in a["slots"]:
                gi = key_to_idx.get((s["date"], s["start"], s["end"]))
                if gi is None:
                    skipped.append(
                        f"{tag}: la franja {s['date']} {s['start']}-{s['end']} "
                        f"no existe en ninguna aula"
                    )
                    ok = False
                    break
                slot_idxs.append(gi)
            if not ok:
                continue

            if len(set(slot_idxs)) != len(slot_idxs):
                skipped.append(f"{tag}: franjas duplicadas en la asignación")
                continue
            slot_idxs.sort()

            exam = exams[e_idx]
            first = global_slots[slot_idxs[0]]

            # El bloque debe ser válido: duración encadenable, no reservada
            block = block_for_start(exam, classrooms[c_idx], slot_idxs[0],
                                    global_slots, key_to_idx)
            if block is None or list(block) != slot_idxs:
                skipped.append(
                    f"{tag}: las franjas no forman un bloque válido "
                    "(duración, franja reservada o hueco)"
                )
                continue

            seen_exams.add(e_idx)
            last = global_slots[slot_idxs[-1]]
            assignment.append({
                "exam": exam,
                "exam_idx": e_idx,
                "block": None,
                "slot": slot_idxs[0],
                "slots": slot_idxs,
                "slot_end": slot_idxs[-1],
                "slot_label": f"{first[0]} {first[1]}-{last[2]}",
                "classroom": classrooms[c_idx],
                "classroom_idx": c_idx,
            })

        assignment.sort(key=lambda x: (x["slot"], x["classroom"]["name"]))
        used = {t for x in assignment for t in x["slots"]}
        solutions.append((idx, len(used), assignment))

    # ── Comprobación de restricciones (no bloquea: solo avisa) ──
    warnings.extend(_check_constraints(solutions, classrooms))

    # ── Bloqueos ──
    locks = {}
    for lk in parsed.get("locks", []):
        ename = lk.get("exam")
        e_idx = exam_by_name.get(ename)
        if e_idx is None:
            skipped.append(f"Bloqueo «{ename}»: el examen no existe")
            continue
        c_idx = class_by_name.get(lk.get("classroom", ""))
        if c_idx is None:
            skipped.append(f"Bloqueo «{ename}»: el aula no existe")
            continue
        # La clave de bloqueo es (date, start) de la franja de INICIO:
        # preferir match exacto (date,start,end); si no, (date,start)
        gi = key_to_idx.get((lk.get("date"), lk.get("start"), lk.get("end")))
        if gi is None:
            for t, (d, st, _en) in enumerate(global_slots):
                if d == lk.get("date") and st == lk.get("start"):
                    gi = t
                    break
        if gi is None:
            skipped.append(
                f"Bloqueo «{ename}»: la franja {lk.get('date')} "
                f"{lk.get('start')} no existe"
            )
            continue
        exam = exams[e_idx]
        if block_for_start(exam, classrooms[c_idx], gi,
                           global_slots, key_to_idx) is None:
            skipped.append(
                f"Bloqueo «{ename}»: el examen no puede empezar ahí "
                "(duración, ordenadores o franja reservada)"
            )
            continue
        locks[e_idx] = (gi, c_idx)

    return solutions, locks, warnings, skipped


def _check_constraints(solutions, classrooms):
    """Detecta solapes de estudio/profesor, capacidad y PCs excedidos."""
    problems = []
    for idx, _n, assignment in solutions:
        used = {}       # (slot, classroom_idx) -> (students, computers)
        by_study = {}   # (slot, study) -> [exam names]
        by_teacher = {}  # (slot, teacher) -> [exam names]
        for a in assignment:
            exam = a["exam"]
            for t in a["slots"]:
                key = (t, a["classroom_idx"])
                s, p = used.get(key, (0, 0))
                used[key] = (s + int(exam.get("students", 0)),
                             p + int(exam.get("computers", 0) or 0))
                study = exam.get("study", "")
                if study:
                    by_study.setdefault((t, study), []).append(exam.get("name"))
                teacher = exam.get("teacher")
                if teacher:
                    by_teacher.setdefault((t, teacher), []).append(exam.get("name"))

        for (t, c_idx), (s, p) in used.items():
            cap = int(classrooms[c_idx].get("capacity", 0))
            if s > cap:
                problems.append(
                    f"Opción {idx}: franja {t} en «{classrooms[c_idx]['name']}» "
                    f"con {s} alumnos > capacidad {cap}"
                )
            pc = int(classrooms[c_idx].get("computers", 0) or 0)
            if p > pc:
                problems.append(
                    f"Opción {idx}: franja {t} en «{classrooms[c_idx]['name']}» "
                    f"con {p} ordenadores > {pc} disponibles"
                )
        for (t, study), names in by_study.items():
            if len(names) > 1:
                problems.append(
                    f"Opción {idx}: {len(names)} exámenes de «{study}» "
                    f"solapados en la franja {t}"
                )
        for (t, teacher), names in by_teacher.items():
            if len(names) > 1:
                problems.append(
                    f"Opción {idx}: {len(names)} exámenes de «{teacher}» "
                    f"solapados en la franja {t}"
                )
    return problems
