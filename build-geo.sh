#!/bin/bash
set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}🔨 Building GeoGuessr React App...${NC}"

if ! docker compose exec -T django-dev bash -c "cd /code/geo-frontend && npm run build"; then
    echo -e "${RED}❌ Build failed!${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Build successful${NC}"

# Extract hashes from the built index.html
SCRIPT_FILE=$(docker compose exec -T django-dev bash -c "grep -oP 'src=\"/static/geo/assets/index-[a-zA-Z0-9_-]+\.js\"' /code/static/geo/index.html | grep -oP 'index-[a-zA-Z0-9_-]+\.js'" || echo "")
CSS_FILE=$(docker compose exec -T django-dev bash -c "grep -oP 'href=\"/static/geo/assets/index-[a-zA-Z0-9_-]+\.css\"' /code/static/geo/index.html | grep -oP 'index-[a-zA-Z0-9_-]+\.css'" || echo "")

if [ -z "$SCRIPT_FILE" ] || [ -z "$CSS_FILE" ]; then
    echo -e "${RED}❌ Could not extract asset hashes!${NC}"
    exit 1
fi

echo -e "${YELLOW}🔍 Updating templates/geo.html...${NC}"
echo "   Script: $SCRIPT_FILE"
echo "   CSS: $CSS_FILE"

docker compose exec -T django-dev bash -c "python3 << 'PYSCRIPT'
script_file = '$SCRIPT_FILE'
css_file = '$CSS_FILE'

content = '''<!DOCTYPE html>
<html lang=\"de\">
<head>
    <meta charset=\"UTF-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
    <title>ClueLess</title>
    <link rel=\"icon\" type=\"image/svg+xml\" href=\"/static/geo/favicon.svg\">
    <link rel=\"apple-touch-icon\" href=\"/static/geo/apple-touch-icon.png\">
    <meta name=\"theme-color\" content=\"#030712\">
    <link rel=\"stylesheet\" href=\"/static/geo/assets/''' + css_file + '''\">
</head>
<body>
    <div id=\"root\"></div>
    <script type=\"module\" src=\"/static/geo/assets/''' + script_file + '''\"></script>
</body>
</html>'''

with open('/code/templates/geo.html', 'w') as f:
    f.write(content)

print('✅ geo.html updated')
PYSCRIPT
"

echo -e "${GREEN}✅ All done!${NC}"
echo -e "${YELLOW}📌 Now stage and commit:${NC}"
echo "   git add templates/geo.html static/geo/"
echo "   git commit -m 'Build: Update geo app assets'"
