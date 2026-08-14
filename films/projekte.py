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
        # JPEG statt PNG: die Vorlage ist ein Screenshot mit weichen
        # Farbverlaeufen, als PNG blieb sie auch mit reduzierter Palette
        # ueber 230 KB. Als JPEG q92 sind es 73 KB bei gleicher Wirkung.
        "bild": "css/images/projects/corvis.jpg",
        "url": "/corvis/",
        "status": "",
        "breit": True,
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
        # Ebenfalls breit: als schmale Karte stand links ein kleines
        # Farbfeld und rechts daneben blieb die halbe Reihe leer. Zwei
        # Karten im selben Format untereinander lesen sich als Paar.
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
