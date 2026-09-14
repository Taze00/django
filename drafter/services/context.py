"""DraftContext - der Zustand eines Drafts als ein Objekt.

Ohne dieses Objekt reicht jede Funktion der Engine zwanzig Parameter
weiter und jede Erweiterung aendert zwanzig Signaturen. Der Context ist
bewusst **unveraenderlich gedacht**: er beschreibt einen Moment im
Draft. Wer den naechsten Moment braucht, baut mit `mit_pick()` einen
neuen - das macht Simulationen ("was waere, wenn wir X nehmen")
nebenbei moeglich und ist die Grundlage fuer spaeteres Backtesting.
"""

from dataclasses import dataclass, field, replace

from drafter import config


class DraftFehler(ValueError):
    """Der Draftzustand ergibt keinen Sinn - z.B. ein Brawler doppelt."""


# Standard-Reihenfolge im Ranked-Draft: 1-2-2-1.
# Das Team mit First Pick nimmt Slot 0, 3 und 4; das andere 1, 2 und 5.
# Der letzte Pick des gesamten Drafts gehoert damit immer dem Team OHNE
# First Pick - deshalb ist "First Pick haben" nicht eindeutig besser.
PICK_REIHENFOLGE = ("first", "second", "second", "first", "first", "second")
PICKS_JE_TEAM = 3
BANS_JE_TEAM = 3


@dataclass(frozen=True)
class DraftContext:
    """Alles, was an einem Punkt des Drafts bekannt ist.

    `own_picks` und `enemy_picks` sind Brawler-Objekte in Pickreihenfolge.
    `personal` bildet Brawler-ID auf eine Sicherheit 0-100 ab - sie kommt
    aus der Datenbank (angemeldet) oder aus der Session (Gast), die
    Engine unterscheidet das nicht.
    """

    game_mode: object = None
    brawl_map: object = None
    own_picks: tuple = ()
    enemy_picks: tuple = ()
    bans: tuple = ()
    own_team_first_pick: bool = True
    patch: object = None
    rank_pool: str = config.RANG_POOL_STANDARD
    user: object = None
    personal: dict = field(default_factory=dict)

    # --- Abgeleiteter Zustand -------------------------------------------
    @property
    def picks_gesamt(self):
        return len(self.own_picks) + len(self.enemy_picks)

    @property
    def unsere_restpicks(self):
        return max(0, PICKS_JE_TEAM - len(self.own_picks))

    @property
    def gegner_restpicks(self):
        return max(0, PICKS_JE_TEAM - len(self.enemy_picks))

    @property
    def draft_fertig(self):
        return self.unsere_restpicks == 0 and self.gegner_restpicks == 0

    @property
    def unser_slot(self):
        """Welcher Platz der Standardreihenfolge uns gehoert."""
        return "first" if self.own_team_first_pick else "second"

    @property
    def am_zug(self):
        """Wer laut Reihenfolge als naechstes waehlt: 'own', 'enemy' oder None.

        Abgeleitet aus der Anzahl bereits getaetigter Picks, nicht aus
        einem gespeicherten Zeiger - dadurch kann die Oberflaeche Picks
        auch nachtraeglich korrigieren, ohne dass der Zustand kaputtgeht.
        """
        if self.draft_fertig:
            return None
        n = self.picks_gesamt
        if n >= len(PICK_REIHENFOLGE):
            return "own" if self.unsere_restpicks else "enemy"
        dran = PICK_REIHENFOLGE[n]
        return "own" if dran == self.unser_slot else "enemy"

    @property
    def phase(self):
        """Die Draft-Phase - sie entscheidet ueber die Gewichte.

        Nach Informationsstand bestimmt, nicht nach Slotnummer: was
        zaehlt, ist wie viel wir vom Gegner wissen und wie viele eigene
        Picks uns noch bleiben. Der vierte Pick eines Drafts ist etwas
        anderes, je nachdem ob danach noch zwei eigene folgen.
        """
        if self.picks_gesamt == 0 and self.am_zug == "own":
            return config.PHASE_FIRST_PICK
        if self.unsere_restpicks <= 1:
            return config.PHASE_LAST
        # Bis zwei Picks auf dem Brett liegen, ist der Informationsstand
        # noch duenn - egal, ob der eine davon von uns kam. Frueher hing
        # die Grenze daran, ob WIR schon gepickt hatten; damit galt der
        # zweite Pick eines Drafts bereits als Mittelphase, obwohl vom
        # Gegner noch nichts bekannt war.
        if self.picks_gesamt <= 2:
            return config.PHASE_EARLY
        return config.PHASE_MID

    @property
    def phase_label(self):
        return config.PHASEN_LABEL.get(self.phase, self.phase)

    @property
    def gesperrte_ids(self):
        """Alles, was nicht mehr gewaehlt werden darf."""
        return {b.id for b in self.own_picks} | {b.id for b in self.enemy_picks} | {
            b.id for b in self.bans
        }

    # --- Simulation -----------------------------------------------------
    def mit_pick(self, brawler, team="own"):
        """Neuer Context mit einem zusaetzlichen Pick.

        Grundlage fuer Vorausschau und spaeteres Backtesting: die Engine
        kann einen Pick durchspielen, ohne den echten Zustand zu
        veraendern.
        """
        if team == "own":
            return replace(self, own_picks=self.own_picks + (brawler,))
        return replace(self, enemy_picks=self.enemy_picks + (brawler,))

    def mit_ban(self, brawler):
        return replace(self, bans=self.bans + (brawler,))

    # --- Pruefung -------------------------------------------------------
    def pruefe(self):
        """Harte Fehler werfen, weiche als Hinweisliste zurueckgeben.

        Hart ist, was zu falschen Empfehlungen fuehrt (ein Brawler in
        zwei Teams). Weich ist, was nur ungewoehnlich ist (mehr Picks auf
        einer Seite, als die Reihenfolge vorsieht) - daran soll die
        Oberflaeche nicht scheitern, denn Nutzer korrigieren Eingaben.
        """
        if len(self.own_picks) > PICKS_JE_TEAM:
            raise DraftFehler(f"Mehr als {PICKS_JE_TEAM} eigene Picks")
        if len(self.enemy_picks) > PICKS_JE_TEAM:
            raise DraftFehler(f"Mehr als {PICKS_JE_TEAM} gegnerische Picks")
        if len(self.bans) > BANS_JE_TEAM * 2:
            raise DraftFehler(f"Mehr als {BANS_JE_TEAM * 2} Bans")

        alle = list(self.own_picks) + list(self.enemy_picks) + list(self.bans)
        ids = [b.id for b in alle]
        if len(ids) != len(set(ids)):
            doppelt = {b.name for b in alle if ids.count(b.id) > 1}
            raise DraftFehler(f"Mehrfach im Draft: {', '.join(sorted(doppelt))}")

        if self.brawl_map is not None and self.game_mode is not None:
            if self.brawl_map.game_mode_id != self.game_mode.id:
                raise DraftFehler(
                    f"Map '{self.brawl_map.name}' gehört nicht zu Modus "
                    f"'{self.game_mode.name}'"
                )

        hinweise = []
        erwartet_own = sum(
            1 for i in range(self.picks_gesamt)
            if i < len(PICK_REIHENFOLGE) and PICK_REIHENFOLGE[i] == self.unser_slot
        )
        if len(self.own_picks) != erwartet_own:
            hinweise.append(
                "Die Pickreihenfolge weicht vom Standard 1-2-2-1 ab - "
                "die Phasenbewertung geht vom tatsächlichen Stand aus."
            )
        return hinweise

    # --- Ausgabe --------------------------------------------------------
    def als_dict(self):
        return {
            "mode": self.game_mode.slug if self.game_mode else None,
            "map": self.brawl_map.slug if self.brawl_map else None,
            "own_picks": [b.slug for b in self.own_picks],
            "enemy_picks": [b.slug for b in self.enemy_picks],
            "bans": [b.slug for b in self.bans],
            "own_team_first_pick": self.own_team_first_pick,
            "phase": self.phase,
            "phase_label": self.phase_label,
            "am_zug": self.am_zug,
            "pick_nummer": self.picks_gesamt + 1,
            "unsere_restpicks": self.unsere_restpicks,
            "gegner_restpicks": self.gegner_restpicks,
            "draft_fertig": self.draft_fertig,
            "rank_pool": self.rank_pool,
        }
