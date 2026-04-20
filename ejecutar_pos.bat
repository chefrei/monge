@echo off
title Cachapéate POS - Servidor Backend
echo =========================================
echo       Iniciando Cachapéate POS...
echo =========================================
echo.
echo Presiona Ctrl+C en esta ventana para apagar el sistema.
echo.

:: Verificar o crear el entorno virtual automáticamente
if not exist "venv\Scripts\python.exe" (
    echo [INFO] No se encontro el entorno virtual en la carpeta 'venv'.
    echo [INFO] Creandolo e instalando dependencias (esto solo ocurrira la primera vez)...
    
    :: Crear el entorno virtual
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] No se pudo crear el entorno virtual. 
        echo Asegurese de tener Python instalado y accesible desde la linea de comandos.
        pause
        exit /b
    )

    :: Instalar dependencias desde requirements.txt
    echo [INFO] Instalando librerias necesarias...
    venv\Scripts\pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] No se pudieron instalar las dependencias. 
        echo Verifique su conexion a internet e intente de nuevo.
        pause
        exit /b
    )
    
    echo [OK] Entorno virtual preparado exitosamente.
    echo.
)

:: Levantar el servidor Flask usando el entorno virtual
:: Usamos 'start' para abrir el servidor en una ventana y el navegador en otra
start "Servidor POS" cmd /k "venv\Scripts\python.exe app.py"

:: Esperar 3 segundos para dar tiempo a que Flask arranque
timeout /t 3 /nobreak > nul

:: Lanzar el navegador predeterminado
echo Abriendo navegador en http://localhost:5000...
start http://localhost:5000
