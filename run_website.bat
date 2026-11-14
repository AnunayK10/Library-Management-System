@echo off
title Online Library Management System - Web Server
cd /d "%~dp0"
echo ========================================================
echo   ONLINE LIBRARY MANAGEMENT SYSTEM - WEB PORTAL
echo ========================================================
echo Starting Flask Server and opening browser...
start "" http://127.0.0.1:5000
python app_web.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo An error occurred while running app_web.py.
    pause
)
