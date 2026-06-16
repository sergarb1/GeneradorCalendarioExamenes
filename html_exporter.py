# -*- coding: utf-8 -*-
# Copyright (C) 2026 Sergi Albuixech
# SPDX-License-Identifier: AGPL-3.0-or-later
"""
HTML EXPORTER - Generador de informes HTML con estilo

Este modulo genera un archivo HTML con el calendario de examenes
ya resuelto. El HTML esta disenado para verse bien en pantalla,
imprimirse como PDF, y tener un diseno profesional.

Colores: azul (#6366f1) principal, dorado (#f59e0b) acento.
"""

import re
from datetime import datetime
from html import escape

# Colores principales
GVA_BLUE = "#6366f1"   # Azul indigo - cabeceras, botones, titulos
GVA_GOLD = "#f59e0b"   # Dorado/ambar - color de acento

# Colores para cada estudio (color_texto, color_fondo)
# Si hay mas estudios que colores, se cicla (vuelve al primero)
STUDY_COLORS = [
    (GVA_BLUE, "#e0e7ff"),
    ("#ef4444", "#fee2e2"),
    ("#10b981", "#d1fae5"),
    ("#8b5cf6", "#ede9fe"),
    (GVA_GOLD, "#fef3c7"),
    ("#06b6d4", "#cffafe"),
    ("#ec4899", "#fce7f3"),
    ("#3b82f6", "#dbeafe"),
    ("#f97316", "#ffedd5"),
    ("#14b8a6", "#ccfbf1"),
]


def _color_for_study(study, studies):
    """
    Asigna un color a cada estudio de forma ciclica.
    
    Busca la posicion del estudio en la lista ordenada y devuelve
    el par (color_texto, color_fondo) correspondiente.
    Si hay mas estudios que colores, se repiten desde el principio.
    """
    idx = studies.index(study) % len(STUDY_COLORS)
    return STUDY_COLORS[idx]


def _fmt_global_slot(global_slots, t):
    """
    Formatea una franja global como texto legible.
    
    Convierte (date, start, end) en algo como "15/06/2026 09:00 - 11:00"
    para mostrar en el HTML.
    """
    if t < len(global_slots):
        date_str, start, end = global_slots[t]
        try:
            d = datetime.strptime(date_str, "%Y-%m-%d")
            date_fmt = d.strftime("%d/%m/%Y")
        except ValueError:
            date_fmt = date_str
        return f"{date_fmt} {start} - {end}"
    return f"Franja {t+1}"


def generate_html(project_name, global_slots, exams, classrooms, assignment, num_slots):
    """
    Genera el codigo HTML completo del calendario de examenes.
    
    Construye todo el HTML desde cero con:
      - CSS embebido (colores azul/dorado, sombras, bordes redondeados)
      - Tabla con franjas como filas y aulas como columnas
      - Bloques de colores para cada examen (segun su estudio)
      - Leyenda de colores
      - Boton de imprimir
      - Estilos de impresion (@media print)
    
    Parametros:
        project_name:  nombre del proyecto
        global_slots:  lista de franjas unicas (date, start, end)
        exams:         lista de examenes
        classrooms:    lista de aulas
        assignment:    asignacion del solver CP-SAT
        num_slots:     numero total de franjas globales
    
    Devuelve:
        String con el HTML completo.
    """
    
    # --- Preparacion de datos ---
    
    # Lista ordenada de estudios para asignar colores
    studies = sorted({e["study"] for e in exams})
    
    # Asignamos un color a cada estudio
    colors = {s: _color_for_study(s, studies) for s in studies}
    # Colores personalizados por examen (si tienen campo "color")
    exam_colors = {e["name"]: e.get("color") for e in exams if e.get("color")}
    
    # Organizamos las asignaciones por franja y por aula
    # slot_assignments[franja_idx][nombre_aula] = [asignacion1, ...]
    slot_assignments = {t: {} for t in range(num_slots)}
    for a in assignment:
        t = a["slot"]
        c_name = a["classroom"]["name"]
        if c_name not in slot_assignments[t]:
            slot_assignments[t][c_name] = []
        slot_assignments[t][c_name].append(a)
    
    # Nombres de aulas (orden original, sin duplicados)
    classroom_names = list(dict.fromkeys(c["name"] for c in classrooms))
    
    # Franjas que se usan realmente (ordenadas)
    used_slots = sorted({a["slot"] for a in assignment})
    
    # Titulo del documento
    title = project_name.strip() or "Calendari d'Examens"
    
    # Fecha/hora de generacion
    now_str = datetime.now().strftime('%d/%m/%Y a les %H:%M')
    
    # --- Construccion del HTML ---
    # NOTA: usamos dobles llaves {{ }} en las f-strings porque
    # las llaves simples {} se interpretan como expresiones Python.
    # En el CSS necesitamos llaves literales, asi que las duplicamos.

    filename_base = re.sub(r'[^a-zA-Z0-9_\-]', '_', title)
    
    html = f"""<!DOCTYPE html>
<html lang="ca">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
{_word_download_js(filename_base)}

<style>
  /* --- Configuracion de pagina para impresion --- */
  @page {{ size: landscape; margin: 1.2cm; }}
  
  /* --- Reset de margenes y paddings --- */
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  
  /* --- Cuerpo del documento --- */
  body {{
    font-family: 'Segoe UI', -apple-system, Helvetica, Arial, sans-serif;
    color: #1e293b;
    background: #f8fafc;
    padding: 20px;
  }}
  
  /* --- Titulo principal --- */
  h1 {{ font-size: 22px; font-weight: 700; color: {GVA_BLUE}; margin-bottom: 2px; }}
  
  /* --- Subtitulo --- */
  .subtitle {{ font-size: 13px; color: #64748b; margin-bottom: 20px; }}
  
  /* --- Tabla principal --- */
  table {{
    border-collapse: collapse; width: 100%;
    box-shadow: 0 1px 3px rgba(0,0,0,.08);
    border-radius: 8px; overflow: hidden;
    margin-bottom: 6px;
  }}
  
  /* --- Celdas --- */
  th, td {{
    border: 1px solid #e2e8f0;
    padding: 8px 10px; text-align: center; vertical-align: top;
    font-size: 12px;
  }}
  
  /* --- Cabeceras de columna --- */
  th {{
    background: {GVA_BLUE}; color: #fff; font-weight: 600;
    font-size: 12px; padding: 10px 8px;
  }}
  th:first-child {{ width: 140px; }}
  
  /* --- Primera columna (franjas) --- */
  td:first-child {{
    font-weight: 600; background: #f1f5f9; color: #0f172a;
    white-space: nowrap; font-size: 11px;
  }}
  
  /* --- Bloque de examen --- */
  .exam-block {{
    display: inline-block; margin: 3px 2px; padding: 6px 10px;
    border-radius: 6px; font-size: 11px; line-height: 1.4;
    min-width: 100px; text-align: left;
  }}
  .exam-name {{ font-weight: 600; display: block; }}
  .exam-meta {{ opacity: 0.8; font-size: 10px; display: block; }}
  
  /* --- Celda vacia --- */
  .empty-cell {{ color: #94a3b8; font-style: italic; font-size: 11px; }}
  
  /* --- Pie de pagina --- */
  .footer {{ margin-top: 14px; font-size: 11px; color: #94a3b8; text-align: center; }}
  
  /* --- Leyenda de colores --- */
  .legend {{ display: flex; flex-wrap: wrap; gap: 10px; margin: 14px 0; justify-content: center; }}
  .legend-item {{ display: flex; align-items: center; gap: 5px; font-size: 12px; }}
  .legend-swatch {{ width: 14px; height: 14px; border-radius: 3px; border: 1px solid #cbd5e1; }}
  
  /* --- Estilos de impresion --- */
  @media print {{
    body {{ background: #fff; padding: 0; }}
    .no-print {{ display: none !important; }}
    th {{
      background: {GVA_BLUE} !important; color: #fff !important;
      -webkit-print-color-adjust: exact; print-color-adjust: exact;
    }}
    .exam-block {{
      -webkit-print-color-adjust: exact; print-color-adjust: exact;
    }}
    td:first-child {{
      background: #f1f5f9 !important;
      -webkit-print-color-adjust: exact; print-color-adjust: exact;
    }}
  }}
  
  /* --- Boton de impresion --- */
  .btn-print {{
    display: inline-block; padding: 10px 24px; background: {GVA_BLUE};
    color: #fff; border: none; border-radius: 6px; font-size: 14px;
    cursor: pointer; margin-bottom: 14px;
  }}
  .btn-print:hover {{ background: #4f46e5; }}
</style>
</head>
<body>

<!-- Botones de accion (se ocultan al imprimir) -->
<div class="no-print" style="text-align:right;">
  <button class="btn-print" onclick="window.print()">🖨️ Imprimir / PDF</button>
  <button class="btn-print" onclick="descargarWord()" style="background:#2b579a;">📄 Word</button>
</div>

<!-- Titulo -->
<h1>📅🎓 {title}</h1>

<!-- Subtitulo con estadisticas -->
<p class="subtitle">
  Generat el {now_str} &middot;
  {len(exams)} examens &middot; {len(used_slots)} franjes &middot; {len(classrooms)} aules
</p>

<!-- Leyenda de colores por estudio -->
<div class="legend">
"""

    for s in studies:
        fg, bg = colors[s]
        html += f"""  <div class="legend-item"><span class="legend-swatch" style="background:{bg};border-color:{fg};"></span>{s}</div>\n"""

    # --- Tabla principal: filas = franjas, columnas = aulas ---
    html += """</div>
<table>
<thead>
<tr>
  <th>Franja</th>
"""
    for cn in classroom_names:
        cap = next((c["capacity"] for c in classrooms if c["name"] == cn), 0)
        html += f"  <th>{cn}<br><span style=\"font-weight:400;font-size:10px;\">cap. {cap}</span></th>\n"
    html += "</tr>\n</thead>\n<tbody>\n"

    # --- Filas de la tabla ---
    for t in used_slots:
        label = _fmt_global_slot(global_slots, t)
        html += f"<tr>\n  <td>{label}</td>\n"
        for cn in classroom_names:
            exams_at = slot_assignments[t].get(cn, [])
            if exams_at:
                cell = '<div style="display:flex;flex-wrap:wrap;gap:4px;justify-content:center;">'
                for a in exams_at:
                    custom = exam_colors.get(a["exam"]["name"])
                    if custom:
                        fg = custom
                        r, g, b = int(custom[1:3], 16), int(custom[3:5], 16), int(custom[5:7], 16)
                        bg = f"rgba({r},{g},{b},0.12)"
                    else:
                        fg, bg = colors[a["exam"]["study"]]
                    cell += (
                        f'<div class="exam-block" style="background:{bg};border-left:3px solid {fg};">'
                        f'<span class="exam-name">{a["exam"]["name"]}</span>'
                        f'<span class="exam-meta">{a["exam"]["study"]} · {a["exam"]["students"]} alumnes</span>'
                        f"</div>"
                    )
                cell += "</div>"
                html += f"  <td>{cell}</td>\n"
            else:
                html += '  <td><span class="empty-cell">—</span></td>\n'
        html += "</tr>\n"

    # --- Cierre del HTML ---
    html += """</tbody>
</table>
<div class="footer">🎓 Generador de Calendario de Examenes &middot; IES Serra Perenxisa &middot; Optimitzacio CP-SAT ⚡</div>
</body>
</html>"""
    
    return html


def _word_download_js(filename_base):
    """JavaScript para descargar el HTML como documento Word."""
    return f"""
<script>
function descargarWord() {{
    var contenido = document.documentElement.outerHTML;
    var blob = new Blob([contenido], {{type:'application/msword'}});
    var enlace = document.createElement('a');
    enlace.href = URL.createObjectURL(blob);
    enlace.download = '{escape(filename_base)}.doc';
    document.body.appendChild(enlace);
    enlace.click();
    document.body.removeChild(enlace);
    URL.revokeObjectURL(enlace.href);
}}
</script>"""


def generate_html_cuadrante(project_name, global_slots, exams, classrooms, assignment, num_slots):
    """
    Genera HTML estilo cuadrante formal para colgar en un tablon.
    Disenado para verse bien impreso en A3/A4/apaisado.
    """
    studies = sorted({e["study"] for e in exams})
    colors = {s: _color_for_study(s, studies) for s in studies}
    exam_colors = {e["name"]: e.get("color") for e in exams if e.get("color")}

    slot_assignments = {t: {} for t in range(num_slots)}
    for a in assignment:
        t = a["slot"]
        c_name = a["classroom"]["name"]
        if c_name not in slot_assignments[t]:
            slot_assignments[t][c_name] = []
        slot_assignments[t][c_name].append(a)

    classroom_names = list(dict.fromkeys(c["name"] for c in classrooms))
    used_slots = sorted({a["slot"] for a in assignment})
    title = project_name.strip() or "Calendari d'Examens"
    now_str = datetime.now().strftime('%d/%m/%Y a les %H:%M')

    filename_base = re.sub(r'[^a-zA-Z0-9_\-]', '_', title) if 're' in dir() else title.replace(' ', '_')

    html = f"""<!DOCTYPE html>
<html lang="ca">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} - Cuadrante</title>
{_word_download_js(filename_base)}
<style>
  @page {{ size: landscape; margin: 0.8cm; }}

  * {{ margin: 0; padding: 0; box-sizing: border-box; }}

  body {{
    font-family: 'Segoe UI', Arial, Helvetica, sans-serif;
    color: #1e293b;
    background: #fff;
    padding: 12px;
  }}

  .toolbar {{
    text-align: right; margin-bottom: 10px;
  }}
  .toolbar button {{
    padding: 8px 18px; margin-left: 6px; border: none; border-radius: 4px;
    font-size: 13px; font-weight: 600; cursor: pointer;
  }}
  .btn-print {{
    background: {GVA_BLUE}; color: #fff;
  }}
  .btn-word {{
    background: #2b579a; color: #fff;
  }}

  h1 {{
    font-size: 26px; font-weight: 800; color: #0f172a;
    text-align: center; margin-bottom: 2px; letter-spacing: 1px;
  }}

  .subtitle {{
    text-align: center; font-size: 13px; color: #475569;
    margin-bottom: 16px;
  }}

  table {{
    border-collapse: collapse; width: 100%;
    border: 2px solid #1e293b;
  }}

  th, td {{
    border: 1.5px solid #334155;
    padding: 10px 8px; text-align: center; vertical-align: middle;
  }}

  th {{
    background: #1e293b; color: #fff; font-weight: 700;
    font-size: 13px; text-transform: uppercase; letter-spacing: 0.5px;
  }}
  th:first-child {{ width: 160px; }}

  td:first-child {{
    font-weight: 700; background: #f1f5f9; color: #0f172a;
    font-size: 12px; white-space: nowrap;
  }}

  .exam-cell {{
    padding: 6px 4px; border-radius: 0;
    font-size: 13px; line-height: 1.3;
    min-height: 48px;
    display: flex; flex-direction: column; justify-content: center;
  }}
  .exam-name {{
    font-weight: 700; font-size: 14px; display: block;
  }}
  .exam-meta {{
    font-size: 11px; opacity: 0.85; display: block;
  }}
  .exam-teacher {{
    font-size: 10px; opacity: 0.7; display: block;
  }}

  .empty-cell {{
    color: #94a3b8; font-style: italic; font-size: 13px;
  }}

  .legend {{
    display: flex; flex-wrap: wrap; gap: 12px;
    margin: 14px 0; justify-content: center;
  }}
  .legend-item {{
    display: flex; align-items: center; gap: 6px;
    font-size: 12px; font-weight: 600;
  }}
  .legend-swatch {{
    width: 18px; height: 18px; border-radius: 2px;
    border: 1.5px solid #334155;
  }}

  .footer {{
    margin-top: 12px; font-size: 10px; color: #64748b;
    text-align: center;
  }}

  @media print {{
    body {{ padding: 0; }}
    .toolbar {{ display: none !important; }}
    th {{ background: #1e293b !important; color: #fff !important; }}
    td:first-child {{ background: #f1f5f9 !important; }}
    .exam-cell, .legend-swatch {{
      -webkit-print-color-adjust: exact; print-color-adjust: exact;
    }}
  }}
</style>
</head>
<body>

<div class="toolbar no-print">
  <button class="btn-print" onclick="window.print()">🖨️ Imprimir / PDF</button>
  <button class="btn-word" onclick="descargarWord()">📄 Word</button>
</div>

<h1>{title}</h1>
<p class="subtitle">
  {len(exams)} examens · {len(used_slots)} franjes · {len(classrooms)} aules
  &nbsp;|&nbsp; Generat el {now_str}
</p>

<!-- Leyenda -->
<div class="legend">
"""
    for s in studies:
        fg, bg = colors[s]
        html += f"""  <div class="legend-item"><span class="legend-swatch" style="background:{bg};border-color:{fg};"></span>{s}</div>\n"""

    # Tabla principal
    html += """</div>
<table>
<thead>
<tr>
  <th>Franja</th>
"""
    for cn in classroom_names:
        cap = next((c["capacity"] for c in classrooms if c["name"] == cn), 0)
        html += f"  <th>{cn}<br><span style=\"font-weight:400;font-size:10px;color:#cbd5e1;\">cap. {cap}</span></th>\n"
    html += "</tr>\n</thead>\n<tbody>\n"

    for t in used_slots:
        label = _fmt_global_slot(global_slots, t)
        html += f"<tr>\n  <td>{label}</td>\n"
        for cn in classroom_names:
            exams_at = slot_assignments[t].get(cn, [])
            if exams_at:
                cell = '<td>\n'
                for a in exams_at:
                    custom = exam_colors.get(a["exam"]["name"])
                    if custom:
                        fg = custom
                        r, g, b = int(custom[1:3], 16), int(custom[3:5], 16), int(custom[5:7], 16)
                        bg = f"rgba({r},{g},{b},0.15)"
                    else:
                        fg, bg = colors[a["exam"]["study"]]
                    cell += f"""  <div class="exam-cell" style="background:{bg};border-left:4px solid {fg};">
    <span class="exam-name" style="color:{fg};">{escape(a["exam"]["name"])}</span>
    <span class="exam-meta">{escape(a["exam"]["study"])} · {a["exam"]["students"]} alumnes</span>"""
                    if a["exam"].get("teacher"):
                        cell += f'\n    <span class="exam-teacher">{escape(a["exam"]["teacher"])}</span>'
                    cell += "\n  </div>\n"
                cell += '</td>\n'
                html += cell
            else:
                html += '  <td><span class="empty-cell">—</span></td>\n'
        html += "</tr>\n"

    html += """</tbody>
</table>
<div class="footer">🎓 Generador de Calendario de Examenes · IES Serra Perenxisa</div>
</body>
</html>"""
    return html


def export_html_cuadrante_file(project_name, global_slots, exams, classrooms, assignment, num_slots, filepath):
    """Genera el HTML cuadrante y lo guarda en un archivo."""
    html = generate_html_cuadrante(project_name, global_slots, exams, classrooms, assignment, num_slots)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    return filepath


def export_html_file(project_name, global_slots, exams, classrooms, assignment, num_slots, filepath):
    """
    Genera el HTML y lo guarda en un archivo.
    
    Esta funcion es la que usa gui.py directamente.
    Crea el HTML llamando a generate_html() y lo escribe en la ruta
    especificada con codificacion UTF-8.
    
    Devuelve la ruta del archivo generado.
    """
    html = generate_html(project_name, global_slots, exams, classrooms, assignment, num_slots)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    return filepath
