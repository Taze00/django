# Fitness App Build Workflow

## Quick Start

After making changes to `fitness-frontend/src/`, run:

```bash
./build-fitness.sh
```

This will:
1. Build the React app
2. Extract asset hashes from Vite build
3. Update the template with new hashes
4. Display instructions for committing

## Manual Steps (if not using script)

```bash
# 1. Build inside Docker
docker compose exec -T django-dev bash -c "cd /code/fitness-frontend && npm run build"

# 2. Copy to static/
docker compose exec -T django-dev bash -c "cp -r /code/fitness-frontend/dist /code/static/fitness"

# 3. Update template hashes manually (find new hashes in fitness-frontend/dist/index.html)
# Edit templates/fitness.html and update the script/link src/href

# 4. Commit
git add templates/fitness.html
git commit -m "Build: Update fitness app assets"
```

## Script Output Example

```
🔨 Building Fitness React App...
✅ Build successful
📦 Deploying to static/fitness/...
🔍 Updating templates/fitness.html...
   Script: index-d-6CqgMS.js
   CSS: index-DEfPXzG8.css
✅ All done!
📌 Now stage and commit:
   git add templates/fitness.html static/fitness/
   git commit -m 'Build: Update fitness app assets'
```

## Notes

- `static/fitness/` is gitignored (auto-generated)
- `templates/fitness.html` should always be committed with new hashes
- Always run `./build-fitness.sh` before `git add/commit` for frontend changes
