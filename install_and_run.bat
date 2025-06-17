@echo off
REM ==================================================
REM Automatic installation and launch of the DDS application
REM ==================================================

echo.
echo [1/6] Checking the installed Python...
python --version
if %errorlevel% neq 0 (
    echo Error: Python is not installed or added to the PATH
    echo Download Python from https://www.python.org/downloads/
    pause
    exit
)

echo.
echo [2/6] Creating a virtual environment...
python -m venv venv
if %errorlevel% neq 0 (
    echo Error when creating a virtual environment
    pause
    exit
)

echo.
echo [3/6] Activation of the virtual environment...
call venv\Scripts\activate

echo.
echo [4/6] Installing dependencies...
pip install django

echo.
echo [5/6] Applying database migrations...
python manage.py migrate

echo.
echo [6/6] Starting the server...
echo ==================================================
echo The application is available at: http://127.0.0.1:8000
echo Stopping the server: CTRL+C
echo ==================================================
python manage.py runserver