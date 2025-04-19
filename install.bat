@echo off
setlocal enabledelayedexpansion

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

:: Determine the absolute path of the script's directory
set SCRIPT_DIR=%~dp0

:: Function to create an executable using PyInstaller
echo Activating virtual environment...
call "%SCRIPT_DIR%.venv\Scripts\activate.bat"

echo Installing PyInstaller if not already installed...
pip show pyinstaller >nul 2>&1 || pip install pyinstaller

echo Creating executable using PyInstaller...
pyinstaller --onefile --name aetherdb "%SCRIPT_DIR%aetherdb\__main__.py"

if not exist "%SCRIPT_DIR%dist\aetherdb.exe" (
    echo Failed to create the executable. Exiting...
    exit /b 1
)

echo Moving the executable to C:\Program Files\aetherdb...
if not exist "C:\Program Files\aetherdb" mkdir "C:\Program Files\aetherdb"
move /y "%SCRIPT_DIR%dist\aetherdb.exe" "C:\Program Files\aetherdb\aetherdb.exe"

:: Setting up AetherDB as a Windows service using NSSM
echo Setting up AetherDB as a Windows service...
if not exist "%SCRIPT_DIR%nssm.exe" (
    echo NSSM (Non-Sucking Service Manager) is required to set up the service.
    echo Please download NSSM and place nssm.exe in the script directory.
    exit /b 1
)

"%SCRIPT_DIR%nssm.exe" install AetherDB "C:\Program Files\aetherdb\aetherdb.exe"
"%SCRIPT_DIR%nssm.exe" set AetherDB Start SERVICE_AUTO_START

echo Starting the AetherDB service...
net start AetherDB

echo Installation complete. AetherDB is now set up as a Windows service.
echo You can manage the service with:
echo   nssm start AetherDB
echo   nssm stop AetherDB
echo   nssm restart AetherDB
echo   nssm remove AetherDB confirm

endlocal
