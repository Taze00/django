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
from drafter.services import draft_position
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
    # Nur Brawler mit Profil - die Passung der anderen ist unbekannt.
    nach_passung = sorted(
        (b for b in kandidaten if b.hat_profil), key=lambda b: -roh_passung(b, anforderungen)
    )
    return nach_passung[:anzahl]


def empfehlungen(ctx, raum, anzahl=None):
    """Ban-Kandidaten, gefaehrlichster zuerst.

    Nur bewertbare Brawler (Stufe profil oder gemessen). Jeder Teilaspekt
    wird nur fuer die Brawler gerechnet, bei denen er bekannt ist, und
    feldrelativ ueber genau diese normalisiert. Fehlt einem Brawler ein
    Aspekt, faellt er aus seiner Summe heraus und die uebrigen werden
    hochgerechnet - wie beim Pick-Score. Frueher galt ein fehlender
    Draft-Wert als 0.5 und eine fehlende Meta als 50 %.
    """
    anzahl = anzahl or config.BAN_VORSCHLAEGE
    kandidaten = [b for b in raum.verfuegbare(ctx.gesperrte_ids) if raum.bewertbar(b)]
    if not kandidaten:
        return []

    anforderungen = (
        ctx.brawl_map.anforderungs_vektor() if ctx.brawl_map is not None else {}
    )
    unsere = _unsere_wahrscheinliche_strategie(kandidaten, anforderungen, ctx)

    # Rohwerte je Teilaspekt - nur wo bekannt.
    roh = {aspekt: {} for aspekt in config.BAN_GEWICHTE}
    gegner_hat_first = not ctx.own_team_first_pick

    for b in kandidaten:
        if b.hat_profil:
            roh["map_strength"][b.id] = roh_passung(b, anforderungen)

        meta = raum.staerke(b)
        if meta.bekannt:
            roh["meta_strength"][b.id] = meta.rate

        # Gepflegte Draftwerte zaehlen nur, wenn sie belastbar sind -
        # die Demo-Handwerte vom 2026-09-14 gehen seit dem 2026-09-20
        # nicht mehr ins Scoring (siehe draft_position).
        draftwerte = {k: draft_position.gepflegter_draftwert(b, k) for k in
                      ("blind_pick_value", "last_pick_value", "counter_pick_value",
                       "flexibility_value", "counterability")}
        if all(v is not None for v in draftwerte.values()):
            # Was ihn in der gegnerischen Pickposition gefaehrlich macht.
            if gegner_hat_first:
                roh["pick_order_threat"][b.id] = draftwerte["blind_pick_value"]
            else:
                roh["pick_order_threat"][b.id] = max(
                    draftwerte["last_pick_value"], draftwerte["counter_pick_value"])
            roh["flexibility"][b.id] = draftwerte["flexibility_value"]
            roh["uncounterability"][b.id] = 1.0 - draftwerte["counterability"]

        # Wie hart bestraft er das, was wir spielen wollen? Unbekannte
        # Matchups zaehlen nicht mit.
        bedrohung = []
        for unser in unsere:
            wert, _, quelle = vorteil(b, unser, raum)
            if quelle is not None:
                bedrohung.append(wert)
        if bedrohung:
            roh["counter_threat"][b.id] = sum(bedrohung) / len(bedrohung)

    normiert = {aspekt: z_werte(werte) for aspekt, werte in roh.items()}

    fokus = (
        config.BAN_FOKUS_GEGNER_FIRST if gegner_hat_first
        else config.BAN_FOKUS_GEGNER_LAST
    )

    bewertet = []
    for b in kandidaten:
        teile = {}
        summe = 0.0
        gewicht_gesamt = 0.0
        gewicht_bekannt = 0.0
        for aspekt, gewicht in config.BAN_GEWICHTE.items():
            g = gewicht * fokus.get(aspekt, 1.0)
            gewicht_gesamt += g
            if b.id not in normiert[aspekt]:
                continue
            gewicht_bekannt += g
            wert = normiert[aspekt][b.id]
            teile[aspekt] = wert * g
            summe += wert * g
        abdeckung = gewicht_bekannt / gewicht_gesamt if gewicht_gesamt else 0.0
        gesamt = summe * (gewicht_gesamt / gewicht_bekannt) if gewicht_bekannt else 0.0

        # Duenne Datenlage senkt die Dringlichkeit eines Bans: einen Ban
        # auf Verdacht auszugeben, kostet einen von drei.
        meta = raum.staerke(b)
        sicherheit = meta.confidence if meta.bekannt else 0.15
        gesamt -= (1.0 - sicherheit) * 0.10

        bewertet.append((gesamt, b, teile, sicherheit, abdeckung))

    bewertet.sort(key=lambda p: -p[0])

    ergebnis = []
    for gesamt, b, teile, sicherheit, abdeckung in bewertet[:anzahl]:
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
            "datenstufe": raum.stufe(b),
            "datenabdeckung": round(abdeckung * 100),
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
            bekannt = [u for u in unsere if vorteil(brawler, u, raum)[2] is not None]
            bedroht = max(
                bekannt, key=lambda u: vorteil(brawler, u, raum)[0], default=None
            )
            if bedroht is not None:
                gruende.append(f"bestraft {bedroht.name}, den wir hier gern spielen würden")
        elif aspekt == "flexibility":
            gruende.append("passt in fast jede Aufstellung - schwer einzuplanen")
        elif aspekt == "uncounterability":
            gruende.append("kaum zu kontern - was wir nicht beantworten können, bannen wir")

    return gruende[:3]
