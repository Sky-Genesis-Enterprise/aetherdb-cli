@echo off
REM Batch installer for AetherDB CLI on Windows

where python >nul 2>nul
if errorlevel 1 (
    echo Python not found. Please install Python 3.8+ and add it to your PATH.
    exit /b 1
)

REM Create virtual environment
echo Creating virtual environment...
python -m venv .venv
if errorlevel 1 (
    echo Failed to create virtualenv. Make sure python-venv is installed!
    exit /b 1
)

REM Activate it and install requirements
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt

REM Create aetherdb.bat CLI launcher to always use python -m aetherdb
echo @echo off > aetherdb.bat
echo call %%~dp0.venv\Scripts\activate.bat >> aetherdb.bat
echo python -m aetherdb %%* >> aetherdb.bat

echo.
echo Install complete. Run:
echo    aetherdb
echo Or, from your project directory, just run:
echo    python -m aetherdb
