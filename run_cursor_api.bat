@echo off
echo ========================================
echo   Wolf CLI - Cursor API Server
echo ========================================
echo.

REM Get the directory where this batch file is located
set SCRIPT_DIR=%~dp0
set CURSOR_API_DIR=%SCRIPT_DIR%cursor_api

REM Check if cursor_api directory exists
if not exist "%CURSOR_API_DIR%" (
    echo Error: cursor_api directory not found!
    echo Expected location: %CURSOR_API_DIR%
    pause
    exit /b 1
)

REM Check if venv exists in cursor_api
set VENV_PATH=%CURSOR_API_DIR%\venv\Scripts\python.exe
if not exist "%VENV_PATH%" (
    echo Error: Virtual environment not found!
    echo Expected location: %CURSOR_API_DIR%\venv
    echo.
    echo Please run the installer or set up the cursor_api virtual environment.
    pause
    exit /b 1
)

echo Starting Cursor API Server...
echo Server will be available at: http://localhost:5005
echo.
echo Press Ctrl+C to stop the server.
echo.

REM Change to cursor_api directory
cd /d "%CURSOR_API_DIR%"

REM Launch Uvicorn server
"%VENV_PATH%" -m uvicorn cursor_api:app --host 0.0.0.0 --port 5005

REM Keep window open after server stops
echo.
echo Server stopped.
pause

