@echo off
cd /d %~dp0

echo ========================================
echo  Cambridge Academy - Pruebas rapidas
echo ========================================
echo.

if exist venv\Scripts\activate (
    call venv\Scripts\activate
)

echo Ejecutando pruebas rapidas...
echo.

python -m pytest ^
    tests/test_entities.py ^
    tests/test_service_utils.py ^
    tests/test_login_service.py ^
    -v

echo.
pause
