@echo off
cd /d %~dp0

echo ========================================
echo  Cambridge Academy - Robot de pruebas
echo ========================================
echo.

if exist venv\Scripts\activate (
    call venv\Scripts\activate
)

echo Verificando dependencias de pruebas...
python -m pip install -r requirements-test.txt

if not exist reports (
    mkdir reports
)

echo.
echo Ejecutando pruebas automatizadas...
echo.

python -m pytest ^
    tests/test_entities.py ^
    tests/test_service_utils.py ^
    tests/test_login_service.py ^
    --html=reports/test_report.html ^
    --self-contained-html ^
    --cov=ca_program ^
    --cov-report=html:reports/coverage ^
    -v

echo.
echo ========================================
echo  Reportes generados
echo ========================================
echo  HTML:      reports\test_report.html
echo  Coverage:  reports\coverage\index.html
echo ========================================
echo.

pause
