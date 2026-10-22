# App de Certificados de la Academia

## Problema
La Academia emite certificados cruzando a mano dos Excel. Esta app web lee los datos, los guarda en una base de datos, aplica las reglas, genera los certificados en PDF y muestra las inconsistencias. La app NO usa inteligencia artificial: son reglas fijas en Python.

## Estado actual
La app YA ESTÁ CONSTRUIDA Y PROBADA (versión de rescate de la Sesión 3). No la reconstruyas: solo haz los cambios pequeños que se te pidan, en el archivo de la capa que corresponda.

## Datos (insumos/, solo lectura)
- insumos/Maestro_Estudiantes.xlsx: Identificacion, Nombre_Completo, Correo, Programa, Cohorte (24 filas).
- insumos/Registro_Evaluaciones.xlsx: Identificacion, Programa, Modulo, Nota, Asistencia_Pct, Fecha_Cierre (88 filas).
- La Identificacion siempre se trata como texto, sin espacios.

## Base de datos
- Si existe DATABASE_URL en el archivo .env (o en Vercel), se usa Supabase (PostgreSQL, Transaction pooler, psycopg con prepare_threshold=None).
- Si no existe, se usa SQLite local (datos_local.db). En Vercel sin DATABASE_URL se usa /tmp.
- Tablas: estudiantes (identificacion PK, nombre_completo, correo, programa, cohorte) y evaluaciones (id, identificacion, programa, modulo, nota, asistencia_pct, fecha_cierre).
- Si las tablas están vacías, la app carga sola los Excel de insumos.

## Reglas del negocio (models/certificados.py)
- R1. Agrupar por identificacion + programa.
- R2. Promedio de nota y de asistencia_pct, redondeados a 2 decimales.
- R3. Aprobación: promedio >= 70 y asistencia >= 80 (los límites incluyen).
- R4. Participación: promedio < 70 y asistencia >= 80.
- R5. Sin certificado: asistencia < 80.
- R6. Inconsistencias (alerta, no se certifican): en el maestro sin evaluaciones; con evaluaciones pero no está en el maestro; asistencia menor a 50 %.

## Cifras de control
- 19 Aprobación, 3 Participación, 1 Sin certificado y 3 inconsistencias (304560321 sin evaluaciones, 999880777 no está en el maestro, Fernanda Zúñiga asistencia 36.25).
- Camila Rojas Méndez 101230456 = 91.25 / 96.25 Aprobación. Luis Acuña Blanco = 72.0 / 81.67 Aprobación.
- El .zip de certificados trae 22 PDF.

## Arquitectura (MVC)
- models/datos.py: único archivo que habla con la base de datos.
- models/certificados.py: reglas del negocio (NOTA_MINIMA = 70, ASISTENCIA_MINIMA = 80).
- services/carga_excel.py: leer los Excel y guardarlos en la base.
- services/generador_pdf.py: certificado PDF con fpdf2, en memoria.
- controllers/rutas.py: rutas de Flask. No calculan.
- views/: plantillas HTML (Jinja). Azul marino #14213D y dorado #B8923D.
- app.py: crea la variable app (Vercel la busca ahí).
- Python 3.12 con uv (nunca pip). Se enciende con iniciar_app.bat.

## Cómo trabajar conmigo
- Responde en español, con lenguaje sencillo: soy principiante.
- Cambios pequeños: dime qué archivo cambiaste y en qué capa está.
- Nunca modifiques insumos/. Nunca leas ni muestres el archivo .env. Nunca escribas contraseñas en el código.
- Ahorra cuota: no leas todo el proyecto si te indico el archivo con @.
