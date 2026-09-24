import io

import openpyxl
from openpyxl.styles import Font
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import CIDFont, UnicodeCIDFont
from reportlab.pdfbase._cidfontdata import widthsByUnichar
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

# Fuentes CID de reportlab: vienen incluidas (no requieren archivos .ttf ni
# internet), cubren chino tradicional/simplificado con la codificación
# estándar de Adobe. Sin esto, el PDF no puede dibujar caracteres CJK.
_CID_FONTS = {
    "zh-hk": "MSung-Light",   # chino tradicional (CNS1) — Hong Kong
    "zh": "STSong-Light",     # chino simplificado (GB1) — China continental
}
_registered = set()


def _register_cid_font(cid_name):
    """Registra una fuente CID de reportlab, corrigiendo un bug real de la
    librería: su tabla `defaultUnicodeEncodings` mapea 'MSung-Light' (chino
    TRADICIONAL, familia de glifos CNS1) a la codificación 'UniGB-UCS2-H',
    que es para chino SIMPLIFICADO (GB1). Usar `UnicodeCIDFont('MSung-Light')`
    tal cual produce caracteres incorrectos (glifos desplazados) en el PDF.
    Verificado manualmente: con la codificación correcta 'UniCNS-UCS2-H' el
    texto sale bien; con la que trae reportlab por defecto, no.
    """
    if cid_name == "MSung-Light":
        font = UnicodeCIDFont.__new__(UnicodeCIDFont)
        CIDFont.__init__(font, cid_name, "UniCNS-UCS2-H")
        font.language = "cht"
        font.name = font.fontName = cid_name
        font.vertical = False
        font.isHalfWidth = False
        font.unicodeWidths = widthsByUnichar[cid_name]
        pdfmetrics.registerFont(font)
    else:
        pdfmetrics.registerFont(UnicodeCIDFont(cid_name))


def _font_for_lang(lang):
    cid_name = _CID_FONTS.get(lang)
    if cid_name is None:
        return "Helvetica", "Helvetica-Bold"
    if cid_name not in _registered:
        _register_cid_font(cid_name)
        _registered.add(cid_name)
    return cid_name, cid_name  # las CID fonts de reportlab no traen variante bold propia


COLUMNS = [
    ("country", "pais"),
    ("period", "periodo"),
    ("employee_name", "nombre"),
    ("total_devengado", "total_devengado"),
    ("neto_pagado", "neto_pagado"),
    ("total_aportes_patronales", "total_aportes_patronales"),
    ("total_provisiones", "total_provisiones"),
]


def _row_values(n):
    nombre = n["empleado"]["nombre"]
    if n["empleado"].get("es_demo"):
        nombre = f"{nombre} (DEMO)"
    return [
        n["pais"],
        n["periodo"],
        nombre,
        round(n["resultado"]["total_devengado"], 2),
        round(n["resultado"]["neto_pagado"], 2),
        round(n["resultado"]["total_aportes_patronales"], 2),
        round(n["resultado"]["total_provisiones"], 2),
    ]


def build_excel(nominas, translate, title):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = title[:31] if title else "Nomina"

    headers = [translate(key) for key, _ in COLUMNS]
    ws.append(headers)
    for cell in ws[1]:
        cell.font = Font(bold=True)

    for n in nominas:
        ws.append(_row_values(n))

    for col in ws.columns:
        width = max(len(str(c.value)) if c.value is not None else 0 for c in col) + 2
        ws.column_dimensions[col[0].column_letter].width = max(width, 12)

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf


def build_pdf(nominas, translate, title, lang):
    buf = io.BytesIO()
    font_name, font_bold = _font_for_lang(lang)
    styles = getSampleStyleSheet()
    title_style = styles["Title"]
    title_style.fontName = font_bold

    doc = SimpleDocTemplate(buf, pagesize=landscape(letter))
    elements = [Paragraph(title, title_style), Spacer(1, 12)]

    headers = [translate(key) for key, _ in COLUMNS]
    data = [headers] + [[str(v) for v in _row_values(n)] for n in nominas]

    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), font_name),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#94a3b8")),
        ("ALIGN", (3, 1), (-1, -1), "RIGHT"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f1f5f9")]),
    ]))
    elements.append(table)
    doc.build(elements)
    buf.seek(0)
    return buf
