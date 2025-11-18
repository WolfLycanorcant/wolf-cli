@echo off
echo Starting Cursor API Server...
echo.

REM Change to your project directory


REM Launch Uvicorn server
.\venv\Scripts\python.exe -m uvicorn cursor_api:app --host 0.0.0.0 --port 5005

REM Keep window open after server stops
pause
