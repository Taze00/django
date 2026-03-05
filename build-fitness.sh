#!/bin/bash
set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}🔨 Building Fitness React App...${NC}"

# Build React inside Docker
if ! docker compose exec -T django-dev bash -c "cd /code/fitness-frontend && npm run build"; then
    echo -e "${RED}❌ Build failed!${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Build successful${NC}"

# Copy to static/
echo -e "${YELLOW}📦 Deploying to static/fitness/...${NC}"
docker compose exec -T django-dev bash -c "rm -rf /code/static/fitness && cp -r /code/fitness-frontend/dist /code/static/fitness"

# Extract hashes (handle underscores and dashes in hash)
SCRIPT_HASH=$(docker compose exec -T django-dev bash -c "grep -oP 'src=\"/assets/index-[a-zA-Z0-9_-]+\.js\"' /code/fitness-frontend/dist/index.html | grep -oP 'index-[a-zA-Z0-9_-]+\.js'" || echo "")
CSS_HASH=$(docker compose exec -T django-dev bash -c "grep -oP 'href=\"/assets/index-[a-zA-Z0-9_-]+\.css\"' /code/fitness-frontend/dist/index.html | grep -oP 'index-[a-zA-Z0-9_-]+\.css'" || echo "")

if [ -z "$SCRIPT_HASH" ] || [ -z "$CSS_HASH" ]; then
    echo -e "${RED}❌ Could not extract asset hashes!${NC}"
    exit 1
fi

echo -e "${YELLOW}🔍 Updating templates/fitness.html...${NC}"
echo "   Script: $SCRIPT_HASH"
echo "   CSS: $CSS_HASH"

# Update template with Python
docker compose exec -T django-dev bash -c "python3 << 'PYSCRIPT'
import re

script_hash = '$SCRIPT_HASH'
css_hash = '$CSS_HASH'

with open('/code/templates/fitness.html', 'r') as f:
    content = f.read()

content = re.sub(
    r'<script type=\"module\" src=\"/static/fitness/assets/index-[a-zA-Z0-9_-]+\.js\"></script>',
    f'<script type=\"module\" src=\"/static/fitness/assets/{script_hash}\"></script>',
    content
)

content = re.sub(
    r'<link rel=\"stylesheet\" href=\"/static/fitness/assets/index-[a-zA-Z0-9_-]+\.css\">',
    f'<link rel=\"stylesheet\" href=\"/static/fitness/assets/{css_hash}\">',
    content
)

with open('/code/templates/fitness.html', 'w') as f:
    f.write(content)

print('✅ fitness.html updated')
PYSCRIPT
"

echo -e "${GREEN}✅ All done!${NC}"
echo -e "${YELLOW}📌 Now stage and commit:${NC}"
echo "   git add templates/fitness.html static/fitness/"
echo "   git commit -m 'Build: Update fitness app assets'"
