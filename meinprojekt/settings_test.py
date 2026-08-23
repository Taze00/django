"""Testeinstellungen.

Aufruf:
    python manage.py test --settings=meinprojekt.settings_test

Warum es diese Datei gibt
-------------------------
`fitness/migrations/0006_update_default_progressions.py` ist eine
Datenmigration, die drei Progressionen ueber feste Primaerschluessel
sucht:

    push  = Progression.objects.get(id=4)
    pull  = Progression.objects.get(id=8)
    plank = Progression.objects.get(id=17)

Die Progressionen selbst legt aber KEINE Migration an - sie wurden
einmal von Hand in die Produktionsdatenbank eingespielt. Auf einer
frischen Datenbank ist die Tabelle leer, `get()` wirft
`Progression.DoesNotExist`, und `migrate` bricht ab.

Die Produktionsdatenbank ist davon nicht betroffen: dort ist 0006
laengst angewendet und die 21 Progressionen existieren. Betroffen ist
jede Datenbank, die bei null anfaengt - also die Testdatenbank, eine
Wiederherstellung und jede neue Umgebung.

Solange das nicht behoben ist, bauen die Tests das fitness-Schema
direkt aus den Modellen statt aus der Migrationskette. Das ist
gaengige Praxis (und schneller), umgeht hier aber eben auch einen
echten Defekt - deshalb steht er hier ausdruecklich beschrieben und
nicht nur im Commit.

Ist 0006 repariert (z.B. `filter(...).update(...)` statt `get(...)`,
oder besser: das Anlegen der Progressionen selbst als Datenmigration),
kann `MIGRATION_MODULES` hier ersatzlos entfallen.
"""

from meinprojekt.settings import *  # noqa: F401,F403

# Schema aus den Modellen bauen statt aus den Migrationen.
#
# Nur fuer fitness abzuschalten reicht nicht: `migrate` legt die
# Tabellen unmigrierter Apps VOR den Migrationen an, und der
# Fremdschluessel von fitness auf auth_user liefe dann ins Leere
# ("relation auth_user does not exist"). Also alles oder nichts.
class _OhneMigrationen:
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return None


MIGRATION_MODULES = _OhneMigrationen()

# Schnellerer Hasher - die Tests pruefen keine Passwort-Sicherheit.
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]
