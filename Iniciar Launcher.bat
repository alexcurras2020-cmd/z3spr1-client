@echo off
rem Situarse en la carpeta del script: permite abrirlo desde un acceso directo.
cd /d "%~dp0"

set "PY="
where python >nul 2>nul && set "PY=python"
if not defined PY (where py >nul 2>nul && set "PY=py -3")

if not defined PY (
    echo No se encontro Python en el sistema.
    echo Instalalo desde https://www.python.org/downloads/ marcando "Add Python to PATH".
    pause
    exit /b 1
)

%PY% launcher.py
if errorlevel 1 pause
