@echo off
chcp 65001 > nul
title ⚡ PAYOMBOY CALL BOMBER — LOCAL ENGINE ⚡
color 0B
cd /d "%~dp0"

set PYTHONIOENCODING=utf-8
set PYTHONUNBUFFERED=1

cls
echo ======================================================================
echo   ⚡ PAYOMBOY CALL BOMBER — LOCAL THAI RESIDENTIAL ENGINE ⚡
echo   • Connection: Domestic Thai Residential ISP (Max Delivery Rate)
echo   • Status: Running locally on your machine
echo   • Auto-Restart: Active (restarts if connection drops)
echo ======================================================================
echo.

:loop
echo [*] Launching PayomboyCallBomber Discord Bot...
echo.
python run_bot.py

echo.
echo ======================================================================
echo [!] Bot process exited.
echo [*] Press Ctrl+C to close window, or waiting 5 seconds to restart...
echo ======================================================================
timeout /t 5 /nobreak > nul
goto loop
