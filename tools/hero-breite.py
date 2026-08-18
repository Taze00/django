#!/usr/bin/env python3
"""Prueft, ob der Namenszug im Hero in seine Spalte passt.

Seit der Nachname am Stueck steht ("VOLKMANN" statt "VOLK-" / "MANN")
ist die breiteste Zeile 5.146 Grad breit - fast doppelt so breit wie
vorher. Damit bindet nicht mehr die Fensterhoehe den Schriftgrad,
sondern die Breite der Spalte, und .container ist bei 1300px
gedeckelt: ueber etwa 1444px Fensterbreite waechst der Name nicht mehr
mit.

Ob die Rechnung in `font-size: min(...)` an .hero-zeile aufgeht, laesst
sich nicht zuverlaessig im Kopf nachvollziehen - .container hat
prozentuale Breite, eine Deckelung und ein clamp() im Innenabstand,
und die Stufe haengt an einem eigenen clamp(). Deshalb wird gemessen,
nicht gerechnet.

Meldet je Fensterbreite den Ueberhang: negativ heisst Luft, positiv
heisst, die Zeile steht ueber der Spalte und bricht um.

Aufruf: python3 tools/hero-breite.py
"""

import sys

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sys.exit(
        "playwright fehlt.\n"
        "  pip install --user --break-system-packages playwright\n"
        "  ~/.local/bin/playwright install chromium"
    )

STANDARD_URL = "http://localhost:8000/"

# Die Breiten, an denen es kippen kann: die schmalste, mit der zu
# rechnen ist, die ueblichen Geraete, und zwei jenseits der Deckelung
# von .container.
FENSTER = [(320, 700), (390, 844), (768, 1024), (1024, 768),
           (1280, 800), (1440, 900), (1440, 700), (1920, 1080),
           (2560, 1440)]

MESSUNG = """() => {
  const zeilen = [...document.querySelectorAll('.hero-name .hero-zeile')];
  const spalte = document.querySelector('.hero .container');
  const scs = getComputedStyle(spalte);
  const innen = spalte.getBoundingClientRect().width
                - parseFloat(scs.paddingLeft) - parseFloat(scs.paddingRight);
  const grad = parseFloat(getComputedStyle(zeilen[0]).fontSize);
  // Die Zeile ist ein Block; ihre eigene Breite waere die der Spalte.
  // Gemessen wird deshalb der Inhalt: der letzte Buchstabe verraet,
  // wie weit die Zeile wirklich reicht.
  const links = spalte.getBoundingClientRect().left + parseFloat(scs.paddingLeft);
  let breiteste = 0, name = '', umbrueche = 0;
  for (const z of zeilen) {
    const buchstaben = [...z.querySelectorAll('.hero-buchstabe')];
    if (!buchstaben.length) continue;
    const kaesten = buchstaben.map(b => b.getBoundingClientRect());
    // Umbruch NICHT ueber getClientRects() der Zeile pruefen: die ist
    // ein Block und hat immer genau ein Rechteck, auch wenn ihr Inhalt
    // laengst auf zwei Reihen steht. Verraeterisch sind die
    // Buchstaben - liegen sie nicht mehr alle auf derselben Hoehe, ist
    // die Zeile umgebrochen.
    const oben = kaesten.map(k => Math.round(k.top));
    const gebrochen = Math.max(...oben) - Math.min(...oben) > 2;
    if (gebrochen) umbrueche++;
    // Bei Umbruch ist die rechte Kante des letzten Buchstabens
    // unbrauchbar (er steht in der zweiten Reihe). Dann zaehlt die
    // Summe der Buchstabenbreiten plus die Einrueckung der Stufe als
    // Mass fuer das, was die Zeile ungebrochen braeuchte - ohne die
    // Stufe faellt der Wert zu klein aus und die Zeile sieht auf dem
    // Papier aus, als passte sie.
    const einzug = parseFloat(getComputedStyle(z).marginLeft) || 0;
    const breite = gebrochen
      ? kaesten.reduce((s, k) => s + k.width, 0) + einzug
      : kaesten[kaesten.length - 1].right - links;
    if (breite > breiteste) {
      breiteste = breite;
      name = buchstaben.map(b => b.textContent).join('');
    }
  }
  return {innen: innen, breite: breiteste, grad: grad, zeile: name,
          umbrueche: umbrueche};
}"""


def main() -> int:
    url = sys.argv[1] if len(sys.argv) > 1 else STANDARD_URL
    schlecht = 0
    with sync_playwright() as p:
        browser = p.chromium.launch()
        print(f"{url}\n")
        print(f"{'Fenster':>12}  {'Grad':>6}  {'Zeile':>7}  {'Spalte':>7}  "
              f"{'Ueberhang':>10}")
        for breite, hoehe in FENSTER:
            kontext = browser.new_context(viewport={"width": breite,
                                                    "height": hoehe})
            # Ohne das zeigt die Aufnahme den Intro-Vorhang statt der
            # Seite - siehe CLAUDE.md.
            kontext.add_init_script(
                "try { sessionStorage.setItem('intro-gesehen', '1'); } catch (e) {}"
            )
            seite = kontext.new_page()
            seite.goto(url, wait_until="networkidle", timeout=60_000)
            seite.wait_for_timeout(1200)
            m = seite.evaluate(MESSUNG)
            ueberhang = m["breite"] - m["innen"]
            fehler = ueberhang > 0 or m["umbrueche"] > 0
            if fehler:
                schlecht += 1
            print(f"{breite:>5}x{hoehe:<6} {m['grad']:>6.0f}  "
                  f"{m['breite']:>7.0f}  {m['innen']:>7.0f}  "
                  f"{ueberhang:>+10.0f}  "
                  f"{'BRICHT UM' if fehler else 'ok'}"
                  f"{'  (' + m['zeile'] + ')' if fehler else ''}")
            kontext.close()
        browser.close()
    print("\n" + ("Alle Breiten passen." if not schlecht
                  else f"{schlecht} Breite(n) passen nicht."))
    return 1 if schlecht else 0


if __name__ == "__main__":
    raise SystemExit(main())
