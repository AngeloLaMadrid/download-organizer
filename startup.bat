@echo off
REM Ejecutar el script de Python para organizar descargas
 
REM Obtener la ruta del script actual
set SCRIPT_PATH=%~dp0

REM Copiar el archivo .bat a la carpeta de inicio
set STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
copy "%SCRIPT_PATH%startup.bat" "%STARTUP_FOLDER%"

REM Ejecutar el script de Python
python "%SCRIPT_PATH%organizar.py"