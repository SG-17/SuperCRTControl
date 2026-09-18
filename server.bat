@echo off
:loop
echo ================================================
echo Super CRT-Control Web Server
echo Started at %date% %time%
echo ================================================

python server.py

echo.

echo(%time% %date%) server crashed / restarting...
goto loop 