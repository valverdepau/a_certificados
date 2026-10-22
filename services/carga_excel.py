"""
CAPA SERVICIOS · carga_excel.py
Lee los dos Excel (desde la carpeta insumos o desde un archivo subido) y los guarda en la base.
"""
from pathlib import Path

import pandas as pd

from models import datos

CARPETA_PROYECTO = Path(__file__).resolve().parent.parent

COLUMNAS_ESTUDIANTES = ["Identificacion", "Nombre_Completo", "Correo", "Programa", "Cohorte"]
COLUMNAS_EVALUACIONES = ["Identificacion", "Programa", "Modulo", "Nota", "Asistencia_Pct", "Fecha_Cierre"]


def carpeta_insumos():
    """Busca la carpeta insumos sin importar mayúsculas (insumos, Insumos, INSUMOS)."""
    for hijo in CARPETA_PROYECTO.iterdir():
        if hijo.is_dir() and hijo.name.lower() == "insumos":
            return hijo
    return CARPETA_PROYECTO / "insumos"


def _buscar(nombre):
    carpeta = carpeta_insumos()
    for archivo in carpeta.iterdir():
        if archivo.name.lower() == nombre.lower():
            return archivo
    raise FileNotFoundError(f"No encontré {nombre} en la carpeta {carpeta.name}")


def _leer(origen, columnas, nombre):
    tabla = pd.read_excel(origen, dtype={"Identificacion": str})
    faltan = [c for c in columnas if c not in tabla.columns]
    if faltan:
        raise ValueError(f"Al archivo {nombre} le faltan las columnas: {', '.join(faltan)}")
    tabla = tabla[columnas].copy()
    tabla["Identificacion"] = tabla["Identificacion"].astype(str).str.strip()
    return tabla


def leer_excel(origen_maestro=None, origen_evaluaciones=None):
    """Si no se entregan archivos, usa los de la carpeta insumos."""
    maestro = _leer(origen_maestro or _buscar("Maestro_Estudiantes.xlsx"),
                    COLUMNAS_ESTUDIANTES, "Maestro_Estudiantes")
    evaluaciones = _leer(origen_evaluaciones or _buscar("Registro_Evaluaciones.xlsx"),
                         COLUMNAS_EVALUACIONES, "Registro_Evaluaciones")
    return maestro, evaluaciones


def leer_datos(origen_maestro=None, origen_evaluaciones=None):
    """Lee los Excel y devuelve dos listas de diccionarios, SIN tocar la base de datos.

    Si no se entregan archivos, lee los de la carpeta insumos (datos de fábrica).
    Si se entregan, pueden ser archivos abiertos en memoria (io.BytesIO).
    """
    maestro, evaluaciones = leer_excel(origen_maestro, origen_evaluaciones)

    estudiantes = [
        {
            "identificacion": str(r.Identificacion),
            "nombre_completo": str(r.Nombre_Completo),
            "correo": str(r.Correo),
            "programa": str(r.Programa),
            "cohorte": str(r.Cohorte),
        }
        for r in maestro.itertuples(index=False)
    ]
    filas_evaluaciones = [
        {
            "identificacion": str(r.Identificacion),
            "programa": str(r.Programa),
            "modulo": str(r.Modulo),
            "nota": float(r.Nota),
            "asistencia_pct": float(r.Asistencia_Pct),
            "fecha_cierre": str(r.Fecha_Cierre)[:10],
        }
        for r in evaluaciones.itertuples(index=False)
    ]
    return estudiantes, filas_evaluaciones


def cargar_a_la_base(origen_maestro=None, origen_evaluaciones=None):
    """Lee los Excel y reemplaza el contenido de las tablas de la base de datos."""
    estudiantes, evaluaciones = leer_datos(origen_maestro, origen_evaluaciones)
    filas_est = [
        (e["identificacion"], e["nombre_completo"], e["correo"], e["programa"], e["cohorte"])
        for e in estudiantes
    ]
    filas_eva = [
        (e["identificacion"], e["programa"], e["modulo"], e["nota"],
         e["asistencia_pct"], e["fecha_cierre"])
        for e in evaluaciones
    ]
    datos.guardar_datos(filas_est, filas_eva)
    return len(filas_est), len(filas_eva)


def asegurar_datos():
    """Si la base está vacía (por ejemplo, la primera vez), carga los Excel de insumos."""
    n_est, n_eva = datos.contar_filas()
    if n_est == 0 and n_eva == 0:
        return cargar_a_la_base()
    return n_est, n_eva
