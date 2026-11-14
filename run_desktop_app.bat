@echo off
title Online Library Management System - Desktop GUI
cd /d "%~dp0"
echo ========================================================
echo   ONLINE LIBRARY MANAGEMENT SYSTEM - DESKTOP GUI
echo ========================================================
echo Starting Tkinter Application...
python app_gui.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo An error occurred while running app_gui.py.
    pause
)
