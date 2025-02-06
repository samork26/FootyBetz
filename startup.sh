#!/bin/bash

# Set script to exit on any errors
set -e

echo "Starting setup script..."

# Check if Python is installed
if ! command -v python3 &>/dev/null; then
    echo "Python3 is not installed. Please install Python3 and try again."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Install Tailwind dependencies (if applicable)
if [ -f "package.json" ]; then
    echo "Installing Node.js dependencies..."
    npm install
    echo "Building Tailwind CSS..."
    npm run build
fi

# Apply database migrations
echo "Running database migrations..."
python manage.py migrate

# Start Django server
echo "Starting Django development server..."
python manage.py runserver

echo "Setup complete. Your Django app is running!"
