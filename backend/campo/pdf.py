"""PDF del informe de servicio con la identidad de InControl (reportlab)."""
from io import BytesIO
from pathlib import Path

from django.core.files.base import ContentFile
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.fonts import addMapping
from reportlab.platypus import (
    Image, KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)
from xml.sax.saxutils import escape

from .services import nombre, resumen_personal

ASSETS = Path(__file__).parent / "assets"
LOGO = ASSETS / "IncontrolLogo.png"

NAVY = colors.HexColor("#39436B")
BLUE = colors.HexColor("#00639B")
TEXT = colors.HexColor("#2E3450")
MUTED = colors.HexColor("#6B7290")
LINE = colors.HexColor("#D9DEEA")
SOFT = colors.HexColor("#F2F4F9")

W, H = letter
M = 0.75 * inch
CW = W - 2 * M

_fuentes = False


def _registrar_fuentes():
    global _fuentes
    if _fuentes:
        return
    for nombre, archivo in [("M", "m400"), ("M-Semi", "m600"), ("M-Bold", "m700")]:
        pdfmetrics.registerFont(TTFont(nombre, str(ASSETS / "fonts" / f"{archivo}.ttf")))
    addMapping("M", 0, 0, "M")
    addMapping("M", 1, 0, "M-Bold")
    addMapping("M", 0, 1, "M")
    addMapping("M", 1, 1, "M-Bold")
    _fuentes = True


def _estilos():
    body = ParagraphStyle("body", fontName="M", fontSize=9.5, leading=14, textColor=TEXT)
    return {
        "body": body,
        "h2": ParagraphStyle("h2", fontName="M-Semi", fontSize=11.5, leading=16, textColor=NAVY,
                             spaceBefore=14, spaceAfter=6, keepWithNext=1),
        "label": ParagraphStyle("label", parent=body, fontName="M-Semi", fontSize=8, leading=11, textColor=MUTED),
        "cell": ParagraphStyle("cell", parent=body, fontSize=9, leading=12.5),
        "cellh": ParagraphStyle("cellh", parent=body, fontName="M-Semi", fontSize=9, leading=12.5,
                                textColor=colors.white),
        "cap": ParagraphStyle("cap", parent=body, fontSize=8, leading=11, textColor=MUTED),
    }


def _texto(valor, estilo):
    """Texto multilínea del usuario, escapado para el mini-HTML de reportlab."""
    return Paragraph(escape(valor or "—").replace("\n", "<br/>"), estilo)


def _hhmm(minutos):
    return f"{minutos // 60:02d}:{minutos % 60:02d}"


def _imagen(campo, ancho, alto_max):
    campo.open("rb")
    try:
        datos = BytesIO(campo.read())
    finally:
        campo.close()
    iw, ih = ImageReader(datos).getSize()
    escala = min(ancho / iw, alto_max / ih)
    datos.seek(0)
    return Image(datos, iw * escala, ih * escala)


def generar_pdf_informe(informe):
    """Devuelve el PDF del informe como ContentFile."""
    _registrar_fuentes()
    st = _estilos()
    buf = BytesIO()
    titulo = informe.consecutivo or "Borrador"

    def pagina(c, doc):
        c.saveState()
        logo = ImageReader(str(LOGO))
        lw, lh = logo.getSize()
        alto = 0.55 * inch
        c.drawImage(logo, M, H - 0.35 * inch - alto, alto * lw / lh, alto, mask="auto")
        c.setFont("M-Bold", 13)
        c.setFillColor(NAVY)
        c.drawRightString(W - M, H - 0.62 * inch, "INFORME DE SERVICIO")
        c.setFont("M-Semi", 10)
        c.setFillColor(BLUE)
        c.drawRightString(W - M, H - 0.82 * inch, titulo)
        c.setStrokeColor(BLUE)
        c.setLineWidth(2)
        c.line(M, H - 1.0 * inch, W - M, H - 1.0 * inch)
        c.setStrokeColor(LINE)
        c.setLineWidth(0.5)
        c.line(M, 0.6 * inch, W - M, 0.6 * inch)
        c.setFont("M", 7.5)
        c.setFillColor(MUTED)
        c.drawString(M, 0.42 * inch, f"InControl · {titulo} · Generado el {timezone.localtime():%d/%m/%Y %H:%M}")
        c.drawRightString(W - M, 0.42 * inch, f"Página {doc.page}")
        c.restoreState()

    doc = SimpleDocTemplate(buf, pagesize=letter, leftMargin=M, rightMargin=M, topMargin=1.25 * inch,
                            bottomMargin=0.85 * inch, title=f"Informe de servicio {titulo}", author="InControl")
    s = []

    # Datos generales
    proyecto = informe.proyecto
    datos = [
        ("Cliente", proyecto.cliente or "—"), ("Proyecto", proyecto.nombre),
        ("Fecha del servicio", f"{informe.fecha_servicio:%d/%m/%Y}"), ("Ubicación", informe.ubicacion or "—"),
        ("Elaborado por", nombre(informe.autor)),
        ("Aprobado por", nombre(informe.revisado_por) if informe.revisado_por_id else "—"),
    ]
    filas = []
    for i in range(0, len(datos), 2):
        fila = []
        for etiqueta, valor in datos[i:i + 2]:
            fila.append([Paragraph(etiqueta.upper(), st["label"]), _texto(valor, st["body"])])
        filas.append(fila)
    t = Table(filas, colWidths=[CW / 2] * 2)
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), SOFT), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                           ("LEFTPADDING", (0, 0), (-1, -1), 10), ("TOPPADDING", (0, 0), (-1, -1), 6),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 6), ("LINEBELOW", (0, 0), (-1, -2), 0.5, colors.white)]))
    s.append(t)

    # Personal
    horas = {f["usuario_id"]: f["minutos"] for f in resumen_personal(informe.proyecto_id, informe.fecha_servicio)}
    participantes = list(informe.participantes.all())
    if participantes:
        s.append(Paragraph("Personal", st["h2"]))
        data = [[Paragraph("Nombre", st["cellh"]), Paragraph("Horas registradas", st["cellh"])]]
        for p in sorted(participantes, key=nombre):
            data.append([Paragraph(escape(nombre(p)), st["cell"]),
                         Paragraph(_hhmm(horas[p.id]) if p.id in horas else "—", st["cell"])])
        t = Table(data, colWidths=[CW - 1.6 * inch, 1.6 * inch], repeatRows=1)
        estilo = [("BACKGROUND", (0, 0), (-1, 0), NAVY), ("LINEBELOW", (0, 1), (-1, -1), 0.5, LINE),
                  ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]
        t.setStyle(TableStyle(estilo))
        s.append(t)

    s.append(Paragraph("Actividades realizadas", st["h2"]))
    s.append(_texto(informe.actividades, st["body"]))
    if informe.observaciones.strip():
        s.append(Paragraph("Observaciones y recomendaciones", st["h2"]))
        s.append(_texto(informe.observaciones, st["body"]))

    # Registro fotográfico en 2 columnas
    fotos = list(informe.fotos.all())
    if fotos:
        s.append(Paragraph("Registro fotográfico", st["h2"]))
        ancho = (CW - 12) / 2
        celdas = []
        for f in fotos:
            celda = [_imagen(f.archivo, ancho, 2.6 * inch)]
            if f.descripcion:
                celda += [Spacer(1, 3), Paragraph(escape(f.descripcion), st["cap"])]
            celdas.append(celda)
        if len(celdas) % 2:
            celdas.append("")
        filas = [celdas[i:i + 2] for i in range(0, len(celdas), 2)]
        t = Table(filas, colWidths=[ancho + 6] * 2)
        t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                               ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                               ("BOTTOMPADDING", (0, 0), (-1, -1), 10)]))
        s.append(t)

    # Firma del cliente
    if informe.firma_imagen or informe.firma_nombre:
        bloque = [Paragraph("Recibido a satisfacción por el cliente", st["h2"])]
        if informe.firma_imagen:
            bloque.append(_imagen(informe.firma_imagen, 2.6 * inch, 1.0 * inch))
        linea = Table([[""]], colWidths=[2.8 * inch])
        linea.setStyle(TableStyle([("LINEABOVE", (0, 0), (-1, -1), 0.75, TEXT)]))
        linea.hAlign = "LEFT"
        bloque += [linea, _texto(informe.firma_nombre, st["body"])]
        if informe.firma_cargo:
            bloque.append(_texto(informe.firma_cargo, st["cap"]))
        for f in bloque:
            if isinstance(f, Image):
                f.hAlign = "LEFT"
        s.append(KeepTogether(bloque))

    doc.build(s, onFirstPage=pagina, onLaterPages=pagina)
    return ContentFile(buf.getvalue())
