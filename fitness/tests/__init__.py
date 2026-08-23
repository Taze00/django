"""Testsuite fuer die CORVIS-Kernlogik.

Ausfuehren
----------
    docker compose exec django-dev python manage.py test fitness --noinput

Das ist der Lauf, der zaehlt: er geht durch die echte Migrationskette
und prueft damit mit, dass `migrate` von null durchlaeuft und die
Stammdaten (3 Uebungen, 21 Progressionen) korrekt entstehen. Vor jedem
Commit und vor jedem Upgrade-Schritt diese Variante nehmen.

Fuers Zwischendurch gibt es eine schnellere, die sich nur im
Passwort-Hasher unterscheidet:

    ... manage.py test fitness --settings=meinprojekt.settings_test --noinput

Inhalt
------
    test_calibration.py    Einstufung beim Onboarding (ohne Datenbank)
    test_streak.py         Serienberechnung (ohne Datenbank)
    test_level_changes.py  Auf- und Abstieg beim Workout-Abschluss
    test_api_smoke.py      Ein Lebenszeichen pro Endpunkt + Auth-Pflicht

Die Testdatenbank bringt seit `0009_seed_exercises_and_progressions` die
drei echten Uebungen samt Progressionen mit. Tests, die Listen pruefen,
duerfen deshalb keine absoluten Anzahlen erwarten, sondern muessen auf
ihre eigenen Objekte filtern.

Alle Tests halten das BESTEHENDE Verhalten fest - auch dort, wo es
fragwuerdig ist. Sie sind das Netz fuer das Django-Upgrade 4.2 -> 5.2,
kein Urteil ueber die Fachlogik. Wo etwas auffiel, steht es als
Kommentar am jeweiligen Test.
"""
