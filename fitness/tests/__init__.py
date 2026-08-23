"""Testsuite fuer die CORVIS-Kernlogik.

Ausfuehren
----------
    docker compose exec django-dev python manage.py test fitness \
        --settings=meinprojekt.settings_test --noinput

Das `--settings=meinprojekt.settings_test` ist Pflicht, nicht Kosmetik:
mit den normalen Einstellungen scheitert schon das Anlegen der
Testdatenbank an der Datenmigration
`fitness/migrations/0006_update_default_progressions.py`. Die Begruendung
steht ausfuehrlich in `meinprojekt/settings_test.py`.

Inhalt
------
    test_calibration.py    Einstufung beim Onboarding (ohne Datenbank)
    test_streak.py         Serienberechnung (ohne Datenbank)
    test_level_changes.py  Auf- und Abstieg beim Workout-Abschluss
    test_api_smoke.py      Ein Lebenszeichen pro Endpunkt + Auth-Pflicht

Alle Tests halten das BESTEHENDE Verhalten fest - auch dort, wo es
fragwuerdig ist. Sie sind das Netz fuer das Django-Upgrade 4.2 -> 5.2,
kein Urteil ueber die Fachlogik. Wo etwas auffiel, steht es als
Kommentar am jeweiligen Test.
"""
