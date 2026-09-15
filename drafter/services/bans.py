"""Ban-Coach.

Ein Ban beantwortet eine andere Frage als ein Pick. Nicht "wer ist gut
fuer uns", sondern **"wen koennen wir uns beim Gegner nicht leisten"**.
Das ist der Grund, warum "banne die drei mit der hoechsten Winrate"
falsch ist: ein starker Brawler, den wir sicher kontern koennen, ist
harmloser als ein mittelmaessiger, gegen den wir keine Antwort haben.

Die Pick-Reihenfolge verschiebt die Gefahr erheblich:

- **Gegner hat First Pick**: gefaehrlich sind Selbstlaeufer - flexibel,
  schwer konterbar, auf jeder Comp gut. Er nimmt sie blind, wir muessen
  reagieren.
- **Gegner hat Last Pick**: gefaehrlich sind Spezialisten - Brawler, die
  eine fertige Aufstellung gezielt zerlegen. Er sieht unser Team und
  bestraft es.

Genau diese Verschiebung machen `BAN_FOKUS_*` in der Konfiguration.
"""

from drafter import config
from drafter.services.counters import vorteil
from drafter.services.map_fit import roh_passung
from drafter.services.scoring import z_werte


def _unsere_wahrscheinliche_strategie(kandidaten, anforderungen, ctx, anzahl=5):
    """Was würden WIR auf dieser Map spielen wollen?

    Ohne diese Schaetzung koennte der Ban-Coach nicht beurteilen, ob ein
    Brawler unseren Plan bedroht - er kennt unseren Plan ja noch nicht.
    Naeherung: die Brawler mit der besten Mappassung sind unsere
    wahrscheinlichen Picks. Grob, aber besser als die Bedrohung ganz
    wegzulassen.
    """
    if ctx.own_picks:
        return list(ctx.own_picks)
    nach_passung = sorted(
        kandidaten, key=lambda b: -roh_passung(b, anforderungen)
    )
    return nach_passung[:anzahl]


def empfehlungen(ctx, raum, anzahl=None):
    """Ban-Kandidaten, gefaehrlichster zuerst."""
    anzahl = anzahl or config.BAN_VORSCHLAEGE
    kandidaten = raum.verfuegbare(ctx.gesperrte_ids)
    if not kandidaten:
        return []

    anforderungen = (
        ctx.brawl_map.anforderungs_vektor() if ctx.brawl_map is not None else {}
    )
    unsere = _unsere_wahrscheinliche_strategie(kandidaten, anforderungen, ctx)

    # Rohwerte je Teilaspekt, danach feldrelativ normalisiert - dieselbe
    # Begruendung wie beim Map-Fit: absolute Schwellen waeren geraten.
    roh = {
        "map_strength": {},
        "meta_strength": {},
        "pick_order_threat": {},
        "counter_threat": {},
        "flexibility": {},
        "uncounterability": {},
    }

    gegner_hat_first = not ctx.own_team_first_pick

    for b in kandidaten:
        roh["map_strength"][b.id] = roh_passung(b, anforderungen)

        stat = raum.stat(b)
        roh["meta_strength"][b.id] = stat.win_rate if stat else 0.5

        # Was ihn in der gegnerischen Pickposition gefaehrlich macht.
        if gegner_hat_first:
            roh["pick_order_threat"][b.id] = b.draftwert("blind_pick_value")
        else:
            roh["pick_order_threat"][b.id] = max(
                b.draftwert("last_pick_value"), b.draftwert("counter_pick_value")
            )

        # Wie hart bestraft er das, was wir spielen wollen?
        bedrohung = [vorteil(b, unser, raum)[0] for unser in unsere]
        roh["counter_threat"][b.id] = (
            sum(bedrohung) / len(bedrohung) if bedrohung else 0.0
        )

        roh["flexibility"][b.id] = b.draftwert("flexibility_value")
        roh["uncounterability"][b.id] = 1.0 - b.draftwert("counterability")

    normiert = {aspekt: z_werte(werte) for aspekt, werte in roh.items()}

    fokus = (
        config.BAN_FOKUS_GEGNER_FIRST if gegner_hat_first
        else config.BAN_FOKUS_GEGNER_LAST
    )

    bewertet = []
    for b in kandidaten:
        teile = {}
        gesamt = 0.0
        for aspekt, gewicht in config.BAN_GEWICHTE.items():
            wert = normiert[aspekt].get(b.id, 0.0)
            g = gewicht * fokus.get(aspekt, 1.0)
            teile[aspekt] = wert * g
            gesamt += wert * g

        # Duenne Datenlage senkt die Dringlichkeit eines Bans: einen Ban
        # auf Verdacht auszugeben, kostet einen von drei.
        stat = raum.stat(b)
        sicherheit = stat.confidence if stat else 0.15
        gesamt -= (1.0 - sicherheit) * 0.10

        bewertet.append((gesamt, b, teile, sicherheit))

    bewertet.sort(key=lambda p: -p[0])

    ergebnis = []
    for gesamt, b, teile, sicherheit in bewertet[:anzahl]:
        ergebnis.append({
            "slug": b.slug,
            "name": b.name,
            "farbe": b.color,
            "initialen": b.initialen,
            "image_url": b.image_url,
            "rollen": b.rollen_label,
            "score": round(50 + 50 * max(-1.0, min(1.0, gesamt))),
            # Sortiert wird bereits nach dem ungeklemmten Wert; er steht
            # zusaetzlich in der Antwort, damit er nicht verloren geht.
            "score_roh": round(gesamt, 3),
            "confidence": round(sicherheit, 2),
            "gruende": _gruende(b, teile, unsere, raum, ctx, gegner_hat_first),
        })
    return ergebnis


def _gruende(brawler, teile, unsere, raum, ctx, gegner_hat_first):
    """Warum genau dieser Ban - aus den stärksten Teilaspekten."""
    gruende = []
    sortiert = sorted(teile.items(), key=lambda p: -p[1])

    for aspekt, beitrag in sortiert[:3]:
        if beitrag < 0.02:
            continue
        if aspekt == "map_strength":
            ort = ctx.brawl_map.name if ctx.brawl_map else "diesem Modus"
            gruende.append(f"gehört auf {ort} zu den stärksten Picks")
        elif aspekt == "meta_strength":
            gruende.append("läuft im aktuellen Patch überdurchschnittlich")
        elif aspekt == "pick_order_threat":
            gruende.append(
                "idealer Blind Pick für den Gegner - er nimmt ihn, bevor wir reagieren können"
                if gegner_hat_first else
                "gefährlicher Last Pick - er sieht unser Team und bestraft es gezielt"
            )
        elif aspekt == "counter_threat":
            bedroht = max(
                unsere, key=lambda u: vorteil(brawler, u, raum)[0], default=None
            )
            if bedroht is not None:
                gruende.append(f"bestraft {bedroht.name}, den wir hier gern spielen würden")
        elif aspekt == "flexibility":
            gruende.append("passt in fast jede Aufstellung - schwer einzuplanen")
        elif aspekt == "uncounterability":
            gruende.append("kaum zu kontern - was wir nicht beantworten können, bannen wir")

    return gruende[:3]
