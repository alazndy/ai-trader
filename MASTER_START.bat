@echo off
title AI TRADER MASTER CONTROL
color 1F
echo ========================================================
echo   AI TRADER MASTER START
echo   Initializing All Systems...
echo ========================================================
echo.

:: 1. Dashboard
echo [1/5] Launching Dashboard...
start "AI Trader - DASHBOARD" cmd /k call Run_Dashboard.bat

:: 2. Crypto (High Freq)
echo [2/5] Launching Crypto Bot (5m)...
start "AI Trader - CRYPTO" cmd /k call Run_Crypto.bat

:: 3. Stocks (Hourly)
echo [3/5] Launching BIST Bot...
start "AI Trader - BIST" cmd /k call Run_BIST.bat

echo [4/5] Launching US Global Bot...
start "AI Trader - GLOBAL" cmd /k call Run_Global.bat

echo [5/5] Launching CHIPS Bot...
start "AI Trader - CHIPS" cmd /k call Run_Chips.bat

echo.
echo ========================================================
echo   ALL SYSTEMS GO! 🚀
echo   You can minimize the popup windows, but DO NOT close them.
echo ========================================================
timeout /t 10
