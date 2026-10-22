"""
CAPA CONTROLADOR · rutas.py
Recibe los clics del usuario (peticiones), llama al modelo y a los servicios,
y entrega la vista. Aquí no se calcula nada.
"""
import io
import unicodedata

from flask import Blueprint, abort, flash, redirect, render_template, request, send_file, url_for

from models import certificados, datos
from services import carga_excel, generador_pdf

rutas = Blueprint("rutas", __name__)


def _resultados():
    carga_excel.asegurar_datos()
    return certificados.calcular_resultados(datos.leer_estudiantes(), datos.leer_evaluaciones())


def _slug(texto):
    """Convierte un texto en una dirección sencilla: sin tildes, sin espacios y en minúsculas.
    Así el enlace funciona igual en Vercel, donde los acentos se codifican distinto."""
    sin_tildes = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    limpio = "".join(c.lower() if c.isalnum() else "-" for c in sin_tildes)
    return "-".join(parte for parte in limpio.split("-") if parte)


def _reparar(texto):
    """Si el texto llegó mal codificado (UTF-8 leído como latin-1), lo devuelve bien."""
    try:
        return texto.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return texto



@rutas.route("/")
def tablero():
    try:
        resultados, contadores, inconsistencias = _resultados()
        n_est, n_eva = datos.contar_filas()
    except Exception as error:  # se muestra el error en pantalla, en lenguaje sencillo
        return render_template("error.html", error=error, motor=datos.nombre_motor()), 500
    return render_template(
        "tablero.html",
        resultados=resultados,
        contadores=contadores,
        inconsistencias=inconsistencias,
        motor=datos.nombre_motor(),
        supabase=datos.usa_supabase(),
        n_est=n_est,
        n_eva=n_eva,
        slug=_slug,
    )


@rutas.route("/cargar", methods=["GET", "POST"])
def cargar():
    if request.method == "POST":
        maestro = request.files.get("maestro")
        evaluaciones = request.files.get("evaluaciones")
        try:
            if maestro and maestro.filename and evaluaciones and evaluaciones.filename:
                n_est, n_eva = carga_excel.cargar_a_la_base(io.BytesIO(maestro.read()),
                                                            io.BytesIO(evaluaciones.read()))
                origen = "los archivos que subió"
            else:
                n_est, n_eva = carga_excel.cargar_a_la_base()
                origen = "la carpeta insumos"
            flash(f"Listo: se cargaron {n_est} estudiantes y {n_eva} evaluaciones desde {origen}.", "ok")
        except Exception as error:
            flash(f"No se pudo cargar: {error}", "error")
        return redirect(url_for("rutas.tablero"))
    return render_template("cargar.html", motor=datos.nombre_motor())


@rutas.route("/certificado/<identificacion>/<path:programa>")
def certificado(identificacion, programa):
    resultados, _c, _i = _resultados()
    buscado = _slug(_reparar(programa))
    for r in resultados:
        if r["identificacion"] == identificacion and (
            r["programa"] == programa or _slug(r["programa"]) == buscado
        ):
            if not certificados.lleva_certificado(r):
                abort(404)
            return send_file(io.BytesIO(generador_pdf.crear_pdf(r)), mimetype="application/pdf",
                             download_name=generador_pdf.nombre_archivo(r))
    abort(404)


@rutas.route("/descargar-todos")
def descargar_todos():
    resultados, _c, _i = _resultados()
    con_certificado = [r for r in resultados if certificados.lleva_certificado(r)]
    return send_file(generador_pdf.crear_zip(con_certificado), mimetype="application/zip",
                     as_attachment=True, download_name="Certificados_Academia.zip")
