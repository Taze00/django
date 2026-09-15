"""Die Engine: Context rein, Empfehlungen raus.

Diese Datei rechnet **nichts** selbst. Sie ruft die Komponenten in der
richtigen Reihenfolge auf, setzt die Gewichte der aktuellen Phase und
setzt das Ergebnis zusammen. Jede Formel steht in ihrem eigenen Modul -
dadurch bleibt hier lesbar, *was* passiert, und dort nachvollziehbar,
*wie*.

Reihenfolge ist wichtig und nicht beliebig:

1. Daten laden (einmal, nicht je Kandidat)
2. Teamanalysen bauen (einmal, von mehreren Komponenten genutzt)
3. feldweite Komponenten (Map-Fit, Meta, Teambedarf brauchen das ganze Feld)
4. kandidatenweise Komponenten
5. Gewichte setzen, persoenlichen Deckel anwenden
6. Confidence - erst wenn alle anderen Komponenten stehen
7. sortieren
8. **erst fuer die Spitze**: Siegchance, Coach-Texte, Build

Schritt 8 ist der Grund, warum die Antwort schnell bleibt: die teuren
Auskuenfte entstehen nur fuer die Vorschlaege, die auch angezeigt
werden - nicht fuer alle 20 Kandidaten.
"""

from drafter import config
from drafter.services import (
    builds, coach, confidence, counters, draft_position, map_fit, meta,
    personal, synergies, team_need, win_probability,
)
from drafter.services.daten import Datenraum
from drafter.services.scoring import Empfehlung, Komponente
from drafter.services.team_coverage import Teamanalyse, anforderungen_mit_gegner


class DraftEngine:
    """Bewertet einen Draftzustand."""

    def __init__(self, ctx, raum=None):
        self.ctx = ctx
        self.hinweise = ctx.pruefe()
        self.raum = (raum or Datenraum(
            brawl_map=ctx.brawl_map,
            game_mode=ctx.game_mode,
            patch=ctx.patch,
            rank_pool=ctx.rank_pool,
        )).laden()

        # Zwei Anforderungsprofile, bewusst getrennt:
        #
        # `anforderungen`       - was die MAP verlangt. Grundlage des Map-Fits.
        # `bedarfsanforderungen` - Map PLUS das, was das Gegnerteam erzwingt.
        #                          Grundlage von Teambedarf, Redundanz und
        #                          Angreifbarkeit.
        #
        # Wuerde der Teambedarf nur die Map lesen, koennte er nie
        # erkennen, dass uns gegen genau dieses Gegnerteam etwas fehlt -
        # und die Empfehlung waere wieder nur eine Map-Tierlist.
        self.anforderungen = self._anforderungen()
        self.bedarfsanforderungen = anforderungen_mit_gegner(
            self.anforderungen, list(ctx.enemy_picks)
        )
        self.eigene_analyse = Teamanalyse.bauen(
            list(ctx.own_picks), self.bedarfsanforderungen
        )
        # Das Gegnerteam wird gespiegelt bewertet: was WIR ihm abverlangen.
        self.gegner_analyse = Teamanalyse.bauen(
            list(ctx.enemy_picks),
            anforderungen_mit_gegner(self.anforderungen, list(ctx.own_picks)),
        )
        # Ausruestung wird erst geladen, wenn jemand nach Builds oder
        # Warnungen fragt - eine reine Score-Abfrage braucht sie nicht.
        self._katalog = None

    @property
    def katalog(self):
        """Ausruestungskatalog der Anfrage, einmal geladen.

        Die gegnerischen Gadgets sind fuer JEDEN Kandidaten dieselben -
        ohne den Katalog fragt sie jede einzelne Empfehlung neu ab.
        """
        if self._katalog is None:
            self._katalog = builds.Ausruestungskatalog(
                list(self.raum.brawler) + list(self.ctx.enemy_picks)
            )
        return self._katalog

    def _anforderungen(self):
        """Was Map und Modus verlangen, als {key: 0-1}."""
        if self.ctx.brawl_map is not None:
            return self.ctx.brawl_map.anforderungs_vektor()
        if self.ctx.game_mode is not None:
            from drafter import attributes as attr
            return attr.als_vektor(self.ctx.game_mode.base_requirements or {})
        return {}

    # --- Empfehlungen ---------------------------------------------------
    def empfehlungen(self, anzahl=None, mit_details=None):
        """Bewertete Kandidaten, bester zuerst.

        `mit_details=None` heisst: Coach-Texte und Build fuer alles, was
        angezeigt wird. Die Score-Aufschluesselung haengt nicht daran -
        die bekommt jede Empfehlung, weil sie ohnehin gerechnet ist.
        """
        anzahl = anzahl or config.EMPFEHLUNGEN_ANZAHL
        kandidaten = self.raum.verfuegbare(self.ctx.gesperrte_ids)
        if not kandidaten:
            return []

        gewichte = config.gewichte_fuer(self.ctx.phase)

        # Feldweite Komponenten - brauchen alle Kandidaten gleichzeitig.
        map_komp = map_fit.komponenten_fuer_pool(
            kandidaten, self.anforderungen, self.ctx.brawl_map
        )
        meta_komp = meta.komponenten_fuer_pool(kandidaten, self.raum, self.ctx.patch)
        bedarf_komp = team_need.komponenten_fuer_pool(
            kandidaten, self.eigene_analyse, self.ctx
        )

        ergebnisse = []
        for kandidat in kandidaten:
            komponenten = {
                config.K_MAP_MODE: map_komp[kandidat.id],
                config.K_META: meta_komp[kandidat.id],
                config.K_TEAM_NEED: bedarf_komp[kandidat.id],
                config.K_COUNTER: counters.komponente(kandidat, self.ctx, self.raum),
                config.K_SYNERGY: synergies.komponente(kandidat, self.ctx, self.raum),
                config.K_DRAFT_POSITION: draft_position.komponente(kandidat, self.ctx),
                config.K_FLEXIBILITY: draft_position.flexibilitaet(kandidat, self.ctx),
                config.K_PERSONAL: personal.komponente(kandidat, self.ctx),
                config.K_REDUNDANCY: team_need.redundanz(
                    kandidat, self.eigene_analyse, self.ctx
                ),
                config.K_WEAKNESS: team_need.angreifbarkeit(
                    kandidat, self.eigene_analyse, self.ctx
                ),
            }
            for key, komp in komponenten.items():
                komp.gewicht = gewichte.get(key, 0.0)

            # Leitplanke: die persoenliche Sicherheit darf den Score nur
            # um config.PERSOENLICH_MAX_AUSSCHLAG verschieben.
            personal.deckel_anwenden(komponenten[config.K_PERSONAL])

            # Datenlage zum Schluss - sie bewertet die anderen Komponenten.
            conf = confidence.fuer_empfehlung(komponenten, self.ctx, self.raum)
            unsicherheit = Komponente(
                key=config.K_UNCERTAINTY,
                wert=-(1.0 - conf),
                gewicht=gewichte.get(config.K_UNCERTAINTY, 0.0),
                confidence=1.0,
            )
            if conf < 0.3:
                from drafter.services.scoring import Grund
                unsicherheit.gruende.append(Grund(
                    text="dünne Datenlage - die Einschätzung ist unsicher",
                    positiv=False, staerke=0.3,
                ))
            komponenten[config.K_UNCERTAINTY] = unsicherheit

            ergebnisse.append(Empfehlung(
                brawler=kandidat,
                komponenten=komponenten,
                confidence=conf,
                rolle=coach.rolle_im_team(kandidat, self.eigene_analyse),
            ))

        # Nach dem ungeklemmten Wert - sonst waeren Kandidaten unterhalb
        # von -1 ununterscheidbar (siehe Empfehlung.roher_score).
        ergebnisse.sort(key=lambda e: -e.roher_score)
        spitze = ergebnisse[:anzahl]
        details_bis = len(spitze) if mit_details is None else mit_details

        # Teure Auskuenfte nur fuer das, was angezeigt wird.
        provider = win_probability.hole_provider()
        for rang, empfehlung in enumerate(spitze):
            nachher = self.ctx.mit_pick(empfehlung.brawler, "own")
            analyse_nachher = Teamanalyse.bauen(
                list(nachher.own_picks), self.bedarfsanforderungen
            )
            empfehlung.win_probability, _ = provider.vorhersage(
                nachher, self.raum, analyse_nachher, self.gegner_analyse
            )
            if rang < details_bis:
                self._details_ergaenzen(empfehlung)

        return spitze

    def _details_ergaenzen(self, empfehlung):
        b = empfehlung.brawler
        gegner = list(self.ctx.enemy_picks)
        empfehlung.aufgaben = coach.aufgaben(b, self.ctx, self.eigene_analyse, self.raum)
        empfehlung.vermeiden = coach.vermeiden(b, self.ctx, self.raum)
        empfehlung.warnungen = coach.warnungen(b, self.ctx, self.raum, self.katalog)
        bestes = coach.bestes_matchup(b, gegner, self.raum)
        empfehlung.bevorzugte_matchups = [bestes] if bestes else []
        empfehlung.zu_vermeidendes_matchup = coach.schlechtestes_matchup(
            b, gegner, self.raum
        )
        empfehlung.build = builds.empfehlung(b, self.ctx, self.katalog)

    def detail(self, brawler):
        """Vollstaendige Bewertung eines einzelnen Brawlers.

        Fuer den Klick auf eine Karte: derselbe Rechenweg, aber mit
        Coach-Texten und Build, auch wenn er nicht unter den ersten drei
        steht.
        """
        for empfehlung in self.empfehlungen(anzahl=200, mit_details=0):
            if empfehlung.brawler.id == brawler.id:
                self._details_ergaenzen(empfehlung)
                nachher = self.ctx.mit_pick(brawler, "own")
                empfehlung.win_probability, _ = win_probability.hole_provider().vorhersage(
                    nachher, self.raum,
                    Teamanalyse.bauen(list(nachher.own_picks), self.bedarfsanforderungen),
                    self.gegner_analyse,
                )
                return empfehlung
        return None

    # --- Gesamtbild -----------------------------------------------------
    def siegchance(self):
        provider = win_probability.hole_provider()
        wert, conf = provider.vorhersage(
            self.ctx, self.raum, self.eigene_analyse, self.gegner_analyse
        )
        return {
            "prozent": round(wert * 100, 1),
            "confidence": round(conf, 2),
            "confidence_label": confidence.label(conf),
            "ist_heuristik": provider.ist_heuristik,
            "hinweis": (
                "Heuristische Schätzung aus Deckung, Matchups und Meta - "
                "keine kalibrierte Wahrscheinlichkeit."
                if provider.ist_heuristik else ""
            ),
        }

    def endanalyse(self):
        """Der Matchplan nach abgeschlossenem Draft.

        Alles hier entsteht aus denselben Strukturen, die auch den Score
        erzeugt haben - Attribute, Counter, Synergien, Teamluecken,
        Build-Regeln. Kein eigener Textbestand: was der Coach sagt, kann
        die Bewertung belegen, und was die Bewertung nicht hergibt, sagt
        der Coach nicht.
        """
        eigene = list(self.ctx.own_picks)
        gegner = list(self.ctx.enemy_picks)

        # Lanes einmal fuer das Team bestimmen und danach je Spieler
        # zuordnen - sonst koennte jeder Spieler eine andere Aufstellung
        # angezeigt bekommen als der Teamplan darunter.
        lanes = coach.lane_vorschlag(eigene, self.ctx)
        lane_nach_slug = {eintrag["slug"]: eintrag for eintrag in lanes}

        # Dasselbe fuer die Matchups: EINE abgestimmte Zuordnung fuer das
        # Team, aus der sich jede Spielerkarte bedient. Rechnet jeder
        # Spieler sein bestes Matchup selbst aus, bekommen zwei denselben
        # Gegner und der dritte gar keinen.
        matchups = coach.matchup_zuordnung(eigene, gegner, self.raum)
        gegner_nach_slug = {b.slug: b for b in gegner}
        zuweisung = {
            eintrag["unser_slug"]: gegner_nach_slug.get(eintrag["gegner_slug"])
            for eintrag in matchups
        }

        spieler = []
        for b in eigene:
            zugewiesen = zuweisung.get(b.slug)
            aufgaben = coach.aufgaben(
                b, self.ctx, self.eigene_analyse, self.raum, zugewiesen
            )
            lane = lane_nach_slug.get(b.slug, {})
            spieler.append({
                "name": b.name,
                "slug": b.slug,
                "farbe": b.color,
                "initialen": b.initialen,
                "image_url": b.image_url,
                "rolle": coach.rolle_im_team(b, self.eigene_analyse),
                "hauptaufgabe": aufgaben[0] if aufgaben else None,
                "aufgaben": aufgaben,
                "vermeiden": coach.vermeiden(b, self.ctx, self.raum),
                "warnungen": coach.warnungen(b, self.ctx, self.raum, self.katalog),
                # Aus der abgestimmten Zuordnung, nicht unabhaengig gesucht.
                "bevorzugtes_matchup": next(
                    (m for m in matchups if m["unser_slug"] == b.slug), None
                ),
                "zu_vermeidendes_matchup": coach.schlechtestes_matchup(
                    b, gegner, self.raum
                ),
                "lane": lane.get("lane"),
                "lane_grund": lane.get("grund"),
                "build": builds.empfehlung(b, self.ctx, self.katalog),
            })

        siegchance = self.siegchance()
        return {
            "siegchance": siegchance,
            "datenlage": {
                "nur_demo": self.raum.nur_demo,
                "confidence": siegchance["confidence"],
                "confidence_label": siegchance["confidence_label"],
                "hinweis": confidence.erklaerung(
                    siegchance["confidence"], self.raum, self.ctx
                ),
            },
            "team": spieler,
            "win_condition": coach.win_condition(self.ctx, self.eigene_analyse, self.raum),
            "schwaechen": coach.team_schwaechen(self.ctx, self.eigene_analyse, self.raum),
            "gefahren": coach.gefahren(self.ctx, self.eigene_analyse, self.raum),
            "lanes": lanes,
            "matchups": matchups,
            "lane_tausch": coach.lane_tausch_plan(self.ctx, self.raum),
            "eigene_analyse": self.eigene_analyse.als_dict(),
            "gegner_analyse": self.gegner_analyse.als_dict(),
        }

    def als_dict(self, mit_bans=True):
        """Vollstaendige Antwort fuer die Oberflaeche."""
        from drafter.services import bans

        empfehlungen = self.empfehlungen()
        daten = {
            "draft_state": self.ctx.als_dict(),
            "hinweise": self.hinweise,
            # Ausfuehrlich fuer alle angezeigten Empfehlungen: die
            # Aufschluesselung, der Build und die Coach-Auskuenfte sind
            # ohnehin berechnet (siehe empfehlungen()), und eine
            # Empfehlung ohne Begruendung ist in diesem Werkzeug keine.
            "empfehlungen": [e.als_dict(ausfuehrlich=True) for e in empfehlungen],
            "team_analyse": self.eigene_analyse.als_dict(),
            "gegner_analyse": self.gegner_analyse.als_dict(),
            "siegchance": self.siegchance(),
            "datenlage": {
                "nur_demo": self.raum.nur_demo,
                "hinweis": confidence.erklaerung(
                    empfehlungen[0].confidence if empfehlungen else 0.0,
                    self.raum, self.ctx,
                ),
            },
        }
        if mit_bans and self.ctx.picks_gesamt == 0:
            daten["ban_empfehlungen"] = bans.empfehlungen(self.ctx, self.raum)
        if self.ctx.draft_fertig:
            daten["endanalyse"] = self.endanalyse()
        return daten
