# -*- coding: utf-8 -*-
"""Breite High-Rank-Stichprobe: Rang belegt, Partien gestreut."""

from drafter import config
from drafter.models import Datenquelle
from drafter.models.collector import TrackedPlayer
from drafter.models.matches import Match, MatchPlayer, RawPayload
from drafter.services.collector import Collector
from drafter.services.stichprobe import HighRankStichprobe
from drafter.tests.basis import DrafterTest
from drafter.tests.fixture_helfer import BASIS


class StichprobeBasis(DrafterTest):
    def partie(self, spieler, nummer=0):
        """spieler: [(tag, rang, seite)]"""
        m = Match.objects.create(
            fingerprint=f"fp-broad-{nummer}", source=Datenquelle.API,
            played_at=BASIS, battle_type="soloRanked", is_ranked=True, winner_side="a",
        )
        for tag, rang, seite in spieler:
            MatchPlayer.objects.create(
                match=m, side=seite, brawler=self.brawler("gale"), brawler_name="gale",
                player_tag=tag, trophies=rang,
            )
        return m

    def spieler(self, tag, **extra):
        return TrackedPlayer.objects.create(tag=tag, **extra)


class HighRankStichprobeTest(StichprobeBasis):
    def test_nur_belegter_rang_zaehlt(self):
        self.partie([("#HOCH", 19, "a"), ("#NIEDRIG", 12, "b")])
        tags = [t for t, _ in HighRankStichprobe().belegte_kandidaten()]
        self.assertIn("#HOCH", tags)
        self.assertNotIn("#NIEDRIG", tags)

    def test_hoechster_belegter_rang_gilt(self):
        self.partie([("#A", 12, "a")], nummer=1)
        self.partie([("#A", 19, "a")], nummer=2)
        self.assertEqual(HighRankStichprobe().rang["#A"], 19)

    def test_nur_einer_je_partie_kommt_nach_vorn(self):
        self.partie([("#A", 20, "a"), ("#B", 19, "a"), ("#C", 18, "b")])
        reihenfolge = HighRankStichprobe().reihenfolge()
        self.assertEqual(reihenfolge[0], "#A", "höchster Rang zuerst")
        # B und C teilen sich die Partie mit A - sie rutschen ans Ende,
        # verschwinden aber nicht.
        self.assertEqual(set(reihenfolge), {"#A", "#B", "#C"})
        self.assertEqual(reihenfolge.index("#A"), 0)

    def test_verschiedene_partien_kommen_alle_nach_vorn(self):
        self.partie([("#A", 20, "a")], nummer=1)
        self.partie([("#B", 19, "a")], nummer=2)
        self.assertEqual(HighRankStichprobe().reihenfolge(), ["#A", "#B"])

    def test_keine_brawler_auswahl(self):
        """Der seltene Brawler spielt keine Rolle - anders als bei 'luecken'."""
        self.partie([("#SELTEN", 16, "a")], nummer=1)
        self.partie([("#HOCH", 21, "a")], nummer=2)
        self.assertEqual(HighRankStichprobe().reihenfolge()[0], "#HOCH")

    def test_fehlende_spieler_werden_ohne_netz_nachgetragen(self):
        self.partie([("#NEU", 19, "a")])
        stichprobe = HighRankStichprobe()
        self.assertEqual(stichprobe.fehlende_spieler(), ["#NEU"])
        stichprobe.nachtragen()
        self.assertTrue(TrackedPlayer.objects.filter(tag="#NEU").exists())

    def test_rangschwelle_ist_konfigurierbar(self):
        self.partie([("#MITTE", 14, "a")])
        self.assertEqual(HighRankStichprobe(min_rang=14).belegte_kandidaten()[0][0], "#MITTE")


class StrategieTest(StichprobeBasis):
    def test_collector_waehlt_den_hoechsten_offenen_rang(self):
        from unittest import mock
        self.partie([("#HOCH", 21, "a")], nummer=1)
        self.partie([("#MITTEL", 17, "a")], nummer=2)
        self.partie([("#NIEDRIG", 11, "a")], nummer=3)
        for tag in ("#HOCH", "#MITTEL", "#NIEDRIG"):
            self.spieler(tag, depth=1)
        collector = Collector(client=mock.Mock(einsatzbereit=True), strategie="broad_high_rank")
        self.assertEqual(collector._naechster(set()).tag, "#HOCH")
        self.assertEqual(collector._naechster({"#HOCH"}).tag, "#MITTEL")
        self.assertIsNone(collector._naechster({"#HOCH", "#MITTEL"}),
                          "ohne belegten Rang wird niemand geholt")


class HerkunftTest(StichprobeBasis):
    def test_eine_partie_kann_mehreren_strategien_gehoeren(self):
        m = self.partie([("#A", 19, "a")])
        for strategie in ("luecken", "broad_high_rank"):
            payload = RawPayload.objects.create(
                source=Datenquelle.API, format="x", reference=strategie,
                content_hash=f"hash-{strategie}", payload={}, sampling=strategie,
            )
            m.payloads.add(payload)
        self.assertEqual(m.sampling_quellen, ["broad_high_rank", "luecken"])
