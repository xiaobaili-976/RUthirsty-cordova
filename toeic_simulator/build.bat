@echo off
setlocal
echo ============================================================
echo  TOEIC Speaking Test Simulator — Build Script
echo ============================================================
echo.

:: Install / upgrade dependencies
echo [1/3] Installing Python dependencies...
pip install --upgrade PyQt6 pyttsx3 pyinstaller
if errorlevel 1 (
    echo ERROR: pip install failed. Make sure Python 3.9+ is on PATH.
    pause & exit /b 1
)

echo.
echo [2/3] Building EXE with PyInstaller...
pyinstaller ^
    --onefile ^
    --windowed ^
    --name "TOEIC_Speaking_Simulator" ^
    --hidden-import pyttsx3.drivers ^
    --hidden-import pyttsx3.drivers.sapi5 ^
    --hidden-import PyQt6.QtTextToSpeech ^
    main.py

if errorlevel 1 (
    echo ERROR: PyInstaller build failed.
    pause & exit /b 1
)

echo.
echo [3/3] Copying runtime files to dist\...
if not exist "dist\images" mkdir "dist\images"
copy /Y "questions.json" "dist\" >nul 2>&1
echo     questions.json  ->  dist\questions.json
echo     images\         ->  dist\images\  (copy your PART 2 images here)

echo.
echo ============================================================
echo  Build complete!
echo  EXE location:  dist\TOEIC_Speaking_Simulator.exe
echo.
echo  Before running:
echo    1. Edit  dist\questions.json  with your questions.
echo    2. Place PART 2 images inside  dist\images\
echo       (paths must match questions.json, e.g. images\q3.jpg)
echo    3. Double-click the EXE — no Python required!
echo ============================================================
pause
