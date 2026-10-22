"""
CAPA MODELO · certificados.py
Las reglas del negocio. Aquí no hay inteligencia artificial: son reglas fijas.

R1. Agrupar por identificacion + programa.
R2. Promedio = promedio de las notas; asistencia = promedio de asistencia_pct (2 decimales).
R3. Aprobación: promedio >= 70 y asistencia >= 80 (los límites incluyen).
R4. Participación: promedio < 70 y asistencia >= 80.
R5. Sin certificado: asistencia < 80.
R6. Inconsistencias (no se certifican, se muestran como alerta).
"""

# Variables (constantes) del negocio: si la Academia cambia la regla, se cambia aquí.
NOTA_MINIMA = 70
ASISTENCIA_MINIMA = 80
ASISTENCIA_ALERTA = 50

APROBACION = "Aprobación"
PARTICIPACION = "Participación"
SIN_CERTIFICADO = "Sin certificado"


def tipo_de_certificado(promedio, asistencia):
    """Función con condicionales: decide el tipo de certificado de una persona."""
    if asistencia < ASISTENCIA_MINIMA:
        return SIN_CERTIFICADO
    if promedio >= NOTA_MINIMA:
        return APROBACION
    return PARTICIPACION


def calcular_resultados(estudiantes, evaluaciones):
    """Recibe las filas de la base y devuelve los resultados, los contadores y las inconsistencias."""
    maestro = {e["identificacion"]: e for e in estudiantes}

    # R1: agrupar las evaluaciones por identificacion + programa (un diccionario de listas)
    grupos = {}
    for ev in evaluaciones:
        llave = (ev["identificacion"], ev["programa"])
        grupos.setdefault(llave, []).append(ev)

    resultados = []
    inconsistencias = []

    for (identificacion, programa), evs in grupos.items():
        # R2: promedios
        promedio = round(sum(e["nota"] for e in evs) / len(evs), 2)
        asistencia = round(sum(e["asistencia_pct"] for e in evs) / len(evs), 2)

        estudiante = maestro.get(identificacion)
        if estudiante is None:
            # R6: tiene evaluaciones pero no está en el maestro -> no se certifica
            inconsistencias.append({
                "identificacion": identificacion,
                "nombre": "(no está en el maestro)",
                "motivo": "Tiene evaluaciones pero no aparece en el maestro de estudiantes",
            })
            continue

        tipo = tipo_de_certificado(promedio, asistencia)
        resultados.append({
            "identificacion": identificacion,
            "nombre": estudiante["nombre_completo"],
            "correo": estudiante["correo"],
            "programa": programa,
            "cohorte": estudiante["cohorte"],
            "modulos": len(evs),
            "promedio": promedio,
            "asistencia": asistencia,
            "tipo": tipo,
        })

        if asistencia < ASISTENCIA_ALERTA:
            # R6: asistencia muy baja -> alerta para revisión humana
            inconsistencias.append({
                "identificacion": identificacion,
                "nombre": estudiante["nombre_completo"],
                "motivo": f"Asistencia de {asistencia:.2f} %, menor al {ASISTENCIA_ALERTA} %",
            })

    # R6: está en el maestro pero no tiene ninguna evaluación
    con_evaluaciones = {i for (i, _p) in grupos}
    for identificacion, est in maestro.items():
        if identificacion not in con_evaluaciones:
            inconsistencias.append({
                "identificacion": identificacion,
                "nombre": est["nombre_completo"],
                "motivo": "Está en el maestro pero no tiene evaluaciones",
            })

    resultados.sort(key=lambda r: r["nombre"])
    contadores = {
        APROBACION: sum(1 for r in resultados if r["tipo"] == APROBACION),
        PARTICIPACION: sum(1 for r in resultados if r["tipo"] == PARTICIPACION),
        SIN_CERTIFICADO: sum(1 for r in resultados if r["tipo"] == SIN_CERTIFICADO),
    }
    return resultados, contadores, inconsistencias


def lleva_certificado(resultado):
    return resultado["tipo"] in (APROBACION, PARTICIPACION)
