@echo off
echo ============================================
echo   Social Sentiment Backend Starter
echo ============================================
echo.

REM Activate virtual environment (must run from project root)
IF EXIST .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
    echo [OK] Virtual environment activated
) ELSE (
    echo [ERROR] Virtual environment not found at .venv\
    echo Please run: python -m venv .venv
    echo Then:       .venv\Scripts\pip install -r backend\requirements.txt
    pause
    exit /b 1
)

echo.
echo [INFO] Starting FastAPI backend at http://127.0.0.1:8000
echo [INFO] API docs at  http://127.0.0.1:8000/docs
echo [INFO] Press Ctrl+C to stop
echo.

REM IMPORTANT: Run from root so "backend.xxx" imports resolve correctly
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000

pause
