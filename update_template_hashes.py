#!/usr/bin/env python3
"""
Auto-update CSS and JS hashes in templates/fitness.html after Vite build.
Reads from dist/ and updates the corresponding links in the template.
"""

import os
import re
import sys
from pathlib import Path

def find_hashes(dist_dir):
    """Find the current JS and CSS file hashes from dist/assets/"""
    hashes = {'js': None, 'css': None}
    assets_dir = Path(dist_dir) / 'assets'

    if not assets_dir.exists():
        print(f"❌ Assets directory not found: {assets_dir}")
        return None

    for file in assets_dir.iterdir():
        if file.name.startswith('index-') and file.suffix == '.js':
            hashes['js'] = file.name
        elif file.name.startswith('index-') and file.suffix == '.css':
            hashes['css'] = file.name

    return hashes if hashes['js'] and hashes['css'] else None

def update_template(template_path, hashes):
    """Update the CSS and JS hashes in templates/fitness.html"""

    if not os.path.exists(template_path):
        print(f"❌ Template not found: {template_path}")
        return False

    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content

    # Update JS hash - use a looser pattern to handle the hash format
    js_pattern = r'src="/static/fitness/assets/index-[A-Za-z0-9\-]*\.js'
    js_replacement = f'src="/static/fitness/assets/{hashes["js"]}'
    content = re.sub(js_pattern, js_replacement, content)

    # Update CSS hash
    css_pattern = r'href="/static/fitness/assets/index-[A-Za-z0-9\-]*\.css'
    css_replacement = f'href="/static/fitness/assets/{hashes["css"]}'
    content = re.sub(css_pattern, css_replacement, content)

    # Check if anything changed
    if content == original_content:
        print("ℹ️  Template hashes already up-to-date")
        return True

    # Write back
    with open(template_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✅ Updated JS hash to: {hashes['js']}")
    print(f"✅ Updated CSS hash to: {hashes['css']}")
    return True

def main():
    # Determine paths - try multiple locations since script may be run from different dirs
    script_dir = Path(__file__).parent.resolve()

    # If running from fitness-frontend, go up one level
    if script_dir.name == 'fitness-frontend':
        script_dir = script_dir.parent

    dist_dir = script_dir / 'fitness-frontend' / 'dist'
    template_path = script_dir / 'templates' / 'fitness.html'

    print("[update_template_hashes.py]")
    print(f"Script dir: {script_dir}")
    print(f"Looking for assets in: {dist_dir}")
    print(f"Template to update: {template_path}\n")

    # Find hashes
    hashes = find_hashes(dist_dir)
    if not hashes:
        print("❌ Failed to find JS or CSS hashes in dist/assets/")
        sys.exit(1)

    print(f"Found hashes:")
    print(f"  - JS:  {hashes['js']}")
    print(f"  - CSS: {hashes['css']}\n")

    # Update template
    if update_template(template_path, hashes):
        print("\n✨ Done!")
        sys.exit(0)
    else:
        print("\n❌ Failed to update template")
        sys.exit(1)

if __name__ == '__main__':
    main()
