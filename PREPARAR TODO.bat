@echo off
rem Descarga de una vez todo lo necesario para COMPILAR la traduccion (programas, fuentes y paquetes de Python).
rem Para JUGAR no hace falta: basta el zip de Releases.
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "herramientas\preparar_todo.ps1" %*
pause
