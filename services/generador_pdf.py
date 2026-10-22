"""
CAPA SERVICIOS · generador_pdf.py
Crea el certificado en PDF (A4 horizontal) con la librería fpdf2.
Todo se genera en memoria: no se escribe en el disco (Vercel no deja escribir).
Paleta celeste y letra formal Crimson Text.
"""
import io
import zipfile
from datetime import date
from pathlib import Path

from fpdf import FPDF

# Paleta en tonos celestes
CELESTE = (126, 200, 227)          # #7EC8E3 marco exterior
CELESTE_MEDIO = (91, 168, 203)     # #5BA8CB detalles
CELESTE_PROFUNDO = (33, 110, 145)  # #216E91 títulos y textos destacados
CELESTE_SUAVE = (205, 234, 247)    # #CDEAF7 líneas suaves
FONDO = (247, 252, 254)            # #F7FCFE fondo de la hoja
GRIS_AZUL = (74, 107, 124)         # #4A6B7C texto de párrafo

CARPETA_FUENTES = Path(__file__).resolve().parent.parent / "assets" / "fuentes"

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


def _fecha_hoy():
    hoy = date.today()
    return f"{hoy.day} de {MESES[hoy.month - 1]} de {hoy.year}"


def _registrar_fuente(pdf):
    """Usa Crimson Text (letra formal) si los archivos están; si no, Helvetica."""
    regular = CARPETA_FUENTES / "CrimsonText-Regular.ttf"
    negrita = CARPETA_FUENTES / "CrimsonText-Bold.ttf"
    cursiva = CARPETA_FUENTES / "CrimsonText-Italic.ttf"
    if not (regular.exists() and negrita.exists() and cursiva.exists()):
        return "Helvetica"
    pdf.add_font("Crimson", "", regular)
    pdf.add_font("Crimson", "B", negrita)
    pdf.add_font("Crimson", "I", cursiva)
    return "Crimson"


def _rombo(pdf, x, y, tamano, color):
    """Adorno pequeño en forma de rombo."""
    pdf.set_fill_color(*color)
    pdf.polygon([(x, y - tamano), (x + tamano, y), (x, y + tamano), (x - tamano, y)], style="F")


def crear_pdf(resultado):
    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.set_auto_page_break(False)
    pdf.add_page()
    fuente = _registrar_fuente(pdf)

    # Fondo celeste muy suave
    pdf.set_fill_color(*FONDO)
    pdf.rect(0, 0, 297, 210, style="F")

    # Marco exterior celeste y marco interior fino
    pdf.set_draw_color(*CELESTE)
    pdf.set_line_width(3)
    pdf.rect(9, 9, 279, 192)
    pdf.set_draw_color(*CELESTE_PROFUNDO)
    pdf.set_line_width(0.4)
    pdf.rect(15, 15, 267, 180)

    # Rombos en las esquinas del marco interior
    for x, y in ((15, 15), (282, 15), (15, 195), (282, 195)):
        _rombo(pdf, x, y, 2.6, CELESTE_MEDIO)

    # Nombre de la academia
    pdf.set_text_color(*CELESTE_PROFUNDO)
    pdf.set_font(fuente, "B", 13)
    pdf.set_xy(16, 28)
    pdf.cell(265, 8, "ACADEMIA HORIZONTE", align="C")

    # Línea decorativa con rombo central
    pdf.set_draw_color(*CELESTE_MEDIO)
    pdf.set_line_width(0.5)
    pdf.line(108, 40, 144, 40)
    pdf.line(153, 40, 189, 40)
    _rombo(pdf, 148.5, 40, 2, CELESTE_MEDIO)

    # Título
    pdf.set_text_color(*CELESTE_PROFUNDO)
    pdf.set_font(fuente, "B", 34)
    pdf.set_xy(16, 46)
    pdf.cell(265, 16, f"Certificado de {resultado['tipo']}", align="C")

    pdf.set_font(fuente, "", 14)
    pdf.set_text_color(*GRIS_AZUL)
    pdf.set_xy(16, 76)
    pdf.cell(265, 8, "Se otorga a", align="C")

    # Nombre del estudiante
    pdf.set_font(fuente, "B", 28)
    pdf.set_text_color(*CELESTE_PROFUNDO)
    pdf.set_xy(16, 88)
    pdf.cell(265, 14, resultado["nombre"], align="C")

    # Línea bajo el nombre
    pdf.set_draw_color(*CELESTE_MEDIO)
    pdf.set_line_width(0.6)
    pdf.line(70, 106, 227, 106)
    _rombo(pdf, 148.5, 106, 1.8, CELESTE_MEDIO)

    pdf.set_font(fuente, "", 14)
    pdf.set_text_color(*GRIS_AZUL)
    pdf.set_xy(16, 114)
    accion = "por haber aprobado" if resultado["tipo"] == "Aprobación" else "por su participación en"
    pdf.cell(265, 8, f"{accion} el programa", align="C")

    pdf.set_font(fuente, "B", 18)
    pdf.set_text_color(*CELESTE_PROFUNDO)
    pdf.set_xy(16, 125)
    pdf.cell(265, 10, f"{resultado['programa']} · Cohorte {resultado['cohorte']}", align="C")

    pdf.set_font(fuente, "", 12)
    pdf.set_text_color(*GRIS_AZUL)
    pdf.set_xy(16, 142)
    pdf.cell(265, 8, f"Promedio: {resultado['promedio']:.2f}     ·     Asistencia: {resultado['asistencia']:.2f} %",
             align="C")

    # Pie
    pdf.set_draw_color(*CELESTE_SUAVE)
    pdf.set_line_width(0.4)
    pdf.line(108, 165, 189, 165)

    pdf.set_font(fuente, "I", 11)
    pdf.set_text_color(*GRIS_AZUL)
    pdf.set_xy(16, 172)
    pdf.cell(265, 6, f"Emitido el {_fecha_hoy()} · Identificación {resultado['identificacion']}", align="C")

    return bytes(pdf.output())


def nombre_archivo(resultado):
    limpio = "".join(c if c.isalnum() else "_" for c in resultado["nombre"])
    return f"Certificado_{limpio}_{resultado['identificacion']}.pdf"


def crear_zip(resultados):
    memoria = io.BytesIO()
    with zipfile.ZipFile(memoria, "w", zipfile.ZIP_DEFLATED) as z:
        for r in resultados:
            z.writestr(nombre_archivo(r), crear_pdf(r))
    memoria.seek(0)
    return memoria
