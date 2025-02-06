#!/bin/bash

# Activate the virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "Virtual environment 'venv' not found. Creating one..."
    python3 -m venv venv
    source venv/bin/activate
    echo "Virtual environment 'venv' created and activated."
fi

# Upgrade pip and install dependencies if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo "Installing dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
else
    echo "No requirements.txt found. Skipping dependency installation."
fi

# Apply migrations
echo "Applying migrations..."
python manage.py migrate

# Build Django Tailwind (if applicable)
if [ -d "theme" ]; then
    echo "Building Django Tailwind..."
    python manage.py tailwind install
    python manage.py tailwind build
else
    echo "Tailwind theme directory not found. Skipping Tailwind build."
fi

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Start Django development server
echo "Starting Django development server..."
python manage.py runserver 127.0.0.1:8000
