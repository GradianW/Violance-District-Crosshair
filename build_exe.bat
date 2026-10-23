@echo off
title Building VD_Crosshair.exe
cd /d "%~dp0"
echo Installing/Verifying PyInstaller...
.\.venv\Scripts\pip install pyinstaller
echo Building standalone VD_Crosshair.exe...
.\.venv\Scripts\pyinstaller --noconsole --onefile --clean --name "VD_Crosshair" main.py
echo.
echo Done! Your standalone executable is ready at: dist\VD_Crosshair.exe
pause
