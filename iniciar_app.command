#!/bin/bash
# Enciende la App de Certificados en Mac.
# Doble clic en este archivo (o ejecutelo en la Terminal).
cd "$(dirname "$0")" || exit 1

echo ""
echo " =============================================="
echo "  App de Certificados - Academia Horizonte"
echo " =============================================="
echo ""

if ! command -v uv >/dev/null 2>&1; then
  echo " Instalando uv por primera vez, espere un momento..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi

echo " Preparando las librerias (la primera vez tarda 1 o 2 minutos)..."
if ! uv sync; then
  echo ""
  echo " No se pudieron instalar las librerias. Revise su conexion a internet y vuelva a intentarlo."
  read -r -p " Presione Enter para cerrar..."
  exit 1
fi

# El puerto 5000 lo usa AirPlay en los Mac, por eso usamos el 5001.
export PORT=5001
( sleep 6; open "http://127.0.0.1:$PORT" ) &
uv run app.py
read -r -p " Presione Enter para cerrar..."
