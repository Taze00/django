from django.conf import settings
from django.shortcuts import render

from films import kuratiert, letterboxd, projekte, tmdb


def index(request):
    # Filme und Serien holen ihre Poster von verschiedenen TMDB-Endpunkten.
    filme = tmdb.mit_postern(kuratiert.get_filme())
    serien = tmdb.mit_postern(
        kuratiert.get_serien(), id_feld='tmdb_tv_id', medium='tv'
    )

    # Ein gemeinsames Raster; die Gattung steckt als data-Attribut an der
    # Karte und wird clientseitig gefiltert.
    eintraege = filme + serien

    # Faellt Letterboxd aus, ist das hier eine leere Liste und die
    # Tagebuch-Zeile wird im Template uebersprungen. Die Seite bleibt
    # in jedem Fall bei 200.
    tagebuch = tmdb.mit_postern_gemischt(letterboxd.get_recent_entries())

    return render(request, 'index.html', {
        'projekte': projekte.get_projekte(),
        'eintraege': eintraege,
        'gattungen': kuratiert.get_gattungen(eintraege),
        'stimmungen': kuratiert.get_stimmungen(filme),
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

