#!/bin/bash
set -e

echo "Starting Django..."
cd /code
python3 manage.py migrate
python3 manage.py runserver 0.0.0.0:80
