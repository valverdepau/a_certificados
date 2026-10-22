"""
app.py · enciende la aplicación.
Vercel busca en este archivo una variable llamada app.
"""
import os

from dotenv import load_dotenv
from flask import Flask

load_dotenv()  # lee el archivo .env (DATABASE_URL), si existe

from controllers.rutas import rutas  # noqa: E402

app = Flask(__name__, template_folder="views")
app.secret_key = os.getenv("SECRET_KEY", "clave-de-clase-cambiar-en-produccion")
app.config["MAX_CONTENT_LENGTH"] = 4 * 1024 * 1024  # Vercel no acepta archivos de más de 4.5 MB
app.register_blueprint(rutas)

if __name__ == "__main__":
    # El puerto se puede cambiar con la variable PORT (por ejemplo, si el 5000 está ocupado en su Mac).
    puerto = int(os.getenv("PORT", "5000"))
    print(f"\n  App de Certificados encendida en: http://127.0.0.1:{puerto}")
    print("  Para apagarla, cierre esta ventana.\n")
    app.run(host="127.0.0.1", port=puerto, debug=False)
