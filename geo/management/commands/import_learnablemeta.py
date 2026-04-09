import time
import requests
from html import unescape
from re import sub
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.utils.text import slugify
from geo.models import Continent, Country, Clue, Course


def html_to_text(html):
    """Strip HTML tags and unescape entities."""
    if not html:
        return ''
    text = sub(r'<[^>]+>', '', html)
    return unescape(text).strip()


def fetch_clues(map_id):
    url = f'https://learnablemeta.com/maps/{map_id}/__data.json'
    r = requests.get(url, headers={'Accept': 'application/json', 'User-Agent': 'Mozilla/5.0'}, timeout=30)
    r.raise_for_status()
    data = r.json()

    for node in data.get('nodes', []):
        if not isinstance(node, dict):
            continue
        items = node.get('data', [])
        if not isinstance(items, list) or not items:
            continue
        root = items[0]
        if not isinstance(root, dict) or 'metaList' not in root:
            continue

        def resolve(obj):
            out = {}
            for k, v in obj.items():
                rk = items[k] if isinstance(k, int) else k
                if isinstance(v, int) and v < len(items):
                    rv = items[v]
                    if isinstance(rv, list):
                        rv = [items[x] if isinstance(x, int) and x < len(items) else x for x in rv]
                    out[rk] = rv
                else:
                    out[rk] = v
            return out

        meta_indices = items[root['metaList']]
        clues = []
        for idx in meta_indices:
            obj = items[idx]
            if isinstance(obj, dict):
                clues.append(resolve(obj))
        return clues

    return []


def download_image(url, session):
    try:
        r = session.get(url, timeout=20)
        if r.ok:
            ct = r.headers.get('Content-Type', '')
            return r.content, ct
    except Exception:
        pass
    return None, None


class Command(BaseCommand):
    help = 'Import clues from LearnableMeta into a continent/course'

    def add_arguments(self, parser):
        parser.add_argument('map_id', help='LearnableMeta map ID')
        parser.add_argument('continent_slug', help='Continent slug (e.g. europe)')
        parser.add_argument('--course-name', default='Beginner Metas', help='Course name to create/update')
        parser.add_argument('--country', default='', help='Force all clues into this country name (for single-country maps)')
        parser.add_argument('--dry-run', action='store_true', help='Do not save anything')

    def handle(self, *args, **options):
        map_id = options['map_id']
        continent_slug = options['continent_slug']
        course_name = options['course_name']
        forced_country = options['country']
        dry_run = options['dry_run']

        try:
            continent = Continent.objects.get(slug=continent_slug)
        except Continent.DoesNotExist:
            self.stderr.write(f'Continent "{continent_slug}" not found')
            return

        if not dry_run:
            course, created = Course.objects.get_or_create(
                name=course_name,
                continent=continent,
                defaults={'description': f'Beginner meta clues for {continent.name}', 'difficulty': 1}
            )
            action = 'Created' if created else 'Using existing'
            self.stdout.write(f'{action} course: {course_name}')

        self.stdout.write(f'Fetching data from LearnableMeta map {map_id}...')
        raw_clues = fetch_clues(map_id)
        self.stdout.write(f'Found {len(raw_clues)} clues')

        session = requests.Session()
        session.headers['User-Agent'] = 'Mozilla/5.0'
        created_count = 0
        skipped_count = 0

        for raw in raw_clues:
            name = raw.get('name', '')
            if forced_country:
                country_name = forced_country
                title = name.strip()
            elif ' - ' not in name:
                self.stdout.write(f'  Skipping (no separator): {name}')
                skipped_count += 1
                continue
            else:
                country_name, title = name.split(' - ', 1)
                country_name = country_name.strip()
                title = title.strip()
            description = html_to_text(raw.get('note', ''))
            images = raw.get('images', [])
            image_url = images[0] if images else ''

            try:
                country = Country.objects.get(continent=continent, name=country_name)
            except Country.DoesNotExist:
                # Try finding in any continent
                try:
                    country = Country.objects.get(name=country_name)
                    self.stdout.write(f'  Found {country_name} in {country.continent.name} (not in {continent.name})')
                except Country.DoesNotExist:
                    self.stdout.write(f'  Country not found anywhere, skipping: {country_name}')
                    skipped_count += 1
                    continue

            if dry_run:
                self.stdout.write(f'  [DRY] {country_name} - {title} | image: {bool(image_url)}')
                created_count += 1
                continue

            # Skip if already exists
            if Clue.objects.filter(country=country, title=title).exists():
                self.stdout.write(f'  Already exists: {country_name} - {title}')
                continue

            clue = Clue(
                country=country,
                title=title,
                description=description,
                category='other',
                importance=2,
            )

            if image_url:
                content, ctype = download_image(image_url, session)
                if content:
                    ext = 'avif' if 'avif' in (ctype or image_url) else 'jpg'
                    fname = f'{slugify(country_name)}-{slugify(title[:50])}.{ext}'
                    clue.image.save(fname, ContentFile(content), save=False)
                time.sleep(0.2)

            clue.save()
            course.clues.add(clue)
            created_count += 1
            self.stdout.write(f'  + {country_name} - {title}')

        self.stdout.write(self.style.SUCCESS(
            f'\nDone! Created {created_count} clues, skipped {skipped_count}.'
        ))
