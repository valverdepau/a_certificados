"""
CAPA SERVICIOS · generador_pdf.py
Crea el certificado en PDF (A4 horizontal) con la librería fpdf2.
Todo se genera en memoria: no se escribe en el disco (Vercel no deja escribir).
"""
import io
import zipfile
from datetime import date

from fpdf import FPDF

AZUL = (20, 33, 61)      # #14213D
DORADO = (184, 146, 61)  # #B8923D

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


def _fecha_hoy():
    hoy = date.today()
    return f"{hoy.day} de {MESES[hoy.month - 1]} de {hoy.year}"


def crear_pdf(resultado):
    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.set_auto_page_break(False)
    pdf.add_page()

    # Marco
    pdf.set_draw_color(*AZUL)
    pdf.set_line_width(2.5)
    pdf.rect(10, 10, 277, 190)
    pdf.set_draw_color(*DORADO)
    pdf.set_line_width(0.8)
    pdf.rect(16, 16, 265, 178)

    pdf.set_text_color(*DORADO)
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_xy(16, 30)
    pdf.cell(265, 8, "ACADEMIA HORIZONTE", align="C")

    pdf.set_text_color(*AZUL)
    pdf.set_font("Helvetica", "B", 34)
    pdf.set_xy(16, 46)
    pdf.cell(265, 16, f"Certificado de {resultado['tipo']}", align="C")

    pdf.set_font("Helvetica", "", 14)
    pdf.set_text_color(60, 60, 60)
    pdf.set_xy(16, 76)
    pdf.cell(265, 8, "Se otorga a", align="C")

    pdf.set_font("Helvetica", "B", 28)
    pdf.set_text_color(*AZUL)
    pdf.set_xy(16, 88)
    pdf.cell(265, 14, resultado["nombre"], align="C")

    pdf.set_draw_color(*DORADO)
    pdf.set_line_width(0.6)
    pdf.line(70, 106, 227, 106)

    pdf.set_font("Helvetica", "", 14)
    pdf.set_text_color(60, 60, 60)
    pdf.set_xy(16, 114)
    accion = "por haber aprobado" if resultado["tipo"] == "Aprobación" else "por su participación en"
    pdf.cell(265, 8, f"{accion} el programa", align="C")

    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(*AZUL)
    pdf.set_xy(16, 125)
    pdf.cell(265, 10, f"{resultado['programa']} · Cohorte {resultado['cohorte']}", align="C")

    pdf.set_font("Helvetica", "", 12)
    pdf.set_text_color(60, 60, 60)
    pdf.set_xy(16, 142)
    pdf.cell(265, 8, f"Promedio: {resultado['promedio']:.2f}     ·     Asistencia: {resultado['asistencia']:.2f} %",
             align="C")

    pdf.set_font("Helvetica", "I", 11)
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
