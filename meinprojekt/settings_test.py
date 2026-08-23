"""Schnelle Testeinstellungen - optional, nicht die Wahrheit.

Die Wahrheit ist der Lauf OHNE Flag:

    docker compose exec django-dev python manage.py test fitness --noinput

Der geht durch die echte Migrationskette und ist damit die Variante, die
beim Django-Upgrade zaehlt: sie prueft mit, dass `migrate` von null
durchlaeuft und die Stammdaten korrekt entstehen.

Fuers Zwischendurch - wenn man dieselbe Datei zum zehnten Mal laufen
laesst - gibt es die schnelle Variante:

    docker compose exec django-dev python manage.py test fitness \
        --settings=meinprojekt.settings_test --noinput

Sie unterscheidet sich nur im Passwort-Hasher. Vor einem Commit und vor
jedem Upgrade-Schritt bitte den Lauf ohne Flag nehmen.

Geschichte
----------
Frueher schaltete diese Datei zusaetzlich die Migrationen ab
(`MIGRATION_MODULES`), weil `0006_update_default_progressions` die
Startprogressionen ueber feste Primaerschluessel suchte und `migrate` auf
einer frischen Datenbank deshalb abbrach. Das ist seit
`0009_seed_exercises_and_progressions` behoben - die Abschaltung ist
ersatzlos entfallen.
"""

from meinprojekt.settings import *  # noqa: F401,F403

# Der einzige Unterschied zum Normalbetrieb: MD5 statt PBKDF2. Die Tests
# pruefen keine Passwort-Sicherheit, und das Hashen dominiert sonst die
# Laufzeit jedes Tests, der einen Nutzer anlegt.
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]
