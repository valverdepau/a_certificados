"""
Pruebas automáticas de la App de Certificados.

Se ejecutan desde la carpeta del proyecto con:  uv run pytest -v
No hace falta abrir la app: el cliente de pruebas de Flask simula el navegador.
"""
import io
import os
import re
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Variables de entorno de prueba.
# Se definen ANTES de crear la app para que las pruebas no dependan del archivo
# .env de la persona que las ejecuta.
# ---------------------------------------------------------------------------
os.environ["ADMIN_CORREO"] = "admin@prueba.test"
os.environ["ADMIN_CLAVE"] = "clave-admin-de-prueba"
os.environ["USUARIO_CORREO"] = "usuario@prueba.test"
os.environ["USUARIO_CLAVE"] = "clave-usuario-de-prueba"
os.environ["SECRET_KEY"] = "clave-secreta-solo-para-pruebas"
os.environ["DATABASE_URL"] = ""  # sin Supabase: las pruebas no tocan internet

from app import app  # noqa: E402  (se importa después de las variables)

CARPETA_INSUMOS = Path(__file__).resolve().parent.parent / "insumos"


def crear_cliente():
    """Crea un navegador de mentira para cada prueba (sesión independiente)."""
    app.config["TESTING"] = True
    return app.test_client()


def test_sin_sesion_redirige_a_login():
    """Simula a alguien que abre la página principal sin haber entrado:
    la app debe mandarlo a la pantalla de entrada."""
    cliente = crear_cliente()

    respuesta = cliente.get("/")

    assert respuesta.status_code == 302
    assert "/login" in respuesta.headers["Location"]


def test_clave_incorrecta_no_entra():
    """Simula a alguien que escribe un correo válido con una clave equivocada:
    debe quedarse en la pantalla de entrada y ver el mensaje de error."""
    cliente = crear_cliente()

    respuesta = cliente.post(
        "/login",
        data={"correo": os.environ["ADMIN_CORREO"], "clave": "clave-equivocada"},
    )

    assert respuesta.status_code == 200
    assert "Correo o contraseña incorrectos." in respuesta.get_data(as_text=True)
    # Tampoco debe quedar una sesión abierta.
    with cliente.session_transaction() as sesion:
        assert "correo" not in sesion


def test_usuario_no_puede_cargar():
    """Simula a una persona con rol "usuario" que escribe /cargar a mano:
    el servidor debe responder 403 (sin permiso), aunque el enlace no se vea."""
    cliente = crear_cliente()

    with cliente.session_transaction() as sesion:
        sesion["correo"] = os.environ["USUARIO_CORREO"]
        sesion["rol"] = "usuario"

    respuesta = cliente.get("/cargar")

    assert respuesta.status_code == 403
    assert "solo para administradores" in respuesta.get_data(as_text=True)


def test_excel_modificado_cambia_contadores():
    """Simula a un administrador que sube un registro con las notas de Camila
    Rojas Méndez (101230456) bajadas a 40. Al bajar sus notas, Camila pasa de
    Aprobación a Participación: los contadores deben quedar en 18 / 4 / 1.

    El Excel se arma en memoria a partir de insumos; el archivo original no se toca.
    """
    cliente = crear_cliente()

    with cliente.session_transaction() as sesion:
        sesion["correo"] = os.environ["ADMIN_CORREO"]
        sesion["rol"] = "admin"

    # 1) Leer el registro original y cambiar SOLO las notas de Camila.
    registro = pd.read_excel(
        CARPETA_INSUMOS / "Registro_Evaluaciones.xlsx",
        dtype={"Identificacion": str},
    )
    filas_de_camila = registro["Identificacion"].str.strip() == "101230456"
    assert filas_de_camila.any(), "Camila no aparece en el registro de evaluaciones"
    registro.loc[filas_de_camila, "Nota"] = 40

    # 2) Guardar ese registro modificado en memoria (no en el disco).
    registro_modificado = io.BytesIO()
    registro.to_excel(registro_modificado, index=False)
    registro_modificado.seek(0)

    # 3) El maestro se lee tal cual, también a memoria.
    maestro = io.BytesIO((CARPETA_INSUMOS / "Maestro_Estudiantes.xlsx").read_bytes())

    # 4) Subir los dos archivos como lo haría el navegador del administrador.
    respuesta = cliente.post(
        "/cargar",
        data={
            "accion": "ver",
            "maestro": (maestro, "Maestro_Estudiantes.xlsx"),
            "evaluaciones": (registro_modificado, "Registro_Evaluaciones.xlsx"),
        },
        content_type="multipart/form-data",
        follow_redirects=True,
    )

    assert respuesta.status_code == 200
    texto = respuesta.get_data(as_text=True)

    # Los tres contadores salen en el mismo orden de las tarjetas.
    numeros = re.findall(r'<div class="num">(\d+)</div>', texto)
    assert numeros == ["18", "4", "1"]

    # Y la pantalla debe decir que está mostrando archivos subidos.
    assert "Archivos subidos" in texto
