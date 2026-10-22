@echo off
chcp 65001 >nul
title App de Certificados
cd /d "%~dp0"
echo.
echo  ==============================================
echo   App de Certificados - Academia Horizonte
echo  ==============================================
echo.
where uv >nul 2>nul
if errorlevel 1 (
  echo  Instalando uv por primera vez, espere un momento...
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  set "PATH=%USERPROFILE%\.local\bin;%PATH%"
)
echo  Preparando las librerias (la primera vez tarda 1 o 2 minutos)...
uv sync
if errorlevel 1 (
  echo.
  echo  No se pudieron instalar las librerias. Revise su conexion a internet y vuelva a intentarlo.
  pause
  exit /b 1
)
start "" /min cmd /c "timeout /t 6 >nul & start http://127.0.0.1:5000"
uv run app.py
pause
