import re
import json
import time
import requests
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.utils.text import slugify
from geo.models import Continent, Country, Clue

BASE_URL = 'https://learnablemeta.com'

CONTINENT_MAP = {
    'Europe':        ('Europa',       'europe'),
    'Asia':          ('Asien',        'asia'),
    'Africa':        ('Afrika',       'africa'),
    'South America': ('Südamerika',   'south-america'),
    'North America': ('Nordamerika',  'north-america'),
    'Oceania':       ('Ozeanien',     'oceania'),
    'World':          None,
}

# Whitelist of valid country names (all GeoGuessr-relevant countries)
VALID_COUNTRIES = {
    'Afghanistan', 'Albania', 'Algeria', 'Andorra', 'Angola', 'Argentina', 'Armenia',
    'Australia', 'Austria', 'Azerbaijan', 'Bahrain', 'Bangladesh', 'Belarus', 'Belgium',
    'Bhutan', 'Bolivia', 'Bosnia', 'Bosnia and Herzegovina', 'Botswana', 'Brazil',
    'Bulgaria', 'Cambodia', 'Cameroon', 'Canada', 'Chile', 'China', 'Colombia',
    'Croatia', 'Cuba', 'Curaçao', 'Cyprus', 'Czechia', 'Czech Republic',
    'Denmark', 'Dominican Republic', 'Ecuador', 'Egypt', 'El Salvador', 'Estonia',
    'Ethiopia', 'Faroe Islands', 'Finland', 'France', 'Georgia', 'Germany', 'Ghana',
    'Gibraltar', 'Greece', 'Greenland', 'Guatemala', 'Honduras', 'Hungary',
    'Iceland', 'India', 'Indonesia', 'Iran', 'Iraq', 'Ireland', 'Israel',
    'Italy', 'Japan', 'Jordan', 'Kazakhstan', 'Kenya', 'Kosovo', 'Kuwait',
    'Kyrgyzstan', 'Laos', 'Latvia', 'Lebanon', 'Lesotho', 'Lithuania', 'Luxembourg',
    'Madagascar', 'Malaysia', 'Malta', 'Mexico', 'Moldova', 'Mongolia', 'Montenegro',
    'Morocco', 'Mozambique', 'Myanmar', 'Namibia', 'Nepal', 'Netherlands',
    'New Zealand', 'Nicaragua', 'Nigeria', 'North Macedonia', 'Norway', 'Oman',
    'Pakistan', 'Palestine', 'Panama', 'Paraguay', 'Peru', 'Philippines', 'Poland',
    'Portugal', 'Qatar', 'Romania', 'Russia', 'Rwanda', 'Saudi Arabia', 'Senegal',
    'Serbia', 'Singapore', 'Slovakia', 'Slovenia', 'South Africa', 'South Korea',
    'Spain', 'Sri Lanka', 'Eswatini', 'Swaziland', 'Sweden', 'Switzerland',
    'Taiwan', 'Tajikistan', 'Tanzania', 'Thailand', 'Tunisia', 'Turkey', 'Türkiye',
    'Turkmenistan', 'Uganda', 'Ukraine', 'United Arab Emirates', 'United Kingdom',
    'United States', 'Uruguay', 'Uzbekistan', 'Venezuela', 'Vietnam', 'West Bank',
    'Isle of Man', 'Jersey', 'Guernsey', 'Azores', 'Madeira', 'Canary Islands',
    'San Marino', 'Monaco', 'Liechtenstein', 'Vatican', 'Kosovo',
    'Åland', 'Aaland', 'Aland',
}

CATEGORY_KEYWORDS = {
    'infrastructure': ['bollard', 'pole', 'tower', 'cable', 'electricity', 'power',
                       'antenna', 'guardrail', 'barrier', 'road sign', 'chevron', 'lamp'],
    'signs':          ['sign', 'suffix', 'writing', 'text', 'language', 'script',
                       'alphabet', 'word for', 'letters', 'spelling'],
    'plates':         ['plate', 'license plate', 'number plate', 'license'],
    'car':            ['car', 'vehicle', 'auto', 'bus', 'truck', 'taxi'],
    'vegetation':     ['tree', 'plant', 'vegetation', 'grass', 'forest', 'palm', 'flora', 'crop'],
    'landscape':      ['landscape', 'terrain', 'mountain', 'coast', 'beach', 'desert',
                       'river', 'lake', 'soil', 'rifts', 'vibes', 'lines'],
}

def guess_category(clue_name):
    name_lower = clue_name.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in name_lower:
                return category
    return 'other'

def fetch_page(url, retries=3):
    headers = {'User-Agent': 'Mozilla/5.0 (compatible; personal-geoguessr-trainer/1.0)'}
    for i in range(retries):
        try:
            r = requests.get(url, headers=headers, timeout=30)
            r.raise_for_status()
            return r.text
        except Exception as e:
            if i < retries - 1:
                time.sleep(2)
            else:
                raise e

def js_obj_to_json(raw):
    return re.sub(r'(?<=[{,])\s*([a-zA-Z_]\w*)\s*:', r'"\1":', raw)

def extract_maps_index(html):
    resolves = re.findall(
        r'__sveltekit_\w+\.resolve\(\d+,\s*\(\)\s*=>\s*(\[.*?\])\s*\)',
        html, re.DOTALL
    )
    for raw in resolves:
        try:
            data = json.loads(js_obj_to_json(raw))
            if isinstance(data, list) and data and isinstance(data[0], list):
                inner = data[0]
                if inner and isinstance(inner[0], dict) and 'geoguessrId' in inner[0]:
                    return inner
        except Exception:
            continue
    return []

def extract_meta_list(html):
    match = re.search(
        r'metaList:(\[.*?\]),\s*(?:mapName|isLoggedIn|totalLocations|personalMaps)',
        html, re.DOTALL
    )
    if match:
        try:
            return json.loads(js_obj_to_json(match.group(1)))
        except Exception:
            pass
    return []

def strip_html(text):
    clean = re.sub(r'<[^>]+>', ' ', text)
    for entity, repl in [('&nbsp;', ' '), ('&amp;', '&'), ('&lt;', '<'), ('&gt;', '>')]:
        clean = clean.replace(entity, repl)
    return re.sub(r'\s+', ' ', clean).strip()

def download_image(url, filename):
    headers = {'User-Agent': 'Mozilla/5.0 (compatible; personal-geoguessr-trainer/1.0)'}
    try:
        r = requests.get(url, headers=headers, timeout=30)
        r.raise_for_status()
        return ContentFile(r.content, name=filename)
    except Exception:
        return None

def is_valid_country(name):
    return name in VALID_COUNTRIES

class Command(BaseCommand):
    help = 'Import GeoGuessr clue data from LearnableMeta'

    def add_arguments(self, parser):
        parser.add_argument('--continent', type=str, help='Only import specific continent (e.g. Europe)')
        parser.add_argument('--no-images', action='store_true', help='Skip image downloads')
        parser.add_argument('--dry-run', action='store_true', help='Show what would be imported without saving')

    def handle(self, *args, **options):
        only_continent = options.get('continent')
        skip_images = options.get('no_images', False)
        dry_run = options.get('dry_run', False)

        self.stdout.write('Fetching maps index from LearnableMeta...')
        try:
            html = fetch_page(f'{BASE_URL}/maps')
        except Exception as e:
            self.stderr.write(f'Failed to fetch maps index: {e}')
            return

        all_maps = extract_maps_index(html)
        if not all_maps:
            self.stderr.write('Could not extract map data. Site structure may have changed.')
            return

        self.stdout.write(f'Found {len(all_maps)} maps')

        maps_by_region = {}
        for m in all_maps:
            region = m.get('regions', 'World')
            maps_by_region.setdefault(region, []).append(m)

        skipped_countries = 0
        for region_name, maps in maps_by_region.items():
            continent_info = CONTINENT_MAP.get(region_name)
            if continent_info is None:
                self.stdout.write(f'Skipping region: {region_name}')
                continue
            if only_continent and region_name.lower() != only_continent.lower():
                continue

            de_name, slug = continent_info
            self.stdout.write(self.style.SUCCESS(f'\n=== {de_name} ({len(maps)} maps) ==='))

            continent = None
            if not dry_run:
                continent, created = Continent.objects.get_or_create(
                    slug=slug,
                    defaults={'name': de_name, 'description': f'GeoGuessr-Tipps für {de_name}'}
                )
                if created:
                    self.stdout.write(f'  Created continent: {de_name}')

            for map_data in maps:
                geoguessr_id = map_data.get('geoguessrId')
                map_name = map_data.get('name', '')
                difficulty_raw = map_data.get('difficulty', 1)

                self.stdout.write(f'  Fetching map: {map_name}')
                try:
                    map_html = fetch_page(f'{BASE_URL}/maps/{geoguessr_id}')
                    time.sleep(0.5)
                except Exception as e:
                    self.stderr.write(f'    Failed: {e}')
                    continue

                meta_list = extract_meta_list(map_html)
                if not meta_list:
                    self.stdout.write(f'    No metas found, skipping')
                    continue

                self.stdout.write(f'    Found {len(meta_list)} clues')

                for meta in meta_list:
                    meta_name = meta.get('name', '')
                    if ' - ' not in meta_name:
                        continue

                    country_name, clue_title = meta_name.split(' - ', 1)
                    country_name = country_name.strip()
                    clue_title = clue_title.strip()

                    # Only import real countries
                    if not is_valid_country(country_name):
                        skipped_countries += 1
                        continue

                    country_slug = slugify(country_name)
                    description = strip_html(meta.get('note', ''))
                    images = meta.get('images', [])
                    category = guess_category(clue_title)

                    if dry_run:
                        self.stdout.write(f'    [DRY] {country_name} / {clue_title} ({category})')
                        continue

                    country, created = Country.objects.get_or_create(
                        slug=country_slug,
                        defaults={
                            'continent': continent,
                            'name': country_name,
                            'difficulty': min(max(difficulty_raw, 1), 3),
                            'short_summary': f'GeoGuessr-Tipps für {country_name}',
                        }
                    )
                    if created:
                        self.stdout.write(f'    + Country: {country_name}')

                    if Clue.objects.filter(country=country, title=clue_title).exists():
                        continue

                    clue = Clue(
                        country=country,
                        title=clue_title,
                        category=category,
                        description=description or f'{clue_title} in {country_name}',
                        importance=min(max(difficulty_raw, 1), 3),
                    )

                    if images and not skip_images:
                        img_url = images[0]
                        ext = img_url.split('.')[-1]
                        filename = f'{country_slug}_{slugify(clue_title)}.{ext}'
                        self.stdout.write(f'      Downloading: {filename}')
                        img_file = download_image(img_url, filename)
                        if img_file:
                            clue.image.save(filename, img_file, save=False)
                        time.sleep(0.3)

                    clue.save()

        if not dry_run:
            self.stdout.write(self.style.SUCCESS('\nImport complete!'))
            self.stdout.write(f'Skipped non-countries: {skipped_countries}')
            self.stdout.write(f'Continents: {Continent.objects.count()}')
            self.stdout.write(f'Countries:  {Country.objects.count()}')
            self.stdout.write(f'Clues:      {Clue.objects.count()}')
