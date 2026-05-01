@echo off
setlocal
cd /d "%~dp0"

echo ==========================================
echo  Generando coverage.xml real del proyecto
echo ==========================================

echo.
echo Instalando dependencias de pruebas...
python -m pip install -r requirements-dev.txt
if errorlevel 1 goto error

echo.
echo Ejecutando pruebas con coverage...
coverage erase
coverage run -m pytest tests
if errorlevel 1 goto error

echo.
echo Generando coverage.xml en formato Cobertura...
coverage xml -o coverage.xml
if errorlevel 1 goto error

echo.
echo Resumen de cobertura:
coverage report --fail-under=80
if errorlevel 1 goto error

echo.
echo ==========================================
echo  Coverage generado correctamente
 echo  Debe superar el 80%% si las pruebas pasan
 echo ==========================================
pause
exit /b 0

:error
echo.
echo ERROR: No se pudo generar coverage mayor o igual al 80%%.
echo Revisa el error mostrado arriba.
pause
exit /b 1
