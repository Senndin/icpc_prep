@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul
set PYTHONUTF8=1

rem --- Install automatically on first start ---
if exist "venv\Scripts\python.exe" goto installed
echo The application is not installed yet. Running install.bat...
set ICPC_NO_PAUSE=1
call install.bat
if not exist "venv\Scripts\python.exe" goto not_installed
:installed

if exist "db.sqlite3" goto db_ready
"venv\Scripts\python.exe" manage.py migrate
"venv\Scripts\python.exe" manage.py seed_demo
:db_ready

echo.
echo ICPC Prep is starting at http://127.0.0.1:8000/
echo The browser opens as soon as the server is ready. Keep this window open.
echo To stop the server press Ctrl+C.
echo.
rem --- The helper waits until the server answers and only then opens the browser ---
start "" /b "venv\Scripts\python.exe" open_browser.py
"venv\Scripts\python.exe" manage.py runserver 127.0.0.1:8000
echo.
echo The server has stopped.
pause
exit /b 0

:not_installed
echo Installation did not complete, the application cannot start.
pause
exit /b 1
