@echo off
REM Activate the virtual environment if it exists, else create it

if exist "venv\Scripts\activate" (
    call venv\Scripts\activate
) else (
    echo Virtual environment 'venv' not found. Creating one...
    python -m venv venv
    call venv\Scripts\activate
    echo Virtual environment 'venv' created and activated.
)

REM Upgrade pip and install dependencies if requirements.txt exists
if exist "requirements.txt" (
    echo Installing dependencies...
    pip install --upgrade pip
    pip install -r requirements.txt
) else (
    echo No requirements.txt found. Skipping dependency installation.
)

REM Apply migrations
echo Applying migrations...
python manage.py migrate

REM Build Django Tailwind (if applicable)
if exist "theme\" (
    echo Building Django Tailwind...
    python manage.py tailwind install
    python manage.py tailwind build
) else (
    echo Tailwind theme directory not found. Skipping Tailwind build.
)

REM Collect static files
echo Collecting static files...
python manage.py collectstatic --noinput

REM Start Django development server
echo Starting Django development server...
python manage.py runserver 127.0.0.1:8000

pause
