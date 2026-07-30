"""Projekte fuer die Sektion "Was ich baue" auf der Startseite.

Steht bewusst in Python statt im Template: Reihenfolge und Inhalte
lassen sich so aendern, ohne Markup anzufassen.

`bild` ist ein Pfad unterhalb von STATIC_URL und wird im Template ueber
{% static %} aufgeloest. Fehlt die Datei oder ist das Feld leer, zeigt
die Karte einen gestalteten Fallback statt eines kaputten Bildes -
siehe .project-fallback in styles.css.

`status` ist optional. Nur Eintraege mit gesetztem Status bekommen ein
Badge.

`breit` markiert eine Karte, die sich ueber die volle Rasterbreite
spannt und Bild und Text nebeneinander zeigt. Das haengt an den Daten
und nicht an der Position im Raster, damit es beim Umsortieren oder
Ergaenzen nicht die falsche Karte trifft.
"""

PROJEKTE = [
    {
        "name": "CORVIS",
        "kategorie": "Fitness-App",
        "beschreibung": (
            "Calisthenics-App, die dein Niveau über einen Max-Test einstuft "
            "und dich hoch- oder runterstuft. Streaks brechen nicht, wenn du "
            "einen Tag pausierst."
        ),
        "tech": ["Django", "DRF", "PostgreSQL", "JWT", "React", "Vite", "Zustand"],
        "bild": "css/images/projects/corvis.png",
        "url": "/corvis/",
        "status": "",
        "breit": False,
    },
    {
        "name": "Aurelia",
        "kategorie": "Technik-Demo",
        "beschreibung": (
            "Übungsstück für WebGL: eine Marke erfunden, um eigene Shader und "
            "eine am Scrollverlauf hängende Choreografie zu bauen."
        ),
        "tech": ["Three.js", "WebGL", "GSAP", "ScrollTrigger", "Canvas"],
        "bild": "css/images/projects/aurelia.png",
        "url": "/aurelia/",
        "status": "",
        "breit": False,
    },
    {
        "name": "Festival-Seite",
        "kategorie": "Single Page",
        "beschreibung": (
            "Packliste fürs Festivalwochenende, entstanden weil ich jedes Mal "
            "was vergessen habe. Kategorien, Fortschritt, Filter – der Stand "
            "bleibt im Browser."
        ),
        "tech": ["HTML", "CSS", "Vanilla JS", "localStorage"],
        "bild": "css/images/projects/festival.png",
        "url": "/festival/",
        "status": "",
        "breit": False,
    },
    {
        "name": "Diese Seite",
        "kategorie": "Portfolio",
        "beschreibung": (
            "Alles an einem Ort: Clubs, Filme, Momente. Die Filmdaten kommen "
            "live aus meinem Letterboxd und von TMDB."
        ),
        "tech": ["Django", "PostgreSQL", "Vanilla JS", "TMDB API"],
        "bild": "css/images/projects/diese-seite.png",
        "url": "/",
        "status": "Im Umbau",
        "breit": True,
    },
]


def get_projekte():
    """Projektliste in der vorgesehenen Reihenfolge.

    Setzt zusaetzlich `hat_bild`: {% static %} baut eine URL auch fuer
    Dateien, die es nicht gibt - das Template koennte den Fallback sonst
    nicht erkennen. Geprueft wird gegen den Static-Finder, damit es in
    Entwicklung (STATICFILES_DIRS) wie in Produktion (STATIC_ROOT)
    funktioniert.
    """
    from django.contrib.staticfiles import finders

    projekte = []
    for projekt in PROJEKTE:
        eintrag = dict(projekt)
        pfad = eintrag.get("bild")
        eintrag["hat_bild"] = bool(pfad) and finders.find(pfad) is not None
        projekte.append(eintrag)
    return projekte
