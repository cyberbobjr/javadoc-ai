@echo off
REM Setup script for Javadoc AI Automation (Windows)

echo ======================================
echo Javadoc AI Automation - Setup Script
echo ======================================
echo.

REM Check Python
echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH.
    echo Please install Python 3.8 or higher from https://www.python.org/
    pause
    exit /b 1
)

python --version
echo.

REM Check Git
echo Checking Git installation...
git --version >nul 2>&1
if errorlevel 1 (
    echo Error: Git is not installed or not in PATH.
    echo Please install Git from https://git-scm.com/
    pause
    exit /b 1
)

git --version
echo.

REM Create virtual environment
echo Creating virtual environment...
if exist venv (
    echo Virtual environment already exists.
) else (
    python -m venv venv
    echo Virtual environment created.
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
echo.
echo Installing dependencies...
pip install -r requirements.txt

REM Copy config template if config doesn't exist
echo.
if not exist config.yaml (
    echo Creating config.yaml from template...
    copy config.yaml.template config.yaml
    echo Config file created. Please edit config.yaml with your settings.
) else (
    echo config.yaml already exists. Skipping.
)

echo.
echo ======================================
echo Setup Complete!
echo ======================================
echo.
echo Next steps:
echo 1. Edit config.yaml with your GitLab, LLM, and email settings
echo 2. Activate virtual environment: venv\Scripts\activate.bat
echo 3. Run the automation: python javadoc_automation.py
echo.
echo To schedule nightly runs, use Windows Task Scheduler:
echo - Open Task Scheduler
echo - Create Basic Task
echo - Set trigger to daily at desired time
echo - Set action to run: %CD%\venv\Scripts\python.exe %CD%\javadoc_automation.py
echo.
pause
