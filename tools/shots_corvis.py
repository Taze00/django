#!/usr/bin/env python3
"""Screenshot-Werkzeug fuer CORVIS - Landing (/corvis/) und App (/corvis-app/).

Gegenstueck zu tools/shots.py, das die Portfolio-Startseite fotografiert.
Der Unterschied: die App unter /corvis-app/ ist eine React-SPA hinter
Login. Das Skript holt sich deshalb per API ein JWT und legt es vor dem
ersten Rendern in den localStorage - dieselbe Stelle, aus der
`authStore.checkAuth()` es liest.

Aufruf:
    python3 tools/shots_corvis.py                       # beide Breiten
    python3 tools/shots_corvis.py --only 390
    python3 tools/shots_corvis.py --user test --password test1234

Alles landet in screenshots/corvis/ (gitignored).

Voraussetzung:
    pip install --user playwright && playwright install chromium
"""

import argparse
import json
import sys
import urllib.error
import urllib.request
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
STANDARD_ZIEL = PROJEKT_WURZEL / "screenshots" / "corvis"
STANDARD_BASIS = "http://localhost:8000"

ANSICHTEN = {
    "1440": {"viewport": {"width": 1440, "height": 900}, "mobil": False},
    "390": {"viewport": {"width": 390, "height": 844}, "mobil": True},
}

# (Dateiname, Pfad unter /corvis-app, Anmeldung noetig?)
APP_ANSICHTEN = [
    ("login", "/corvis-app/login", False),
    ("register", "/corvis-app/register", False),
    ("home", "/corvis-app/", True),
    ("workout", "/corvis-app/workout", True),
    ("exercises", "/corvis-app/exercises", True),
    ("statistics", "/corvis-app/statistics", True),
    ("profile", "/corvis-app/profile", True),
    ("training-days", "/corvis-app/training-days", True),
    ("set-progression", "/corvis-app/set-progression", True),
    ("onboarding", "/corvis-app/onboarding", True),
]

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

SEKTIONS_SELEKTOR = (
    "body > section[id], body > header[id], body > footer[id], body > nav[id]"
)


def token_holen(basis: str, nutzer: str, passwort: str) -> str:
    """JWT ueber /api/token/ besorgen - dieselbe Route wie im Frontend."""
    anfrage = urllib.request.Request(
        f"{basis}/api/token/",
        data=json.dumps({"username": nutzer, "password": passwort}).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(anfrage, timeout=15) as antwort:
            return json.load(antwort)["access"]
    except urllib.error.HTTPError as fehler:
        sys.exit(
            f"Anmeldung fehlgeschlagen ({fehler.code}). "
            f"Nutzer '{nutzer}' pruefen oder --user/--password setzen."
        )


def seite_beruhigen(page, wartezeit: float) -> None:
    try:
        page.wait_for_load_state("networkidle", timeout=15_000)
    except Exception:
        pass
    page.evaluate(DURCHSCROLLEN)
    page.wait_for_timeout(int(wartezeit * 1000))


def landing_schiessen(browser, name, konfig, basis, ziel, wartezeit):
    """Die Landing Page - wie shots.py, inkl. Einzelsektionen."""
    kontext = browser.new_context(
        viewport=konfig["viewport"], device_scale_factor=1,
        is_mobile=konfig["mobil"], has_touch=konfig["mobil"], locale="de-DE",
    )
    page = kontext.new_page()
    url = f"{basis}/corvis/"
    print(f"\n[{name}px] {url}")
    page.goto(url, wait_until="load", timeout=60_000)
    seite_beruhigen(page, wartezeit)

    # Hero als reine Viewport-Aufnahme - er ist 100vh hoch und haengt
    # damit am Fenster, nicht am Layout (siehe Kommentar in shots.py).
    pfad = ziel / f"landing-{name}-hero.png"
    page.screenshot(path=str(pfad))
    print(f"  ok  {pfad.name}")

    voll = ziel / f"landing-{name}-full.png"
    page.screenshot(path=str(voll), full_page=True)
    page.screenshot(path=str(voll), full_page=True)  # zweite zaehlt
    print(f"  ok  {voll.name}")

    ids = page.eval_on_selector_all(SEKTIONS_SELEKTOR, "n => n.map(x => x.id)")
    for sektion in ids:
        try:
            element = page.locator(f"#{sektion}")
            element.scroll_into_view_if_needed(timeout=5_000)
            page.wait_for_timeout(int(wartezeit * 1000))
            pfad = ziel / f"landing-{name}-{sektion}.png"
            element.screenshot(path=str(pfad), timeout=20_000)
            print(f"  ok  {pfad.name}")
        except Exception as fehler:
            print(f"  --  {sektion} uebersprungen ({type(fehler).__name__})")

    kontext.close()


def app_schiessen(browser, name, konfig, basis, ziel, wartezeit, token):
    """Die React-App. Geschuetzte Ansichten bekommen den Token vor dem
    ersten Rendern in den localStorage gelegt - genau dort liest
    `authStore.checkAuth()` ihn.

    Direktes page.goto() reicht dafuer seit dem Fix an `PrivateRoute`
    (Commit "fix: PrivateRoute wartet auf die Auth-Pruefung"). Vorher
    entschied die Route allein an `isAuthenticated`, das auf false
    startet - jeder Aufruf landete deshalb auf /login, und das Skript
    musste sich ueber das Formular anmelden und dann per pushState
    weiternavigieren. Der Umweg ist entfallen."""
    for datei, pfad, braucht_auth in APP_ANSICHTEN:
        kontext = browser.new_context(
            viewport=konfig["viewport"], device_scale_factor=1,
            is_mobile=konfig["mobil"], has_touch=konfig["mobil"],
            locale="de-DE",
        )
        if braucht_auth:
            kontext.add_init_script(
                f"try {{ localStorage.setItem('access_token', {token!r}); }} "
                f"catch (e) {{}}"
            )
        page = kontext.new_page()
        try:
            page.goto(f"{basis}{pfad}", wait_until="load", timeout=60_000)
            seite_beruhigen(page, wartezeit)
            ziel_datei = ziel / f"app-{name}-{datei}.png"
            page.screenshot(path=str(ziel_datei), full_page=True)
            page.screenshot(path=str(ziel_datei), full_page=True)
            gelandet = page.url.split(basis)[-1]
            if braucht_auth and gelandet.endswith("/login"):
                print(f"  !!  {datei}: auf {gelandet} gelandet statt {pfad}")
            else:
                print(f"  ok  {ziel_datei.name}")
        except Exception as fehler:
            print(f"  --  {datei} uebersprungen ({type(fehler).__name__})")
        kontext.close()


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--basis", default=STANDARD_BASIS)
    parser.add_argument("--out", default=str(STANDARD_ZIEL), type=Path)
    parser.add_argument("--wait", default=2.0, type=float)
    parser.add_argument("--only", choices=sorted(ANSICHTEN))
    parser.add_argument("--user", default="test")
    parser.add_argument("--password", default="test1234")
    parser.add_argument("--skip-landing", action="store_true")
    args = parser.parse_args()

    ziel = Path(args.out)
    ziel.mkdir(parents=True, exist_ok=True)

    token = token_holen(args.basis, args.user, args.password)
    print(f"Token fuer '{args.user}' geholt ({len(token)} Zeichen)")

    ansichten = {args.only: ANSICHTEN[args.only]} if args.only else ANSICHTEN

    with sync_playwright() as p:
        browser = p.chromium.launch()
        for name, konfig in ansichten.items():
            if not args.skip_landing:
                landing_schiessen(browser, name, konfig, args.basis, ziel,
                                  args.wait)
            print(f"\n[{name}px] App-Ansichten")
            app_schiessen(browser, name, konfig, args.basis, ziel, args.wait,
                          token)
        browser.close()

    print(f"\nFertig. Bilder in {ziel}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
