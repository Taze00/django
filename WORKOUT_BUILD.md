# Workout App Build & Deploy Guide

## Quick Start

```bash
# 1. Start Docker containers
docker compose up -d

# 2. Build React app (inside running container)
docker compose exec -T django-dev bash -c "cd /code/workout-frontend && npm install --legacy-peer-deps && npm run build"

# 3. Copy build to static directory
docker compose exec -T django-dev bash -c "mkdir -p /code/static/workout && cp -r /code/workout-frontend/dist/* /code/static/workout/"

# 4. Restart Django
docker compose restart django-dev

# 5. Access at http://localhost:8000/workout/
```

## Backend API

All endpoints require JWT authentication (except `/api/workout/exercises/`).

### Available Endpoints
- `GET /api/workout/exercises/` — List all exercises with progressions (public)
- `GET /api/workout/user-progressions/` — User's current progression levels
- `GET /api/workout/workouts/current/` — Get or create active workout
- `POST /api/workout/workouts/{id}/add_set/` — Record a set
- `POST /api/workout/workouts/{id}/complete/` — Complete workout
- `GET /api/workout/last_performance/` — Last set values

## Database

### Current Data
- **Push-ups**: 7 progression levels, user starts at "Knee Push-ups" (level 3)
- **Pull-ups**: 7 progression levels, user starts at "Dead Hang" (level 1, time-based)

### Reset/Reseed

```bash
# Inside container
docker compose exec django-dev bash

# Delete and recreate database
python3 manage.py flush --no-input
python3 manage.py migrate
python3 manage.py seed_exercises

# Verify
python3 manage.py shell
>>> from workout.models import Exercise
>>> Exercise.objects.count()
2
>>> exit()
```

## Frontend Development

React app is in `workout-frontend/`

```bash
# Install dependencies
cd workout-frontend
npm install --legacy-peer-deps

# Development with Vite
npm run dev
# This starts dev server on http://localhost:5173

# Build for production
npm run build
# Output goes to dist/
```

### Key Files
- `src/App.jsx` — Main component (currently just demos exercise list)
- `src/main.jsx` — Vite entry point
- `src/index.css` — Global styles
- `vite.config.js` — Vite configuration

## Troubleshooting

**Problem:** React build fails with dependency errors
```
Solution: Use --legacy-peer-deps flag
npm install --legacy-peer-deps
```

**Problem:** Static files not loading after build
```
1. Verify dist/ exists: docker compose exec django-dev bash -c "ls -la /code/workout-frontend/dist/"
2. Copy to static/: docker compose exec django-dev bash -c "cp -r /code/workout-frontend/dist/* /code/static/workout/"
3. Restart Django: docker compose restart django-dev
```

**Problem:** Permission denied when deleting files
```
Always work inside the container:
docker compose exec django-dev bash
rm -rf /code/static/workout/
```

## Production Deployment

When ready to deploy to production:

1. Build React app
2. Commit changes to git (except /static/workout/ which is auto-generated)
3. Docker image will automatically build React on startup
4. Test all API endpoints with actual user data
