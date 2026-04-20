@echo off
title Cachapéate POS - Servidor Backend
echo =========================================
echo       Iniciando Cachapéate POS...
echo =========================================
echo.
echo Presiona Ctrl+C en esta ventana para apagar el sistema.
echo.

:: Verificar si el entorno virtual existe
if not exist "venv/Scripts/python.exe" (
    echo [ERROR] No se encontro el entorno virtual en la carpeta 'venv'.
    echo Por favor, asegurese de que la instalacion sea correcta.
    pause
    exit /b
)

:: Levantar el servidor Flask usando el entorno virtual
:: Usamos 'start' para abrir el servidor en una ventana y el navegador en otra
start "Servidor POS" cmd /k "venv\Scripts\python.exe app.py"

:: Esperar 3 segundos para dar tiempo a que Flask arranque
timeout /t 3 /nobreak > nul

:: Lanzar el navegador predeterminado
echo Abriendo navegador en http://localhost:5000...
start http://localhost:5000
