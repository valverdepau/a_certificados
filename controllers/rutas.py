"""
CAPA CONTROLADOR · rutas.py
Recibe los clics del usuario (peticiones), llama al modelo y a los servicios,
y entrega la vista. Aquí no se calcula nada.
"""
import io
import unicodedata
from functools import wraps

from flask import (Blueprint, abort, flash, redirect, render_template, request,
                   send_file, session, url_for)

from models import certificados, datos
from services import autenticacion, carga_excel, generador_pdf, resultados_excel

rutas = Blueprint("rutas", __name__)

# Vercel rechaza las peticiones de más de 4.5 MB; dejamos 4 MB por seguridad.
LIMITE_ARCHIVOS = 4 * 1024 * 1024


def _resultados(estudiantes=None, evaluaciones=None):
    """Calcula los resultados con las reglas del negocio.

    Si no se entregan datos, usa los de la base (los datos de fábrica que se
    cargaron desde insumos). Si se entregan, calcula con esos datos en memoria.
    """
    if estudiantes is None or evaluaciones is None:
        carga_excel.asegurar_datos()
        estudiantes = datos.leer_estudiantes()
        evaluaciones = datos.leer_evaluaciones()
    return certificados.calcular_resultados(estudiantes, evaluaciones)


def _render_tablero(resultados, contadores, inconsistencias, origen_datos,
                    datos_subidos, n_est, n_eva):
    """Entrega la vista del tablero con todos sus datos."""
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
        origen_datos=origen_datos,
        datos_subidos=datos_subidos,
    )


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


def _leer_subido(campo, etiqueta):
    """Lee un archivo del formulario y lo deja en memoria.

    BytesIO es como una caja de archivos dentro de la memoria del computador:
    se abre, se lee y se cierra igual que un archivo del disco, pero nunca se
    escribe en el disco. Es justo lo que necesita Vercel, donde el disco es de
    solo lectura.

    Devuelve (caja_en_memoria, nombre_del_archivo, mensaje_de_error).
    """
    archivo = request.files.get(campo)
    if archivo is None or not archivo.filename:
        return None, None, f"Falta el archivo: {etiqueta} (.xlsx)."

    # Solo el nombre, sin las carpetas que algunos navegadores agregan.
    nombre = archivo.filename.replace("\\", "/").split("/")[-1]
    contenido = archivo.read()  # todo el archivo pasa a la memoria (RAM)

    if not contenido:
        return None, None, f"El archivo {nombre} está vacío."
    if len(contenido) > LIMITE_ARCHIVOS:
        return None, None, f"El archivo {nombre} pesa más de 4 MB."
    if not contenido.startswith(b"PK"):  # los .xlsx son archivos ZIP: empiezan con "PK"
        return None, None, f"El archivo {nombre} no parece un Excel válido (.xlsx)."

    return io.BytesIO(contenido), nombre, None


def requiere_login(vista):
    """Decoradora: deja pasar solo si la persona ya entró con correo y contraseña.
    Si no hay sesión, la manda a la pantalla de entrada."""
    @wraps(vista)
    def envoltura(*args, **kwargs):
        if "correo" not in session:  # no hay sesión iniciada
            flash("Primero debe entrar con su correo y contraseña.", "error")
            return redirect(url_for("rutas.login"))
        return vista(*args, **kwargs)
    return envoltura


def solo_admin(vista):
    """Decoradora: deja pasar solo al rol "admin".
    A cualquier otro rol le responde un error 403 (sin permiso)."""
    @wraps(vista)
    def envoltura(*args, **kwargs):
        if session.get("rol") != "admin":
            abort(403)
        return vista(*args, **kwargs)
    return envoltura


@rutas.errorhandler(403)
def sin_permiso(_error):
    """Página amable cuando alguien intenta entrar a una sección de administración."""
    return render_template("sin_permiso.html"), 403


@rutas.app_errorhandler(413)
def archivo_demasiado_grande(_error):
    """Flask corta la petición cuando pasa de MAX_CONTENT_LENGTH (4 MB).
    Aquí se avisa con un mensaje entendible en vez de dejar la página en blanco."""
    flash("Los archivos juntos pesan más de 4 MB. Use archivos más pequeños.", "error")
    return redirect(url_for("rutas.tablero"))



@rutas.route("/login", methods=["GET", "POST"])
def login():
    """Pantalla de entrada: pide correo y contraseña."""
    if "correo" in session:  # si ya entró, no tiene sentido pedirle la clave otra vez
        return redirect(url_for("rutas.tablero"))

    error = None
    if request.method == "POST":
        usuario = autenticacion.verificar(request.form.get("correo"), request.form.get("clave"))
        if usuario is None:
            error = "Correo o contraseña incorrectos."
        else:
            session.clear()  # empieza una sesión limpia
            session["correo"] = usuario["correo"]
            session["rol"] = usuario["rol"]
            return redirect(url_for("rutas.tablero"))

    return render_template(
        "login.html",
        error=error,
        modo_demo=autenticacion.modo_demostracion(),
        usuarios_demo=autenticacion.usuarios_demo(),
    )


@rutas.route("/salir")
def salir():
    """Borra la sesión y devuelve a la pantalla de entrada."""
    session.clear()
    return redirect(url_for("rutas.login"))


@rutas.route("/")
@requiere_login
def tablero():
    try:
        resultados, contadores, inconsistencias = _resultados()
        n_est, n_eva = datos.contar_filas()
    except Exception as error:  # se muestra el error en pantalla, en lenguaje sencillo
        return render_template("error.html", error=error, motor=datos.nombre_motor()), 500
    return _render_tablero(
        resultados, contadores, inconsistencias,
        "Datos de fábrica (carpeta insumos)", False, n_est, n_eva,
    )


@rutas.route("/cargar", methods=["GET", "POST"])
@requiere_login
@solo_admin
def cargar():
    """Panel de administrador: recibe los dos Excel y calcula los resultados EN MEMORIA.
    No guarda nada en la base ni en el disco: al recargar la app vuelven los datos
    de fábrica, porque todavía no hay dónde guardar los archivos subidos."""
    if request.method == "GET":
        return redirect(url_for("rutas.tablero"))

    # 1) Revisar el tamaño total antes de leer nada (Vercel rechaza más de 4.5 MB).
    if request.content_length and request.content_length > LIMITE_ARCHIVOS:
        flash("Los archivos juntos pesan más de 4 MB. Use archivos más pequeños.", "error")
        return redirect(url_for("rutas.tablero"))

    # 2) Leer los dos archivos a memoria y revisar que sean Excel.
    caja_maestro, nombre_maestro, error = _leer_subido("maestro", "Maestro de estudiantes")
    if error:
        flash(error, "error")
        return redirect(url_for("rutas.tablero"))

    caja_evaluaciones, nombre_evaluaciones, error = _leer_subido("evaluaciones", "Registro de evaluaciones")
    if error:
        flash(error, "error")
        return redirect(url_for("rutas.tablero"))

    # 3) Leer los Excel con la misma función de siempre y aplicar las reglas del negocio.
    try:
        estudiantes, filas_evaluaciones = carga_excel.leer_datos(caja_maestro, caja_evaluaciones)
        resultados, contadores, inconsistencias = certificados.calcular_resultados(
            estudiantes, filas_evaluaciones
        )
    except ValueError as error:  # por ejemplo, si falta una columna (mensaje en español)
        flash(f"No se pudo leer: {error}", "error")
        return redirect(url_for("rutas.tablero"))
    except Exception:
        flash("Alguno de los archivos no es un Excel válido o está dañado.", "error")
        return redirect(url_for("rutas.tablero"))

    # 4) "Procesar y descargar Excel": se arma en memoria y se envía con send_file.
    if request.form.get("accion") == "excel":
        return send_file(
            resultados_excel.crear_excel(resultados),
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name="Resultados_Academia.xlsx",
        )

    # 5) "Procesar y ver en pantalla": se muestran solo en esta pantalla.
    origen = f"Archivos subidos: {nombre_maestro} y {nombre_evaluaciones}"
    return _render_tablero(resultados, contadores, inconsistencias, origen, True,
                           len(estudiantes), len(filas_evaluaciones))


@rutas.route("/resultados-excel")
@requiere_login
@solo_admin
def resultados_fabrica():
    """Descarga un Excel con los resultados de los datos de fábrica (carpeta insumos)."""
    resultados, _c, _i = _resultados()
    return send_file(
        resultados_excel.crear_excel(resultados),
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name="Resultados_Academia.xlsx",
    )


@rutas.route("/certificado/<identificacion>/<path:programa>")
@requiere_login
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
@requiere_login
def descargar_todos():
    resultados, _c, _i = _resultados()
    con_certificado = [r for r in resultados if certificados.lleva_certificado(r)]
    return send_file(generador_pdf.crear_zip(con_certificado), mimetype="application/zip",
                     as_attachment=True, download_name="Certificados_Academia.zip")
