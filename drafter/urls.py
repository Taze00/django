"""URLs des Drafters, eingehaengt unter /draft/.

Anmeldung: der Drafter bringt die einzige Session-Login-Seite des
Projekts mit (CORVIS benutzt JWT, die Portfolio-Seiten brauchen keine).
Sie steht hier und nicht im Projektkern, weil sie nur hierfuer
existiert - und benutzt Djangos eigene LoginView, damit weder
Passwortpruefung noch Session-Handling neu geschrieben werden.
"""

from django.contrib.auth import views as auth_views
from django.urls import path

from drafter import views
from drafter.views.challenger import challenger, challenger_recommend, challenger_snapshots, challenger_result, challenger_info

app_name = "drafter"

urlpatterns = [
    path("api/challenger/info/", challenger_info, name="api_challenger_info"),
    path("api/challenger/snapshots/", challenger_snapshots, name="api_challenger_snapshots"),
    path("api/challenger/snapshots/<int:pk>/result/", challenger_result, name="api_challenger_result"),
    path("challenger/", challenger, name="challenger"),
    path("api/challenger/", challenger_recommend, name="api_challenger"),
    path("", views.draft, name="draft"),
    path("meine-brawler/", views.meine_brawler, name="meine_brawler"),

    path("login/", auth_views.LoginView.as_view(
        template_name="drafter/login.html",
        redirect_authenticated_user=True,
    ), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),

    # JSON-Schnittstelle
    path("api/katalog/", views.katalog, name="api_katalog"),
    path("api/recommend/", views.empfehlen, name="api_recommend"),
    path("api/final-analysis/", views.endanalyse, name="api_final_analysis"),
    path("api/detail/", views.detail, name="api_detail"),
    path("api/confidence/", views.confidence_speichern, name="api_confidence"),
]
