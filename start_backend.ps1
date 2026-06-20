# start_backend.ps1 — Jalankan dari root project folder
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Social Sentiment Backend Starter" -ForegroundColor Cyan  
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Aktivasi virtual environment
if (Test-Path ".venv\Scripts\Activate.ps1") {
    & ".venv\Scripts\Activate.ps1"
    Write-Host "[OK] Virtual environment activated" -ForegroundColor Green
} else {
    Write-Host "[ERROR] .venv tidak ditemukan!" -ForegroundColor Red
    Write-Host "Jalankan: python -m venv .venv" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "[INFO] Backend berjalan di  http://127.0.0.1:8000" -ForegroundColor Green
Write-Host "[INFO] API docs di          http://127.0.0.1:8000/docs" -ForegroundColor Green
Write-Host "[INFO] Tekan Ctrl+C untuk stop" -ForegroundColor Yellow
Write-Host ""

# PENTING: jalankan dari root agar import 'backend.xxx' bisa ditemukan
# Gunakan 'python -m uvicorn' agar tidak bergantung pada launcher script
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
