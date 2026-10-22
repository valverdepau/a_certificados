"""
CAPA SERVICIOS · autenticacion.py
Revisa el correo y la contraseña de las dos personas que pueden entrar.

- Todavía no hay base de datos de usuarios: los datos se leen de variables de
  entorno (archivo .env en su computador o Environment Variables en Vercel).
- Si las variables no existen, se usan usuarios de demostración y la pantalla
  de entrada muestra un aviso.
- Más adelante, cuando exista una tabla de usuarios, las claves deberían
  guardarse como "hash" (una huella) y no en texto legible.
"""
import os

# Usuarios de demostración: solo se usan cuando faltan las variables de entorno.
DEMO_ADMIN = {"correo": "admin@academia.demo", "clave": "admin123", "rol": "admin"}
DEMO_USUARIO = {"correo": "usuario@academia.demo", "clave": "usuario123", "rol": "usuario"}


def _leer(nombre):
    """Lee una variable de entorno y le quita los espacios de los extremos."""
    return (os.environ.get(nombre) or "").strip()


def usuarios_efectivos():
    """Devuelve los dos usuarios con los datos configurados.

    Si a un usuario le falta el correo o la clave en el entorno, se completa
    con su versión de demostración y se marca con "demo": True.
    """
    usuarios = []
    for rol, prefijo, demo in (
        ("admin", "ADMIN", DEMO_ADMIN),
        ("usuario", "USUARIO", DEMO_USUARIO),
    ):
        correo = _leer(f"{prefijo}_CORREO")
        clave = _leer(f"{prefijo}_CLAVE")
        es_demo = not correo or not clave  # si falta uno de los dos, se usa el de prueba
        usuarios.append({
            "correo": correo or demo["correo"],
            "clave": clave or demo["clave"],
            "rol": rol,
            "demo": es_demo,
        })
    return usuarios


def modo_demostracion():
    """True si al menos uno de los dos usuarios está usando los valores de prueba."""
    return any(u["demo"] for u in usuarios_efectivos())


def usuarios_demo():
    """Usuarios de prueba que se están usando (para mostrarlos en la pantalla de entrada)."""
    return [u for u in usuarios_efectivos() if u["demo"]]


def verificar(correo, clave):
    """Compara el correo y la clave con los usuarios configurados.

    Devuelve {"correo": ..., "rol": ...} si coinciden, o None si son incorrectos.
    """
    correo = (correo or "").strip().lower()
    clave = clave or ""
    for usuario in usuarios_efectivos():
        if usuario["correo"].strip().lower() == correo and usuario["clave"] == clave:
            return {"correo": usuario["correo"], "rol": usuario["rol"]}
    return None
