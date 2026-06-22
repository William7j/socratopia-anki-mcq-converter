@echo off
setlocal
cd /d "%~dp0"
python "%~dp0socratopia_txt_to_anki_gui.py"
if errorlevel 1 (
  echo.
  echo Failed to start. Please make sure Python is installed and available in PATH.
  pause
)
