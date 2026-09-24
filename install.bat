@echo off
rem Installazione di ScriVoice su Windows: doppio clic su questo file.
cd /d "%~dp0"
echo === Installazione di ScriVoice ===
echo.

set "PY=python"
where py >nul 2>nul && set "PY=py -3"
%PY% --version >nul 2>nul
if errorlevel 1 (
  echo Python non trovato. Installalo da https://www.python.org/downloads/
  echo ^(durante l'installazione spunta "Add python.exe to PATH"^), poi rilancia questo file.
  pause
  exit /b 1
)

echo Preparo Python...
if exist .venv rmdir /s /q .venv
%PY% -m venv .venv || goto :error

echo Installo le librerie (qualche minuto)...
.venv\Scripts\python -m pip install --upgrade pip >nul
.venv\Scripts\python -m pip install -r requirements.txt || goto :error

echo Creo l'icona e i collegamenti (Desktop e menu Start)...
.venv\Scripts\python setup_shortcut.py || goto :error

echo.
echo Installazione completata! Avvia "ScriVoice" dal Desktop o dal menu Start.
pause
exit /b 0

:error
echo.
echo Errore durante l'installazione.
pause
exit /b 1
