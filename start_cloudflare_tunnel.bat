@echo off
title Cloudflare Tunnel - Tibbi STT
echo ====================================================
echo   Cloudflare Tunnel ise salir (Port 7860)...
echo ====================================================
"C:\Program Files (x86)\cloudflared\cloudflared.exe" tunnel --url http://127.0.0.1:7860
pause
