@echo off
rem Yakuza 5 Remastered - herramienta de traduccion: extraer textos
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (py -3 herramienta_traduccion.py extraer %*) else (python herramienta_traduccion.py extraer %*)
if %errorlevel%==9009 echo Falta Python 3: instalalo desde https://www.python.org (marca "Add python.exe to PATH").
pause
