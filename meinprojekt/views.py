from django.conf import settings
from django.shortcuts import render

from films import kuratiert, letterboxd, projekte, statistik, tmdb
from films.models import Film, normalisiere


def index(request):
    # Nur noch die fuenf kuratierten Kinofilme. Serien und Anime haben
    # die Startseite verlassen und stehen jetzt auf /filme/ (siehe
    # films.views.uebersicht) - die Daten sind dieselben geblieben.
    filme = tmdb.mit_postern(kuratiert.get_filme())

    # Faellt Letterboxd aus, ist das hier eine leere Liste und die
    # Tagebuch-Zeile wird im Template uebersprungen. Die Seite bleibt
    # in jedem Fall bei 200.
    tagebuch = tmdb.mit_postern_gemischt(letterboxd.get_recent_entries())

    # Empfehlungen: alles ab 3.5 aus dem Letterboxd-Bestand, absteigend.
    # Die Grenze lag bei 4.0 und liess 17 Filme uebrig - zu wenig fuer
    # ein Regal, durch das sich das Blaettern lohnt. Ab 3.5 sind es 40.
    #
    # Poster holt der Import nur fuer Filme ab einer Wertung
    # (`import_letterboxd --poster-ab`), nicht fuer alle 216. Fuer die
    # 3.5er sind sie da - wer die Grenze weiter senkt, muss vorher
    # nachsehen, sonst fuellt sich das Regal mit Platzhaltern.
    # Die fuenf kuratierten Filme haben alle 5.0 und stuenden sonst
    # gleich zweimal untereinander - einmal oben mit Text, einmal hier
    # ohne. Ausgeschlossen wird ueber normalisierten Titel und Jahr:
    # filme.json fuehrt Letterboxd-Slugs, die Datenbank boxd.it-URIs,
    # eine gemeinsame Kennung gibt es nicht.
    kuratierte = {
        (normalisiere(e.get('titel')), e.get('jahr')) for e in filme
    }
    empfehlungen = [
        f for f in Film.objects.filter(gesehen=True, wertung__gte=3.5)
                               .order_by('-wertung', 'titel')
        if (f.titel_normalisiert, f.jahr) not in kuratierte
    ]

    return render(request, 'index.html', {
        'projekte': projekte.get_projekte(),
        'statistik': statistik.hole_statistik(),
        'empfehlungen': empfehlungen,
        # Zaehler als fertiger Text - im Template waere das eine
        # unleserliche Filterkette.
        'empfehlungen_zaehler': f'{len(empfehlungen)} Filme ab 3,5',
        'filme': filme,
        'filme_zaehler': f'{len(filme)} Filme',
        'tagebuch': tagebuch,
        'letterboxd_url': letterboxd.get_profile_url(),
        'letterboxd_user': settings.LETTERBOXD_USERNAME,
    })

def freundin_page(request):
    return render(request, "schubi.html")

def impressum(request):
    return render(request, 'impressum.html')

def fitness_page(request):
    return render(request, 'fitness.html')

def festival_page(request):
    return render(request, 'festival.html')

def skills_page(request):
    return render(request, 'skills.html')

def fitness_landing_page(request):
    return render(request, 'fitness-landing.html')

def not_found(request, exception=None):
    return render(request, '404.html', status=404)

def aurelia_demo(request):
    return render(request, 'aurelia-demo.html')

