@echo off
setlocal EnableDelayedExpansion

REM MOD=1 para crear el servicio, MOD=0 para eliminarlo
set MOD=0

REM Requiere privilegios de administrador
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Necesitas ejecutar como administrador
    pause
    exit /b 1
)

set "SERVICE_NAME=DownloadOrganizerService"
set "SCRIPT_PATH=%~dp0src\extension_organizador\server.py"
set "PYTHON_PATH=pythonw.exe"

if %MOD%==1 (
    REM Crear el servicio
    sc create %SERVICE_NAME% binPath= "%PYTHON_PATH% %SCRIPT_PATH%" start= auto
    sc description %SERVICE_NAME% "Servicio para organizar descargas automáticamente"
    sc start %SERVICE_NAME%
    echo Servicio creado y iniciado exitosamente
) else (
    REM Detener y eliminar el servicio
    sc stop %SERVICE_NAME%
    sc delete %SERVICE_NAME%
    echo Servicio eliminado exitosamente
)

pause