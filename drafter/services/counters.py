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
from drafter.services import quellen, staerke
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
    if b.wert_oder("tankiness") > 0.5:
        w = (a.wert_oder("anti_tank") - _SCHWELLE) * b.wert_oder("tankiness") * 1.3
        signale.append((w, f"hat Anti-Tank-Werkzeuge gegen {b.name}"))

    # 2. Antwort auf Angreifer. Wer schnell an dich herankommt, ist nur
    #    dann ein Problem, wenn du ihn nicht wegschieben kannst.
    angriff = max(b.wert_oder("engage"), b.wert_oder("mobility")) if _ist(b, "assassin", "aggro") \
        else b.wert_oder("engage") * 0.5
    if angriff > 0.45:
        w = (a.wert_oder("anti_assassin") - _SCHWELLE) * angriff * 1.2
        signale.append((w, f"kann {b.name} auf Abstand halten"))

    # 3. Antwort auf Flaechenverweigerung.
    wurf = 1.0 if _ist(b, "thrower") else b.wert_oder("area_control") * 0.5
    if wurf > 0.4:
        w = (a.wert_oder("anti_thrower") - _SCHWELLE) * wurf * 1.1
        signale.append((w, f"kommt an {b.name} heran, statt die Fläche zu meiden"))

    # 4. Reichweite. Der Vorteil verpufft, wenn b die Distanz schliessen kann.
    diff = a.wert_oder("long_range") - b.wert_oder("long_range")
    if abs(diff) > 0.2:
        w = diff * (1.0 - b.wert_oder("mobility") * 0.7) * 0.55
        signale.append((
            w,
            f"schießt weiter als {b.name}" if diff > 0 else f"wird von {b.name} überschossen",
        ))

    # 5. Druck auf empfindliche Ziele: viel Reichweite, wenig Eigenschutz.
    weich = b.wert_oder("long_range") * (1.0 - max(b.wert_oder("survivability"), b.wert_oder("peel")))
    if weich > 0.3:
        w = a.wert_oder("backline_pressure") * weich * 0.8
        signale.append((w, f"kommt an {b.name} in der Backline heran"))

    # 6. Kontrolle gegen Nahkampf.
    kontrolle = max(a.wert_oder("knockback"), a.wert_oder("crowd_control"), a.wert_oder("stun"))
    naehe = max(b.wert_oder("close_range"), b.wert_oder("engage"))
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


def _gepflegter_vorteil(hin, her, gegner):
    """Netto aus gepflegten, gerichteten Zeilen - oder (None, None)."""
    hin_wert = hin.manual_counter_score if hin is not None else None
    her_wert = her.manual_counter_score if her is not None else None
    if hin_wert is None and her_wert is None:
        return None, None
    wert = (hin_wert or 0.0) - (her_wert or 0.0) * config.GEPFLEGTER_COUNTER_GEGENRICHTUNG
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
    return klemme(wert), grund


def vorteil(kandidat, gegner, raum):
    """Netto-Vorteil im Matchup, [-1, +1] - plus Begruendung und Quelle.

    Quelle nach services/quellen.py: "Measured", "Measured + Prior",
    "Profile" - oder None, wenn nichts bekannt ist (Aufrufer lassen das
    Paar dann aus).

    Drei Wertarten, weil sie Verschiedenes bedeuten:

    1. **Gemessen** (`measured_counter_advantage`): bereits die Netto-
       Aussage (Abweichung von der log5-Erwartung), die Gegenrichtung ist
       ihr Negativ - symmetrisch per Konstruktion.
    2. **Gepflegt** (`manual_counter_score`): zwei gerichtete
       Einschaetzungen, Netto = hin - Faktor * her.
    3. **Heuristik** aus Eigenschaften - nur, wenn weder 1 noch 2 vorliegt
       und BEIDE ein Profil haben. Zaehlt als "Profile".

    Liegen 1 und 2 vor, entscheidet die Stichprobe: wenig Partien mischen
    die Messung mit dem gepflegten Wert, viele ersetzen ihn. Die frueher
    gemeinsame Formel "hin - 0,8 * her" fuer beide zaehlte gemessene
    Matchups 1,8-fach.
    """
    hin = raum.counter(kandidat, gegner)
    her = raum.counter(gegner, kandidat)

    # --- 1. Gemessen (echte Partien) -----------------------------------
    gem_wert, gem_zeile = None, None
    gemessen = _gemessener_vorteil(hin, her)
    if gemessen is not None and not gemessen[1].is_demo and (gemessen[1].games or 0) > 0:
        gem_wert, gem_zeile = gemessen

    # --- 2. Gepflegt: aus der Prior-Quelle; ohne getrennten Prior (reiner
    #        Demo-Provider) stehen die gepflegten Zeilen im Messplatz.
    p_hin = raum.counter_prior(kandidat, gegner) or (hin if hin is not None and hin.ist_gepflegt else None)
    p_her = raum.counter_prior(gegner, kandidat) or (her if her is not None and her.ist_gepflegt else None)
    gep_wert, gep_grund = _gepflegter_vorteil(p_hin, p_her, gegner)

    # Nicht gemessene "Messungen" (synthetische Testdaten) sind kein Beleg:
    # sie gelten wie ein gepflegter Wert, wenn es keinen echten gibt.
    if gem_wert is None and gep_wert is None and gemessen is not None:
        return klemme(gemessen[0]), None, quellen.PROFILE

    if gem_wert is not None or gep_wert is not None:
        n = float(gem_zeile.sample_size or gem_zeile.games or 0) if gem_zeile else 0.0
        wert, quelle = quellen.mischen(gem_wert, gep_wert, n, config.PAAR_PRIOR_STAERKE)
        grund = gep_grund
        if gem_zeile is not None:
            # Gemessene Zeilen haben keinen gepflegten Grundtext - der Satz
            # nennt, WORAUF die Aussage beruht, statt einen Mechanismus zu
            # behaupten, den die Messung nicht kennt.
            if wert > 0.15:
                grund = f"gewinnt gegen {gegner.name} öfter als erwartet ({gem_zeile.games} Partien)"
            elif wert < -0.15:
                grund = f"verliert gegen {gegner.name} öfter als erwartet ({gem_zeile.games} Partien)"
            else:
                grund = None
        return klemme(wert), grund, quelle

    # --- 3. Heuristik ---------------------------------------------------
    # Nur, wenn BEIDE ein Profil haben. Sonst rechnete sie mit Nullen
    # ("schießt weiter als SHELLY", weil Shellys Reichweite als 0 galt).
    if not (kandidat.hat_profil and gegner.hat_profil):
        return 0.0, None, None
    hin_h, grund_hin = heuristischer_vorteil(kandidat, gegner)
    her_h, grund_her = heuristischer_vorteil(gegner, kandidat)
    wert = klemme(hin_h - her_h * config.HEURISTISCHER_COUNTER_GEGENRICHTUNG)
    grund = grund_hin if abs(hin_h) >= abs(her_h) else grund_her
    return wert, grund, quellen.PROFILE


def paar_sicherheit(kandidat, gegner, raum):
    """Wie sicher ist die Aussage ueber GENAU DIESES Paar? (0-1)

    Aus der Stichprobe des Paares, nicht aus der Zahl der Gegner im
    Draft: frueher stand hier `0.45 + 0.2 * Anzahl bekannter Gegner` -
    drei Gegner ergaben 1.0, auch wenn zu jedem Paar drei Partien
    vorlagen. Ein gemessenes Matchup mit 4 Partien und eines mit 400
    waren ununterscheidbar.
    """
    hin = raum.counter(kandidat, gegner)
    her = raum.counter(gegner, kandidat)
    gemessen = [z for z in (hin, her) if z is not None and z.ist_gemessen]
    n = max((float(z.sample_size or z.games or 0) for z in gemessen), default=0.0)
    if n > 0:
        return staerke.paar_confidence(n)
    gepflegt = [
        z for z in (raum.counter_prior(kandidat, gegner), raum.counter_prior(gegner, kandidat),
                    hin, her)
        if z is not None and z.ist_gepflegt
    ]
    if gepflegt:
        return max(z.confidence or 0.0 for z in gepflegt)
    return config.HEURISTIK_PAAR_CONFIDENCE


def ist_heuristisch(kandidat, gegner, raum):
    """Beruht das Matchup nur auf Eigenschaften (fuer "(geschätzt)" im Text)?"""
    return (
        raum.counter(kandidat, gegner) is None and raum.counter(gegner, kandidat) is None
        and raum.counter_prior(kandidat, gegner) is None
        and raum.counter_prior(gegner, kandidat) is None
    )


def komponente(kandidat, ctx, raum):
    """Counter-Komponente des Scores.

    Mittelt ueber die bekannten Gegner. Der schlechteste Wert zieht
    zusaetzlich: ein Pick, der gegen zwei Gegner neutral und gegen einen
    hart verliert, ist kein neutraler Pick - genau dieser eine Gegner
    wird ihn den ganzen Kampf lang jagen.

    Quelle der Komponente ist die schwaechste beteiligte Quelle.
    """
    komp = Komponente(key=config.K_COUNTER)
    if not ctx.enemy_picks:
        # Nicht anwendbar (fuer alle gleich) - verfuegbar mit Wert 0.
        komp.anwendbar = False
        komp.quelle = quellen.PROFILE if kandidat.hat_profil else quellen.UNKNOWN
        return komp

    werte = []
    herkunft = []
    sicherheiten = []
    for gegner in ctx.enemy_picks:
        wert, grund, quelle = vorteil(kandidat, gegner, raum)
        if quelle is None:
            continue   # unbekanntes Matchup - weder Vorteil noch Nachteil
        werte.append(wert)
        herkunft.append(quelle)
        sicherheiten.append(paar_sicherheit(kandidat, gegner, raum))
        if grund and abs(wert) > 0.12:
            grund_quelle = (
                "heuristik" if ist_heuristisch(kandidat, gegner, raum)
                else "daten" if quelle != quellen.PROFILE else "demo"
            )
            komp.gruende.append(Grund(
                text=grund, positiv=wert > 0, staerke=min(1.0, abs(wert) + 0.3),
                quelle=grund_quelle,
            ))

    if not werte:
        # Gegner stehen fest, aber zu keinem ist etwas bekannt: nicht
        # "neutral", sondern nicht berechenbar.
        komp.verfuegbar = False
        komp.confidence = 0.0
        komp.quelle = quellen.UNKNOWN
        return komp
    mittel = sum(werte) / len(werte)
    schlechtester = min(werte)
    komp.wert = klemme(mittel * 0.7 + schlechtester * 0.3)
    # Sicherheit aus den Stichproben der Paare, gedaempft um die Gegner,
    # zu denen nichts bekannt ist: zwei von drei Matchups bekannt heisst
    # zwei Drittel der Aussage.
    komp.confidence = (sum(sicherheiten) / len(sicherheiten)) * (
        len(werte) / len(ctx.enemy_picks))
    komp.quelle = quellen.schwaechste(herkunft)
    return komp


def _bekannte_matchups(kandidat, gegner_liste, raum):
    ergebnis = []
    for g in gegner_liste or ():
        wert, _, quelle = vorteil(kandidat, g, raum)
        if quelle is not None:
            ergebnis.append((wert, g))
    return ergebnis


def bestes_matchup(kandidat, gegner_liste, raum):
    """Gegen wen soll dieser Brawler bevorzugt spielen?"""
    bewertet = _bekannte_matchups(kandidat, gegner_liste, raum)
    if not bewertet:
        return None
    wert, gegner = max(bewertet, key=lambda p: p[0])
    return {"gegner": gegner.name, "vorteil": round(wert, 2)} if wert > 0.05 else None


def schlechtestes_matchup(kandidat, gegner_liste, raum):
    bewertet = _bekannte_matchups(kandidat, gegner_liste, raum)
    if not bewertet:
        return None
    wert, gegner = min(bewertet, key=lambda p: p[0])
    return {"gegner": gegner.name, "vorteil": round(wert, 2)} if wert < -0.05 else None
