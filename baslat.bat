@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Animasyon Canavari
if not exist ".venv\Scripts\python.exe" (
  echo Once kur.bat'i calistir.
  pause
  exit /b 1
)
set PYTHONIOENCODING=utf-8
echo Animasyon Canavari aciliyor... Bu pencereyi kapatma; kapatirsan arayuz durur.
".venv\Scripts\python.exe" arayuz\sunucu.py
pause
