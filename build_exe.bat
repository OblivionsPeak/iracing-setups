@echo off
echo ========================================
echo  iRacing Setup Manager - Build EXE
echo ========================================
echo.

:: Activate venv if it exists
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else (
    echo Creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
)

:: Install PyInstaller
pip install pyinstaller --quiet

:: Build
echo Building exe...
pyinstaller iracing_setups.spec --clean --noconfirm

echo.
if exist "dist\iRacing Setup Manager.exe" (
    echo BUILD SUCCESSFUL
    echo EXE is at: dist\iRacing Setup Manager.exe
) else (
    echo BUILD FAILED - check output above
)
pause
