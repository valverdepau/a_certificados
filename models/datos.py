"""
CAPA MODELO · datos.py
Único archivo que habla con la base de datos.

- Si existe la variable DATABASE_URL (archivo .env o Vercel), usa Supabase (PostgreSQL).
- Si no existe, usa una base SQLite local (un archivo en su computador) para que
  la app funcione igual mientras se configura Supabase.
"""
import os
import sqlite3
from pathlib import Path

CARPETA_PROYECTO = Path(__file__).resolve().parent.parent

TABLA_ESTUDIANTES = """
CREATE TABLE IF NOT EXISTS estudiantes (
    identificacion  TEXT PRIMARY KEY,
    nombre_completo TEXT NOT NULL,
    correo          TEXT,
    programa        TEXT NOT NULL,
    cohorte         TEXT
)
"""

TABLA_EVALUACIONES_PG = """
CREATE TABLE IF NOT EXISTS evaluaciones (
    id             SERIAL PRIMARY KEY,
    identificacion TEXT NOT NULL,
    programa       TEXT NOT NULL,
    modulo         TEXT,
    nota           NUMERIC(6,2),
    asistencia_pct NUMERIC(6,2),
    fecha_cierre   TEXT
)
"""

TABLA_EVALUACIONES_SQLITE = """
CREATE TABLE IF NOT EXISTS evaluaciones (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    identificacion TEXT NOT NULL,
    programa       TEXT NOT NULL,
    modulo         TEXT,
    nota           REAL,
    asistencia_pct REAL,
    fecha_cierre   TEXT
)
"""


def _url():
    return os.getenv("DATABASE_URL", "").strip()


def usa_supabase():
    """True si la app está conectada a Supabase (PostgreSQL)."""
    return _url().startswith(("postgres://", "postgresql://"))


def nombre_motor():
    return "Supabase (PostgreSQL)" if usa_supabase() else "SQLite local (sin Supabase todavía)"


def _ruta_sqlite():
    # En Vercel solo se puede escribir en /tmp; en su computador, en la carpeta del proyecto.
    if os.getenv("VERCEL"):
        return Path("/tmp/datos_local.db")
    return CARPETA_PROYECTO / "datos_local.db"


def conectar():
    """Abre una conexión. El texto de las consultas usa %s en PostgreSQL y ? en SQLite."""
    if usa_supabase():
        import psycopg  # solo se importa cuando hay Supabase

        # prepare_threshold=None: necesario con el "Transaction pooler" de Supabase.
        return psycopg.connect(_url(), prepare_threshold=None, connect_timeout=15)
    return sqlite3.connect(_ruta_sqlite())


def _marca():
    return "%s" if usa_supabase() else "?"


def crear_tablas():
    con = conectar()
    try:
        cur = con.cursor()
        cur.execute(TABLA_ESTUDIANTES)
        cur.execute(TABLA_EVALUACIONES_PG if usa_supabase() else TABLA_EVALUACIONES_SQLITE)
        con.commit()
    finally:
        con.close()


def guardar_datos(estudiantes, evaluaciones):
    """Reemplaza el contenido de las dos tablas.
    estudiantes y evaluaciones son listas de tuplas, en el orden de las columnas."""
    crear_tablas()
    m = _marca()
    con = conectar()
    try:
        cur = con.cursor()
        cur.execute("DELETE FROM evaluaciones")
        cur.execute("DELETE FROM estudiantes")
        cur.executemany(
            f"INSERT INTO estudiantes (identificacion, nombre_completo, correo, programa, cohorte) "
            f"VALUES ({m}, {m}, {m}, {m}, {m})",
            estudiantes,
        )
        cur.executemany(
            f"INSERT INTO evaluaciones (identificacion, programa, modulo, nota, asistencia_pct, fecha_cierre) "
            f"VALUES ({m}, {m}, {m}, {m}, {m}, {m})",
            evaluaciones,
        )
        con.commit()
    finally:
        con.close()


def contar_filas():
    """Devuelve (filas de estudiantes, filas de evaluaciones)."""
    crear_tablas()
    con = conectar()
    try:
        cur = con.cursor()
        cur.execute("SELECT COUNT(*) FROM estudiantes")
        n_est = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM evaluaciones")
        n_eva = cur.fetchone()[0]
        return int(n_est), int(n_eva)
    finally:
        con.close()


def leer_estudiantes():
    con = conectar()
    try:
        cur = con.cursor()
        cur.execute(
            "SELECT identificacion, nombre_completo, correo, programa, cohorte "
            "FROM estudiantes ORDER BY nombre_completo"
        )
        columnas = ["identificacion", "nombre_completo", "correo", "programa", "cohorte"]
        return [dict(zip(columnas, fila)) for fila in cur.fetchall()]
    finally:
        con.close()


def leer_evaluaciones():
    con = conectar()
    try:
        cur = con.cursor()
        cur.execute(
            "SELECT identificacion, programa, modulo, nota, asistencia_pct, fecha_cierre "
            "FROM evaluaciones ORDER BY id"
        )
        columnas = ["identificacion", "programa", "modulo", "nota", "asistencia_pct", "fecha_cierre"]
        filas = []
        for fila in cur.fetchall():
            d = dict(zip(columnas, fila))
            d["nota"] = float(d["nota"])
            d["asistencia_pct"] = float(d["asistencia_pct"])
            filas.append(d)
        return filas
    finally:
        con.close()
