"""Counter: wer wen bestraft.

Zwei Quellen, klar getrennt:

1. **Gepflegte Counter** (`CounterStat`) - gelten, wenn vorhanden.
2. **Heuristik aus Eigenschaften** - wenn nichts gepflegt ist.

Die Trennung ist wichtig fuer die Ehrlichkeit der Oberflaeche: ein Grund
aus gepflegten Daten wird anders gekennzeichnet als einer, den das
System aus Attributen erschlossen hat. Ohne Heuristik waere die App bei
jedem ungepflegten Paar blind, ohne Kennzeichnung wuerde sie raten und
so tun, als wuesste sie es.

Bewusst **nicht** getan: eine gemessene Winrate direkt als Vorteil
verwenden. "Gale gewinnt 62 % gegen Bull" heisst nicht "Gale ist ein
62-%-Counter" - da stecken Map, Rang, Mitspieler und Patch mit drin.
Der Vorteil ist die bereinigte Groesse; wie sie spaeter aus Rohdaten
entsteht, ist Sache des Aggregators, nicht dieser Datei.
"""

from drafter import config
from drafter.services.scoring import Grund, Komponente, klemme

# Ab welchem Attributwert eine Eigenschaft ueberhaupt als Antwort zaehlt.
# Darunter ist "ein bisschen Anti-Tank" kein Vorteil, sondern Zufall.
_SCHWELLE = 0.40


def _ist(brawler, *rollen):
    return any(r in brawler.alle_rollen for r in rollen)


def heuristischer_vorteil(a, b):
    """Geschaetzter Vorteil von a gegen b, [-1, +1], plus Begruendung.

    Jedes Signal beantwortet eine konkrete Frage ("hat a eine Antwort auf
    das, was b gefaehrlich macht"). Die Betraege sind so gewaehlt, dass
    ein einzelnes Signal den Vorteil nicht allein bestimmt - erst mehrere
    zusammen ergeben einen klaren Counter.
    """
    signale = []

    # 1. Antwort auf Robustheit. Nur relevant, wenn b ueberhaupt robust ist.
    if b.wert("tankiness") > 0.5:
        w = (a.wert("anti_tank") - _SCHWELLE) * b.wert("tankiness") * 1.3
        signale.append((w, f"hat Anti-Tank-Werkzeuge gegen {b.name}"))

    # 2. Antwort auf Angreifer. Wer schnell an dich herankommt, ist nur
    #    dann ein Problem, wenn du ihn nicht wegschieben kannst.
    angriff = max(b.wert("engage"), b.wert("mobility")) if _ist(b, "assassin", "aggro") \
        else b.wert("engage") * 0.5
    if angriff > 0.45:
        w = (a.wert("anti_assassin") - _SCHWELLE) * angriff * 1.2
        signale.append((w, f"kann {b.name} auf Abstand halten"))

    # 3. Antwort auf Flaechenverweigerung.
    wurf = 1.0 if _ist(b, "thrower") else b.wert("area_control") * 0.5
    if wurf > 0.4:
        w = (a.wert("anti_thrower") - _SCHWELLE) * wurf * 1.1
        signale.append((w, f"kommt an {b.name} heran, statt die Fläche zu meiden"))

    # 4. Reichweite. Der Vorteil verpufft, wenn b die Distanz schliessen kann.
    diff = a.wert("long_range") - b.wert("long_range")
    if abs(diff) > 0.2:
        w = diff * (1.0 - b.wert("mobility") * 0.7) * 0.55
        signale.append((
            w,
            f"schießt weiter als {b.name}" if diff > 0 else f"wird von {b.name} überschossen",
        ))

    # 5. Druck auf empfindliche Ziele: viel Reichweite, wenig Eigenschutz.
    weich = b.wert("long_range") * (1.0 - max(b.wert("survivability"), b.wert("peel")))
    if weich > 0.3:
        w = a.wert("backline_pressure") * weich * 0.8
        signale.append((w, f"kommt an {b.name} in der Backline heran"))

    # 6. Kontrolle gegen Nahkampf.
    kontrolle = max(a.wert("knockback"), a.wert("crowd_control"), a.wert("stun"))
    naehe = max(b.wert("close_range"), b.wert("engage"))
    if kontrolle > 0.5 and naehe > 0.55:
        signale.append((kontrolle * naehe * 0.45, f"unterbricht {b.name} beim Herankommen"))

    if not signale:
        return 0.0, None

    gesamt = klemme(sum(w for w, _ in signale))
    staerkstes = max(signale, key=lambda p: abs(p[0]))
    return gesamt, (staerkstes[1] if abs(staerkstes[0]) > 0.08 else None)


def _gemessener_vorteil(hin, her):
    """Berechneter Vorteil aus der Sicht von `hin` - oder None.

    Gespeichert ist je Paar nur eine Richtung. Liegt sie als `her` vor,
    ist der Vorteil ihr Negativ. Liegen (etwa aus alten Daten) beide
    Richtungen vor, zaehlt nur `hin` - die andere ist dieselbe Messung
    mit umgekehrtem Vorzeichen und wird nicht noch einmal verrechnet.
    """
    if hin is not None and hin.measured_counter_advantage is not None:
        return hin.measured_counter_advantage, hin
    if her is not None and her.measured_counter_advantage is not None:
        return -her.measured_counter_advantage, her
    return None


def vorteil(kandidat, gegner, raum):
    """Netto-Vorteil im Matchup, [-1, +1] - plus Begruendung und Quelle.

    Drei Rechenwege, weil die drei Quellen Verschiedenes bedeuten:

    1. **Gemessen** (aus Partien aggregiert, `measured_counter_advantage`):
       Der Wert IST bereits die Netto-Aussage - die Abweichung der
       Paar-Siegquote von der log5-Erwartung aus den Einzelstaerken. Die
       Gegenrichtung ist exakt ihr Negativ und wird daraus abgeleitet,
       nicht zusaetzlich abgezogen. Symmetrisch per Konstruktion:
       vorteil(A, B) == -vorteil(B, A).

    2. **Gepflegt** (Demo, manuell, `manual_counter_score`): Zwei
       eigenstaendige, gerichtete Einschaetzungen, die asymmetrisch sein
       duerfen. Netto = hin - Faktor * her.

    3. **Heuristik** (keine Zeile): wie gepflegt, aus Attributen geschaetzt.

    Gibt es fuer ein Paar Messung und Pflege zugleich, gilt die Messung.

    Frueher liefen 1 und 2 durch dieselbe Formel "hin - 0,8 * her". Fuer
    gepflegte Werte ist das richtig; fuer gemessene, gegengleiche Werte
    wurde dasselbe Matchup damit 1,8-fach gezaehlt.
    """
    hin = raum.counter(kandidat, gegner)
    her = raum.counter(gegner, kandidat)

    # --- 1. Gemessen ----------------------------------------------------
    gemessen = _gemessener_vorteil(hin, her)
    if gemessen is not None:
        wert, zeile = gemessen
        quelle = "demo" if zeile.is_demo else "daten"
        grund = None
        # Gemessene Zeilen haben keinen gepflegten Grundtext - der Satz
        # nennt deshalb, WORAUF die Aussage beruht, statt einen Mechanismus
        # zu behaupten, den die Messung nicht kennt.
        if wert > 0.15:
            grund = f"gewinnt gegen {gegner.name} öfter als erwartet ({zeile.games} Partien)"
        elif wert < -0.15:
            grund = f"verliert gegen {gegner.name} öfter als erwartet ({zeile.games} Partien)"
        return klemme(wert), grund, quelle

    # --- 2. Gepflegt ----------------------------------------------------
    hin_wert = hin.manual_counter_score if hin is not None else None
    her_wert = her.manual_counter_score if her is not None else None
    if hin_wert is not None or her_wert is not None:
        wert = (hin_wert or 0.0) - (her_wert or 0.0) * config.GEPFLEGTER_COUNTER_GEGENRICHTUNG
        quelle = "demo" if (hin or her).is_demo else "daten"
        # Vier Faelle, nicht zwei: ein Vorteil kann auch daraus entstehen,
        # dass der GEGNER gegen uns schlecht dasteht. Wurde das uebersehen,
        # rechnete die Engine den Vorteil zwar richtig, konnte ihn aber
        # nicht begruenden - die Empfehlung stand oben und sagte nicht warum.
        grund = None
        if hin_wert is not None and hin_wert > 0.15:
            grund = hin.reason or f"ist stark gegen {gegner.name}"
        elif her_wert is not None and her_wert < -0.15:
            grund = her.reason or f"hat gegen {gegner.name} die besseren Werkzeuge"
        elif her_wert is not None and her_wert > 0.15:
            grund = her.reason or f"verliert das Matchup gegen {gegner.name}"
        elif hin_wert is not None and hin_wert < -0.15:
            grund = hin.reason or f"kommt gegen {gegner.name} nicht durch"
        return klemme(wert), grund, quelle

    # --- 3. Heuristik ---------------------------------------------------
    hin_h, grund_hin = heuristischer_vorteil(kandidat, gegner)
    her_h, grund_her = heuristischer_vorteil(gegner, kandidat)
    wert = klemme(hin_h - her_h * config.HEURISTISCHER_COUNTER_GEGENRICHTUNG)
    grund = grund_hin if abs(hin_h) >= abs(her_h) else grund_her
    return wert, grund, "heuristik"


def komponente(kandidat, ctx, raum):
    """Counter-Komponente des Scores.

    Mittelt ueber die bekannten Gegner. Der schlechteste Wert zieht
    zusaetzlich: ein Pick, der gegen zwei Gegner neutral und gegen einen
    hart verliert, ist kein neutraler Pick - genau dieser eine Gegner
    wird ihn den ganzen Kampf lang jagen.
    """
    komp = Komponente(key=config.K_COUNTER)
    if not ctx.enemy_picks:
        return komp

    werte = []
    for gegner in ctx.enemy_picks:
        wert, grund, quelle = vorteil(kandidat, gegner, raum)
        werte.append(wert)
        if grund and abs(wert) > 0.12:
            komp.gruende.append(Grund(
                text=grund, positiv=wert > 0, staerke=min(1.0, abs(wert) + 0.3), quelle=quelle
            ))

    mittel = sum(werte) / len(werte)
    schlechtester = min(werte)
    komp.wert = klemme(mittel * 0.7 + schlechtester * 0.3)
    # Jeder bekannte Gegner macht die Aussage sicherer.
    komp.confidence = min(1.0, 0.45 + 0.2 * len(werte))
    return komp


def bestes_matchup(kandidat, gegner_liste, raum):
    """Gegen wen soll dieser Brawler bevorzugt spielen?"""
    if not gegner_liste:
        return None
    bewertet = [(vorteil(kandidat, g, raum)[0], g) for g in gegner_liste]
    wert, gegner = max(bewertet, key=lambda p: p[0])
    return {"gegner": gegner.name, "vorteil": round(wert, 2)} if wert > 0.05 else None


def schlechtestes_matchup(kandidat, gegner_liste, raum):
    if not gegner_liste:
        return None
    bewertet = [(vorteil(kandidat, g, raum)[0], g) for g in gegner_liste]
    wert, gegner = min(bewertet, key=lambda p: p[0])
    return {"gegner": gegner.name, "vorteil": round(wert, 2)} if wert < -0.05 else None
