@echo off
REM Setup script for Windows systems

echo Setting up Kiro Backend Civic Assistant...

REM Check Python version
python --version | findstr /C:"3.11" >nul
if errorlevel 1 (
    echo Error: Python 3.11 is required but not found.
    echo Please install Python 3.11 and try again.
    exit /b 1
)

echo Python 3.11 found.

REM Create virtual environment
echo Creating virtual environment...
python -m venv venv

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
echo Installing dependencies...
pip install -r requirements-dev.txt

echo.
echo Setup complete!
echo.
echo To activate the virtual environment in the future, run:
echo   venv\Scripts\activate.bat
echo.
echo To run tests:
echo   pytest tests/
echo.
