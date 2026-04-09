from django.db import models
from django.contrib.auth.models import User


class Continent(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(help_text="Makro-Tipps: Wie erkennt man diesen Kontinent?")
    cover_image = models.ImageField(upload_to='geo/continents/', blank=True, null=True)
    drive_side_note = models.CharField(
        max_length=255, blank=True,
        help_text="z.B. 'Gemischt – Linksverkehr in ZA, KE, ...'"
    )
    name_de = models.CharField(max_length=100, blank=True, help_text="Deutscher Name")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class Country(models.Model):
    DRIVE_SIDE_CHOICES = [
        ('left', 'Linksverkehr'),
        ('right', 'Rechtsverkehr'),
    ]

    continent = models.ForeignKey(Continent, on_delete=models.CASCADE, related_name='countries')
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    flag_emoji = models.CharField(max_length=10, blank=True)
    map_image = models.ImageField(upload_to="geo/countries/", blank=True, null=True)
    drive_side = models.CharField(max_length=5, choices=DRIVE_SIDE_CHOICES, default='right')
    difficulty = models.IntegerField(
        default=1,
        choices=[(1, '★ Leicht'), (2, '★★ Mittel'), (3, '★★★ Schwer')]
    )
    short_summary = models.TextField(blank=True)
    domain = models.CharField(max_length=50, blank=True, help_text="Google domain z.B. .de, .co.uk")
    capital = models.CharField(max_length=100, blank=True, help_text="Hauptstadt")
    name_de = models.CharField(max_length=100, blank=True, help_text="Deutscher Name")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']
        verbose_name_plural = 'Countries'

    def __str__(self):
        return f"{self.flag_emoji} {self.name}"


class Clue(models.Model):
    CATEGORY_CHOICES = [
        ('car', 'Fahrzeuge'),
        ('infrastructure', 'Infrastruktur'),
        ('vegetation', 'Vegetation'),
        ('signs', 'Schilder'),
        ('landscape', 'Landschaft'),
        ('plates', 'Nummernschilder'),
        ('other', 'Sonstiges'),
    ]

    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='clues')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    title = models.CharField(max_length=200)
    description = models.TextField(help_text="Warum ist das ein eindeutiger Hinweis?")
    image = models.ImageField(upload_to='geo/clues/')
    importance = models.IntegerField(
        default=1,
        choices=[(1, '★ Selten'), (2, '★★ Wichtig'), (3, '★★★ Entscheidend')]
    )
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'importance']

    def __str__(self):
        return f"{self.country.name} – {self.title}"


class UserProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='geo_progress')
    clue = models.ForeignKey(Clue, on_delete=models.CASCADE, related_name='user_progress')
    known = models.BooleanField(default=False)
    seen_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'clue')

    def __str__(self):
        status = '✓' if self.known else '✗'
        return f"{self.user.username} – {self.clue.title} {status}"


class CourseCardProgress(models.Model):
    """Tracks stage/streak progress for country cards in a course (flags/domains/capitals)."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='course_card_progress')
    course = models.ForeignKey('Course', on_delete=models.CASCADE, related_name='card_progress')
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='course_card_progress')
    stage = models.IntegerField(default=1)        # 1, 2, or 3 (learned)
    streak = models.IntegerField(default=0)
    learned = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'course', 'country')

    def __str__(self):
        return f"{self.user.username} – {self.course.name} – {self.country.name}"


class Course(models.Model):
    continent = models.ForeignKey(Continent, on_delete=models.CASCADE, related_name='courses')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    difficulty = models.IntegerField(
        default=1,
        choices=[(1, 'Einsteiger'), (2, 'Fortgeschritten'), (3, 'Experte')]
    )
    COURSE_TYPE_CHOICES = [
        ('clues', 'Clue Karten'),
        ('flags', 'Flaggen'),
        ('domains', 'Domains'),
        ('capitals', 'Hauptstädte'),
    ]
    course_type = models.CharField(max_length=20, choices=COURSE_TYPE_CHOICES, default='clues')
    clues = models.ManyToManyField(Clue, related_name='courses', blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'difficulty']

    def __str__(self):
        return self.name
