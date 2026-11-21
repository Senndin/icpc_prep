@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul
set PYTHONUTF8=1
echo === ICPC Prep: install ===

rem --- 1. Look for a suitable Python (3.10 or newer) ---
set "PY="
call :check_python py -3
if not defined PY call :check_python python
if not defined PY call :check_python python3
if defined PY goto have_python

echo Python 3.10 or newer was not found on this computer.
where winget >nul 2>nul
if errorlevel 1 goto no_python
choice /C YN /M "Install Python 3.12 now with winget"
if errorlevel 2 goto no_python
winget install -e --id Python.Python.3.12 --scope user --accept-package-agreements --accept-source-agreements
echo.
echo Python has been installed. Close this window and run install.bat again.
pause
exit /b 0

:no_python
echo Install Python 3.10+ from https://www.python.org/downloads/
echo During setup tick "Add python.exe to PATH", then run install.bat again.
pause
exit /b 1

:have_python
echo Python found: %PY% - nothing to install.

rem --- 2. Virtual environment ---
if exist "venv\Scripts\python.exe" goto venv_ready
echo Creating virtual environment...
%PY% -m venv venv
if errorlevel 1 goto failed
:venv_ready

rem --- 3. Libraries ---
echo Installing libraries...
"venv\Scripts\python.exe" -m pip install --disable-pip-version-check -r requirements.txt
if errorlevel 1 goto failed

rem --- 4. Database (demo data only on first install) ---
set "FRESH=1"
if exist "db.sqlite3" set "FRESH=0"
"venv\Scripts\python.exe" manage.py migrate
if errorlevel 1 goto failed
if "%FRESH%"=="0" goto done
"venv\Scripts\python.exe" manage.py seed_demo
if errorlevel 1 goto failed

:done
echo.
echo Installation finished. Start the application with run.bat
if not defined ICPC_NO_PAUSE pause
exit /b 0

:failed
echo.
echo Installation FAILED. See the messages above.
pause
exit /b 1

:check_python
%* -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>nul
if not errorlevel 1 set "PY=%*"
exit /b 0
