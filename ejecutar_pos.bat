@echo off
title Cachapéate POS - Servidor Backend
echo =========================================
echo       Iniciando Cachapéate POS...
echo =========================================
echo.
echo Presiona Ctrl+C en esta ventana para apagar el sistema.
echo.

:: Levantar el servidor Flask en otra ventana oculta o minimizada no es recomendable
:: porque es mejor ver los logs. Asignamos inicio normal y asincrono del navegador.
start "Servidor POS" cmd /c "python app.py"

:: Esperar 2 segundos para dar tiempo a que Flask arranque en el puerto 5000
timeout /t 2 /nobreak > nul

:: Lanzar el navegador predeterminado a la dirección correcta automáticamente
echo Abriendo navegador en localhost:5000...
start http://localhost:5000
