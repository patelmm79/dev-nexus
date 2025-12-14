@echo off
REM Auth Proxy Setup Script for Windows

echo Setting up Authentication Proxy...

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed. Please install Python 3.8 or higher.
    exit /b 1
)

echo Python found

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install --upgrade pip
pip install -r requirements.txt

REM Create .env if it doesn't exist
if not exist ".env" (
    echo Creating .env file from template...
    copy .env.example .env
    echo Please edit .env with your configuration
) else (
    echo .env file already exists
)

REM Check for service account file
if not exist "service-account.json" (
    echo.
    echo WARNING: service-account.json not found
    echo.
    echo To create a service account:
    echo   1. Go to Google Cloud Console
    echo   2. IAM ^& Admin ^> Service Accounts
    echo   3. Create new service account
    echo   4. Download JSON key as 'service-account.json'
    echo.
) else (
    echo service-account.json found
)

echo.
echo Setup complete!
echo.
echo Next steps:
echo   1. Edit .env with your configuration
echo   2. Ensure service-account.json is in this directory
echo   3. Run: python server.py
echo.

pause
