"""Gemeinsame Grundlage der Drafter-Tests.

Die Tests laufen gegen den echten Demo-Datensatz statt gegen erfundene
Testobjekte. Grund: der Seed ist Teil der Auslieferung. Waere er kaputt
oder widerspruechlich, muessten die Tests das merken - mit
handgebauten Miniaturbrawlern wuerden sie an ihm vorbeipruefen.
"""

from django.core.management import call_command
from django.test import TestCase

from drafter.models import BrawlMap, Brawler
from drafter.services.context import DraftContext
from drafter.services.draft_engine import DraftEngine


class DrafterTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_brawl_data", verbosity=0)

    # --- Kleine Helfer --------------------------------------------------
    def brawler(self, slug):
        return Brawler.objects.get(slug=slug)

    def karte(self, slug="hart-rock-mine"):
        return BrawlMap.objects.select_related("game_mode").get(slug=slug)

    def context(self, karte="hart-rock-mine", eigene=(), gegner=(), bans=(),
                first_pick=True, personal=None):
        k = self.karte(karte)
        return DraftContext(
            game_mode=k.game_mode,
            brawl_map=k,
            own_picks=tuple(self.brawler(s) for s in eigene),
            enemy_picks=tuple(self.brawler(s) for s in gegner),
            bans=tuple(self.brawler(s) for s in bans),
            own_team_first_pick=first_pick,
            personal=personal or {},
        )

    def engine(self, **kwargs):
        return DraftEngine(self.context(**kwargs))

    def rang(self, empfehlungen, slug):
        """Platz eines Brawlers in der Empfehlungsliste (1-basiert)."""
        for i, e in enumerate(empfehlungen, 1):
            if e.brawler.slug == slug:
                return i
        return None

    def score(self, empfehlungen, slug):
        for e in empfehlungen:
            if e.brawler.slug == slug:
                return e.score
        return None
