#!/usr/bin/env python3
"""Screenshot-Werkzeug fuer die Design-Arbeit an der Startseite.

Schiesst pro Durchlauf:
  - einen Full-Page-Screenshot in 1440px Breite  -> 1440-full.png
  - einen Full-Page-Screenshot in  390px Breite  ->  390-full.png
  - je einen Einzel-Screenshot pro Sektion       -> <breite>-<section-id>.png

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
# im Screenshot. decode() faengt auch die gerade erst angestossenen.
BILDER_ABWARTEN = """
() => Promise.all(
  Array.from(document.images)
    .filter(img => !img.complete)
    .map(img => img.decode().catch(() => null))
)
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
    page.evaluate(BILDER_ABWARTEN)

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
    page = kontext.new_page()

    print(f"\n[{name}px] {url}")
    seite_vorbereiten(page, url, wartezeit)

    voll = ziel / f"{name}-full.png"
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
