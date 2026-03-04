#!/bin/bash
set -e

echo "Building React app..."
cd /code/workout-frontend
npm install --legacy-peer-deps
npm run build

echo "Starting Django..."
cd /code
python3 manage.py migrate
python3 manage.py runserver 0.0.0.0:80
