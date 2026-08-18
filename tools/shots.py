#!/usr/bin/env python3
"""Screenshot-Werkzeug fuer die Design-Arbeit an der Startseite.

Schiesst pro Durchlauf:
  - einen Viewport-Screenshot des Hero            -> <breite>-hero.png
  - einen Full-Page-Screenshot in 1440px Breite  -> 1440-full.png
  - einen Full-Page-Screenshot in  390px Breite  ->  390-full.png
  - je einen Einzel-Screenshot pro Sektion       -> <breite>-<section-id>.png

Der Hero-Shot ist die Aufnahme, der beim Hero zu trauen ist: nur
Fensterhoehe, ohne Scrollen, ohne dass die Parallaxe gelaufen ist.
Naeheres bei ansicht_schiessen.

Alles landet in screenshots/ (gitignored).

Aufruf:
    python3 tools/shots.py                        # http://localhost:8000/
    python3 tools/shots.py --url https://alex.volkmann.com/
    python3 tools/shots.py --wait 4               # laenger warten

Voraussetzung:
    pip install --user playwright && playwright install chromium
"""

import argparse
import sys
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sys.exit(
        "playwright fehlt.\n"
        "  pip install --user --break-system-packages playwright\n"
        "  ~/.local/bin/playwright install chromium"
    )

PROJEKT_WURZEL = Path(__file__).resolve().parent.parent
STANDARD_ZIEL = PROJEKT_WURZEL / "screenshots"
STANDARD_URL = "http://localhost:8000/"

# Breite x Hoehe. Die Hoehe ist nur das Fenster - die Full-Page-Shots
# wachsen ohnehin ueber sie hinaus.
ANSICHTEN = {
    "1440": {"viewport": {"width": 1440, "height": 900}, "mobil": False},
    "390": {"viewport": {"width": 390, "height": 844}, "mobil": True},
}

# Harte Obergrenze pro Sektions-Screenshot. Die Tinder-Galerie auf Mobil
# baut einen Kartenstapel, an dem Playwright sonst minutenlang haengt.
# Der Full-Page-Shot ist wichtiger als jede Einzelsektion - lieber eine
# Sektion ueberspringen als den Lauf verlieren.
SEKTIONS_ZEITLIMIT_MS = 20_000

# Sektionen sind die direkten Kinder von <body> mit id. Bewusst nicht
# hartkodiert: kommt eine Sektion dazu, taucht sie ohne Codeaenderung auf.
SEKTIONS_SELEKTOR = "body > section[id], body > header[id], body > footer[id], body > nav[id]"

# Laedt alle lazy-loading-Bilder und loest die fade-in-Beobachter aus.
# Ohne das ist die halbe Seite auf dem Full-Page-Shot unsichtbar oder leer.
DURCHSCROLLEN = """
async () => {
  const schritt = Math.round(window.innerHeight * 0.8);
  for (let y = 0; y < document.body.scrollHeight; y += schritt) {
    window.scrollTo(0, y);
    await new Promise(r => setTimeout(r, 120));
  }
  window.scrollTo(0, document.body.scrollHeight);
  await new Promise(r => setTimeout(r, 400));
  window.scrollTo(0, 0);
  await new Promise(r => setTimeout(r, 400));
}
"""

# Bilder, die noch im Flug sind, abwarten - sonst landen graue Kacheln
# im Screenshot.
#
# Das Limit ist Pflicht, nicht Vorsicht: decode() auf einem Bild mit
# loading="lazy", das ausserhalb des Viewports steht, loest sich unter
# Umstaenden nie auf - weder erfuellt noch abgelehnt. Ein .catch() hilft
# dagegen nicht, und page.evaluate() hat von sich aus kein Zeitlimit.
# Genau daran hing der 390px-Lauf minutenlang (ein TMDB-Poster weit
# unten auf der Seite).
BILDER_ABWARTEN = """
() => {
  const offen = Array.from(document.images).filter(img => !img.complete);
  const fertig = Promise.all(offen.map(img => img.decode().catch(() => null)));
  const limit = new Promise(r => setTimeout(() => r('limit'), 8000));
  return Promise.race([fertig, limit]).then(e => e === 'limit' ? offen.length : 0);
}
"""


def seite_vorbereiten(page, url: str, wartezeit: float) -> None:
    """Seite oeffnen, komplett durchscrollen, Bilder abwarten, ruhen lassen."""
    page.goto(url, wait_until="load", timeout=60_000)
    try:
        page.wait_for_load_state("networkidle", timeout=15_000)
    except Exception:
        # Manche Drittanbieter-Skripte halten die Verbindung offen.
        # Kein Grund abzubrechen - wir warten unten ohnehin noch.
        pass

    page.evaluate(DURCHSCROLLEN)
    haengend = page.evaluate(BILDER_ABWARTEN)
    if haengend:
        print(f"  ..  {haengend} Bild(er) nicht fertig geladen, weiter nach Limit")

    # Die geforderte Ruhepause: Animationen auslaufen lassen.
    page.wait_for_timeout(int(wartezeit * 1000))


def sektionen_lesen(page) -> list[str]:
    return page.eval_on_selector_all(
        SEKTIONS_SELEKTOR, "nodes => nodes.map(n => n.id)"
    )


def ansicht_schiessen(browser, name: str, konfig: dict, url: str,
                      ziel: Path, wartezeit: float) -> None:
    kontext = browser.new_context(
        viewport=konfig["viewport"],
        device_scale_factor=1,
        is_mobile=konfig["mobil"],
        has_touch=konfig["mobil"],
        locale="de-DE",
    )
    # Der Ladebildschirm der Startseite laeuft nur beim ersten Besuch je
    # Sitzung. Fuer Screenshots wird er uebersprungen: sonst zeigte jede
    # Aufnahme den Vorhang statt der Seite, und das Scrollen waere
    # waehrenddessen gesperrt. Geprueft wird das Intro mit eigenen Proben.
    kontext.add_init_script(
        "try { sessionStorage.setItem('intro-gesehen', '1'); } catch (e) {}"
    )

    page = kontext.new_page()

    print(f"\n[{name}px] {url}")
    seite_vorbereiten(page, url, wartezeit)

    # Der Hero zuerst, als reine Viewport-Aufnahme ohne Scrollen.
    #
    # Er ist die einzige Sektion, die ihre Hoehe aus dem Fenster nimmt
    # (height: 100vh), und die einzige mit Parallaxe. Beides macht ihn
    # abhaengig vom Aufnahmezustand statt nur vom Layout, und im
    # Full-Page-Bild steht er zwischen 9000 Pixeln Seite - man sieht ihn
    # dort nie so, wie ein Besucher ihn sieht.
    #
    # Nachgemessen mit der Playwright-Version von August 2026 stimmen
    # die beiden Aufnahmen exakt ueberein: Abweichung 0.00, der
    # Namenszug sitzt in beiden auf derselben Zeile, offsetHeight
    # bleibt bei 900. Chromium nimmt Full-Page ueber
    # captureBeyondViewport auf und fasst den Layout-Viewport dabei
    # nicht an, 100vh bleibt also die Fensterhoehe. Die Aufnahme hier
    # ist trotzdem die, der zu trauen ist - sie haengt an keiner
    # dieser Zusicherungen. Sollte Chromium je auf die alte
    # Umschalt-Strategie zurueckfallen (sie greift ab etwa 16384px
    # Seitenhoehe; die Startseite liegt bei 9000 auf 1440px und 9800
    # auf 390px), waere der Hero im Full-Page-Bild verzerrt und hier
    # weiterhin richtig.
    hero = ziel / f"{name}-hero.png"
    page.screenshot(path=str(hero))
    print(f"  ok  {hero.name}")

    voll = ziel / f"{name}-full.png"
    # Zweimal, und nur die zweite Aufnahme zaehlt.
    #
    # Bei langen Seiten laesst Chromium in der ersten Full-Page-Aufnahme
    # regelmaessig Bilder weit unterhalb des Viewports weg - sie sind
    # geladen (complete, naturalWidth > 0) und sichtbar (opacity 1), aber
    # zum Aufnahmezeitpunkt nicht rasterisiert. Welche fehlen, wechselt
    # von Lauf zu Lauf. Im Bild sehen sie aus wie leere Kacheln, was
    # schon zweimal zu einer Fehlersuche an der Seite gefuehrt hat,
    # obwohl die Seite in Ordnung war.
    #
    # Die erste Aufnahme erzwingt die Rasterung, die zweite ist
    # vollstaendig. Gemessen: erster Durchgang 9 leere Kacheln, zweiter
    # und dritter keine.
    page.screenshot(path=str(voll), full_page=True)
    page.screenshot(path=str(voll), full_page=True)
    print(f"  ok  {voll.name}")

    for sektions_id in sektionen_lesen(page):
        element = page.locator(f"#{sektions_id}")
        try:
            element.scroll_into_view_if_needed(timeout=5_000)
            # Kurz atmen lassen: die fade-in-Animation startet erst beim
            # Sichtbarwerden, ein sofortiger Shot zeigt sie halbtransparent.
            page.wait_for_timeout(int(wartezeit * 1000))
            pfad = ziel / f"{name}-{sektions_id}.png"
            element.screenshot(path=str(pfad), timeout=SEKTIONS_ZEITLIMIT_MS)
            print(f"  ok  {pfad.name}")
        except Exception as fehler:
            # Weitermachen statt abbrechen - der Full-Page-Shot steht schon.
            grund = type(fehler).__name__
            print(f"  --  {sektions_id} uebersprungen ({grund})")

    kontext.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--url", default=STANDARD_URL,
                        help=f"Zu schiessende Seite (Standard: {STANDARD_URL})")
    parser.add_argument("--out", default=str(STANDARD_ZIEL), type=Path,
                        help="Zielordner (Standard: screenshots/)")
    parser.add_argument("--wait", default=2.0, type=float,
                        help="Ruhepause in Sekunden vor jedem Shot (Standard: 2)")
    parser.add_argument("--only", choices=sorted(ANSICHTEN),
                        help="Nur eine Breite schiessen")
    args = parser.parse_args()

    ziel = Path(args.out)
    ziel.mkdir(parents=True, exist_ok=True)

    ansichten = {args.only: ANSICHTEN[args.only]} if args.only else ANSICHTEN

    with sync_playwright() as p:
        browser = p.chromium.launch()
        for name, konfig in ansichten.items():
            ansicht_schiessen(browser, name, konfig, args.url, ziel, args.wait)
        browser.close()

    print(f"\nFertig. Bilder in {ziel}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
