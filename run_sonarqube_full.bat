@echo off
setlocal
cd /d "%~dp0"

call run_coverage.bat
if errorlevel 1 exit /b 1

call run_sonar.bat
if errorlevel 1 exit /b 1

endlocal
