@echo off
setlocal
cd /d "%~dp0"

echo ==========================================
echo  Ejecutando SonarScanner
 echo ==========================================

if "%SONAR_TOKEN%"=="" (
    echo ERROR: Primero define el token en esta consola:
    echo set SONAR_TOKEN=TU_TOKEN_REAL
    pause
    exit /b 1
)

where sonar-scanner >nul 2>nul
if errorlevel 1 (
    echo ERROR: sonar-scanner no esta instalado o no esta en el PATH.
    pause
    exit /b 1
)

sonar-scanner ^
  -Dsonar.host.url=http://localhost:9000 ^
  -Dsonar.token=%SONAR_TOKEN%

if errorlevel 1 (
    echo ERROR: El analisis de SonarQube fallo.
    pause
    exit /b 1
)

echo Analisis finalizado correctamente.
pause
