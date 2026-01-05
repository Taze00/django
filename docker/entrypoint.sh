#!/bin/bash
set -e

echo "=== Fitness Tracker Startup ==="

# Build React app if not already built
if [ ! -f "/code/static/fitness/index.html" ]; then
    echo "Building React app..."
    cd /code/fitness-frontend
    # Ensure .env.production is available for build
    if [ ! -f ".env.production" ]; then
        echo "VITE_API_URL=https://alex.volkmann.com/api/fitness" > .env.production
    fi
    npm install --legacy-peer-deps
    # Source environment variables and build
    set -a
    . ./.env.production
    set +a
    npm run build
    mkdir -p /code/static/fitness
    cp -r dist/* /code/static/fitness/
    # Copy the generated index.html to templates for Django to serve
    cp dist/index.html /code/templates/fitness.html
    echo "✓ React app built successfully!"
else
    echo "✓ React app already built"
fi

echo "Starting Django server..."
exec python3 manage.py runserver 0.0.0.0:80
