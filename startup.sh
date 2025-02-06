#!/bin/bash

# Stop the script on errors
set -e

echo "🔹 Checking if virtual environment exists..."
if [ ! -d "venv" ]; then
    echo "📌 Creating virtual environment..."
    python3 -m venv env
fi

echo "🔹 Activating virtual environment..."
source env/bin/activate

echo "📦 Installing dependencies..."
pip install -r requirements.txt

echo "🎨 Checking if Tailwind is installed..."
if ! python -c "import tailwind" 2>/dev/null; then
    echo "📌 Installing Tailwind..."
    python manage.py tailwind install
fi

echo "🎨 Building Tailwind CSS..."
python manage.py tailwind build

echo "📂 Collecting static files..."
python manage.py collectstatic --noinput

echo "🔄 Applying database migrations..."
python manage.py makemigrations
python manage.py migrate

echo "🚀 Starting Django server..."
python manage.py runserver