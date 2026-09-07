@echo off
chcp 65001 > nul
echo ============================================================
echo   Tibbi Səs-Mətn Sistemi (Gemini API)
echo ============================================================
echo.
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
python app_gemini.py
pause
