@echo off
setlocal
cd /d "%~dp0"

echo ==========================================
echo    INICIANDO POS PROFESIONAL - CACHAPEATE
echo ==========================================
echo.

:: Verificar si Python esta instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] No se encontro Python en el sistema.
    echo Por favor, instala Python 3 desde https://www.python.org/
    echo Asegurate de marcar la casilla "Add Python to PATH" durante la instalacion.
    pause
    exit /b
)

:: Gestion del Entorno Virtual (venv)
if not exist venv (
    echo [INFO] Creando entorno virtual venv por primera vez...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] No se pudo crear el entorno virtual.
        pause
        exit /b
    )
)

echo [INFO] Activando entorno virtual...
call venv\Scripts\activate

:: Verificar si las dependencias estan instaladas (comprobando Pillow como referencia)
python -c "from PIL import Image" >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Instalando dependencias en el entorno virtual...
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [ERROR] No se pudieron instalar las dependencias.
        pause
        exit /b
    )
)

echo [INFO] Iniciando programa...
echo.
python programa.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] El programa se cerro con un error.
    pause
)

deactivate
