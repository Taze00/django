import re
import json
import time
import requests
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.utils.text import slugify
from geo.models import Country, Clue

PLONKIT_BASE = 'https://www.plonkit.net'
GITHUB_BASE = 'https://raw.githubusercontent.com/IngridAkeida/plonkit-data-api/main/data/countries'

# Step title → category mapping
def guess_category_from_step(step_title, item_text):
    title_lower = step_title.lower()
    text_lower = item_text.lower()
    combined = title_lower + ' ' + text_lower
    if any(k in combined for k in ['license plate', 'number plate', 'plate']):
        return 'plates'
    if any(k in combined for k in ['car', 'vehicle', 'google car', 'camera']):
        return 'car'
    if any(k in combined for k in ['sign', 'language', 'script', 'text', 'writing', 'alphabet', 'word']):
        return 'signs'
    if any(k in combined for k in ['vegetation', 'tree', 'plant', 'grass', 'forest', 'palm', 'flora']):
        return 'vegetation'
    if any(k in combined for k in ['landscape', 'terrain', 'soil', 'region', 'map', 'coverage', 'road']):
        return 'landscape'
    if any(k in combined for k in ['pole', 'bollard', 'infrastructure', 'power', 'electricity', 'antenna']):
        return 'infrastructure'
    return 'other'

def download_image(url, filename):
    headers = {'User-Agent': 'Mozilla/5.0 (compatible; personal-geoguessr-trainer/1.0)'}
    try:
        r = requests.get(url, headers=headers, timeout=30)
        r.raise_for_status()
        return ContentFile(r.content, name=filename)
    except Exception:
        return None

class Command(BaseCommand):
    help = 'Import Plonkit clue data from GitHub for African countries'

    def add_arguments(self, parser):
        parser.add_argument('--no-images', action='store_true', help='Skip image downloads')
        parser.add_argument('--country', type=str, help='Only import specific country slug (e.g. botswana)')

    def handle(self, *args, **options):
        skip_images = options.get('no_images', False)
        only_country = options.get('country')

        africa_countries = Country.objects.filter(continent__slug='africa')
        if only_country:
            africa_countries = africa_countries.filter(slug=only_country)

        self.stdout.write(f'Importing Plonkit data for {africa_countries.count()} African countries...\n')

        for country in africa_countries:
            # Build GitHub URL from country slug
            github_url = f'{GITHUB_BASE}/{country.slug}.json'
            self.stdout.write(f'Fetching: {country.flag_emoji} {country.name} ({github_url})')

            try:
                r = requests.get(github_url, timeout=15)
                if r.status_code == 404:
                    self.stdout.write(f'  Not found on GitHub, skipping')
                    continue
                r.raise_for_status()
                data = r.json()
            except Exception as e:
                self.stderr.write(f'  Error: {e}')
                continue

            steps = data.get('steps', [])
            clue_count = 0

            for step in steps:
                step_title = step.get('title', '')
                # Skip "Other resources" steps
                if 'resource' in step_title.lower() or 'other' in step_title.lower():
                    continue

                items = step.get('items', [])
                for i, item in enumerate(items):
                    text = item.get('text', '').strip()
                    image_path = item.get('image')
                    note = item.get('note', '')

                    # Skip items with no text and no image
                    if not text and not image_path:
                        continue

                    # Build title from step + index
                    clue_title = f'{step_title} #{i+1}'
                    if text:
                        # Use first sentence as title (max 80 chars)
                        first_sentence = text.split('.')[0].strip()
                        if len(first_sentence) <= 80:
                            clue_title = first_sentence
                        else:
                            clue_title = first_sentence[:77] + '...'

                    description = text
                    if note:
                        description += f'\n\nHinweis: {note}'

                    category = guess_category_from_step(step_title, text)
                    importance = 2  # default
                    if 'step 1' in step_title.lower():
                        importance = 3  # identifying clues = most important
                    elif 'spotlight' in step_title.lower():
                        importance = 1

                    # Skip duplicates
                    if Clue.objects.filter(country=country, title=clue_title).exists():
                        continue

                    clue = Clue(
                        country=country,
                        title=clue_title,
                        category=category,
                        description=description or clue_title,
                        importance=importance,
                        order=i,
                    )

                    # Download image
                    if image_path and not skip_images:
                        img_url = f'{PLONKIT_BASE}{image_path}'
                        ext = image_path.split('.')[-1].split('/')[0]
                        if not ext or len(ext) > 4:
                            ext = 'png'
                        filename = f'{country.slug}_{slugify(clue_title)[:40]}.{ext}'
                        img_file = download_image(img_url, filename)
                        if img_file:
                            clue.image.save(filename, img_file, save=False)
                        time.sleep(0.2)

                    clue.save()
                    clue_count += 1

            self.stdout.write(self.style.SUCCESS(f'  ✓ {clue_count} clues imported'))
            time.sleep(0.5)

        self.stdout.write(self.style.SUCCESS(f'\nDone! Total clues in DB: {Clue.objects.count()}'))
