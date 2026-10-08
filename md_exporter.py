# Copyright (C) 2026 Sergi Albuixech
# SPDX-License-Identifier: AGPL-3.0-or-later


def _assignment_slots(a):
    """Todas las franjas globales que ocupa una asignación."""
    return a.get("slots", [a["slot"]])


def _exam_range(a):
    """Rango horario real del examen ('09:00-13:30') a partir del label."""
    label = a.get("slot_label", "")
    return label.split(" ", 1)[1] if " " in label else label


def _duration_label(exam):
    """Duración declarada del examen ('2 h')."""
    try:
        dur = float(exam.get("duration_hours", 2.0) or 2.0)
    except (TypeError, ValueError):
        dur = 2.0
    return f"{dur:g} h"


def export_calendar_to_md(assignment, exams, classrooms, filepath, project_name=""):
    """Exporta el calendario generado a Markdown."""
    lines = []

    if project_name:
        lines.append(f"# Calendario de Exámenes — {project_name}")
    else:
        lines.append("# Calendario de Exámenes")
    lines.append("")

    n_exams = len(exams)
    total_students = sum(e["students"] for e in exams)
    n_slots = len({t for a in assignment for t in _assignment_slots(a)})
    n_classrooms = len(classrooms)
    n_studies = len({e["study"] for e in exams})
    n_pcs = sum(int(e.get("computers", 0) or 0) for e in exams)
    pcs_txt = f" · 💻 {n_pcs} ordenadores" if n_pcs else ""
    lines.append(f"📋 {n_exams} exámenes · 🕐 {n_slots} franjas · 🏫 {n_classrooms} aulas · 👥 {total_students} alumnos · 📚 {n_studies} estudios{pcs_txt}")
    lines.append("")

    groups = {}
    for a in sorted(assignment, key=lambda x: (x["slot"], x["classroom"]["name"])):
        groups.setdefault(a["slot"], []).append(a)

    for t in sorted(groups.keys()):
        label = groups[t][0]["slot_label"] if groups[t] else f"Franja {t+1}"
        lines.append(f"## 🕐 {label}")
        lines.append("")
        lines.append("| Aula | Examen | Alumnos | Estudio | Horario | Duración | Ordenadores |")
        lines.append("|------|--------|:-------:|---------|:-------:|:--------:|:-----------:|")
        for x in sorted(groups[t], key=lambda x: x["classroom"]["name"]):
            prof = f" ({x['exam'].get('teacher', '')})" if x['exam'].get('teacher') else ""
            study = x['exam']['study']
            pcs = int(x['exam'].get("computers", 0) or 0)
            lines.append(
                f"| {x['classroom']['name']} | {x['exam']['name']}{prof} | "
                f"{x['exam']['students']} | {study} | {_exam_range(x)} | "
                f"{_duration_label(x['exam'])} | {pcs if pcs else '—'} |"
            )
        lines.append("")

    studies = sorted({e["study"] for e in exams})
    lines.append("## Estudios")
    for s in studies:
        count = sum(1 for e in exams if e["study"] == s)
        students = sum(e["students"] for e in exams if e["study"] == s)
        lines.append(f"- **{s}**: {count} exámenes, {students} alumnos")
    lines.append("")
    lines.append("---")
    lines.append("*Generado con Generador de Calendario de Exámenes*")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def export_exams_to_md(exams, filepath):
    """Exporta la lista de exámenes a Markdown."""
    lines = []
    lines.append("# Lista de Exámenes")
    lines.append("")
    lines.append(f"Total: **{len(exams)}** exámenes")
    lines.append("")

    lines.append("| # | Nombre | Alumnos | Estudio | Profesor | Turno | Duración | Ordenadores |")
    lines.append("|--:|--------|:-------:|---------|:--------:|:-----:|:--------:|:-----------:|")
    shift_map = {"morning": "Mañana", "afternoon": "Tarde"}
    for i, e in enumerate(exams, 1):
        turno = shift_map.get(e.get("preferred_shift", ""), "")
        prof = e.get("teacher", "")
        pcs = int(e.get("computers", 0) or 0)
        lines.append(
            f"| {i} | {e['name']} | {e['students']} | {e['study']} | {prof} | "
            f"{turno} | {_duration_label(e)} | {pcs if pcs else '—'} |"
        )

    lines.append("")
    lines.append("## Resumen por estudio")
    studies = {}
    for e in exams:
        studies.setdefault(e["study"], []).append(e)
    for s, lst in sorted(studies.items()):
        total = sum(e["students"] for e in lst)
        lines.append(f"- **{s}**: {len(lst)} exámenes, {total} alumnos")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
