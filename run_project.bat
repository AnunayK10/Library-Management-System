@echo off
title Online Library Management System - Project Launcher
cd /d "%~dp0"
python run.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    pause
)
