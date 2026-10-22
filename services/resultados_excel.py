"""
CAPA SERVICIOS · resultados_excel.py
Arma un archivo Excel con los resultados EN MEMORIA (sin escribir en el disco).
Se usa cuando el administrador pide "Procesar y descargar Excel".
"""
import io

import pandas as pd

# Nombres de las columnas del Excel que se descarga (en el mismo orden).
COLUMNAS = ["Identificación", "Nombre", "Programa", "Cohorte", "Módulos",
            "Promedio", "Asistencia %", "Certificado"]


def crear_excel(resultados):
    """Devuelve un Excel listo para descargar, guardado en memoria (io.BytesIO)."""
    filas = [
        {
            "Identificación": str(r["identificacion"]),
            "Nombre": r["nombre"],
            "Programa": r["programa"],
            "Cohorte": r["cohorte"],
            "Módulos": r["modulos"],
            "Promedio": r["promedio"],
            "Asistencia %": r["asistencia"],
            "Certificado": r["tipo"],
        }
        for r in resultados
    ]
    tabla = pd.DataFrame(filas, columns=COLUMNAS)

    # BytesIO es como una caja de archivos en la memoria (RAM): se usa igual que un
    # archivo del disco, pero no toca el disco. Vercel solo permite escribir en /tmp,
    # así que el Excel se arma aquí y se envía tal cual.
    memoria = io.BytesIO()
    with pd.ExcelWriter(memoria, engine="openpyxl") as escritor:
        tabla.to_excel(escritor, index=False, sheet_name="Resultados")
    memoria.seek(0)  # vuelve al inicio para que send_file lo lea desde el principio
    return memoria
