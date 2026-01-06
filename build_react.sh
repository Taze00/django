#!/bin/bash
set -e

echo "Building React app..."
cd /media/docker/alex-django/fitness-frontend
npm install
npm run build

echo "Copying build output to static/fitness/"
rm -rf /media/docker/alex-django/static/fitness/*
cp -r dist/* /media/docker/alex-django/static/fitness/

echo "Done!"
ls -la /media/docker/alex-django/static/fitness/
