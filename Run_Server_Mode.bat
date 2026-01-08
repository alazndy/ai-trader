@echo off
title AI TRADER SERVER BOSS
color 0A
echo ========================================================
echo   AI TRADER SERVER MODE DETECTED
echo   Launching 5 Independent Agents...
echo ========================================================
echo.

echo 1. Starting Dashboard (Web Interface)...
start "AI Trader - DASHBOARD" cmd /k call Run_Dashboard.bat

echo 2. Starting Crypto Bot (5min Scalper)...
start "AI Trader - CRYPTO" cmd /k call Run_Crypto.bat

echo 3. Starting BIST Bot (Hourly)...
start "AI Trader - BIST" cmd /k call Run_BIST.bat

echo 4. Starting GLOBAL Bot (Hourly)...
start "AI Trader - GLOBAL" cmd /k call Run_Global.bat

echo 5. Starting CHIPS Bot (Hourly)...
start "AI Trader - CHIPS" cmd /k call Run_Chips.bat

echo.
echo ========================================================
echo   SYSTEM OPERATIONAL. DO NOT CLOSE THIS WINDOW.
echo   Use Ctrl+C in individual windows to stop specific bots.
echo ========================================================
pause
