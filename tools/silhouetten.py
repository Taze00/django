#!/usr/bin/env python3
"""Macht aus den beiden Midjourney-Bildern (schwarze Silhouette auf
weissem Grund) freigestellte PNGs fuer den Hero.

Zwei Dinge sind dabei nicht offensichtlich:

1. Der Weisspunkt ist nicht 255. Beim Turmbild ist der Grund 246 - ein
   blosses `alpha = 255 - helligkeit` liesse dort einen Schleier von
   Alpha 9 ueber der ganzen Flaeche stehen, also ein sichtbares
   Rechteck. Deshalb werden Schwarz- und Weisspunkt je Bild gemessen
   und die Helligkeit dazwischen auf 0..255 gestreckt. Die Grauwerte
   der Kantenglaettung bleiben dabei erhalten und werden zu
   Alpha-Zwischenwerten - genau das glaettet die Kanten.

2. Der Fernsehturm muss aus der Skyline heraus, weil er einzeln als
   eigene Ebene daneben liegt. Er steht bei x 1375..1417 und ist
   oberhalb der Dachlinie frei - unterhalb ist sein Schaft nur 22px
   breit. Also: Rechteck weiss ausmalen, und die kleine Kerbe, die im
   Haeuserband zurueckbleibt, mit Schwarz auffuellen, damit dort eine
   niedrige Hausreihe steht und kein Loch.

Aufruf: python3 tools/silhouetten.py
"""

from PIL import Image

HERE = 'static/css/images/header/'

SKYLINE_QUELLE = HERE + ('Taze_Berlin_skyline_silhouette_flat_vector_'
                         'illustration_solid_'
                         '50601b7c-8e50-4b17-8dd8-a9b4e2472fb7_1.png')
TURM_QUELLE = HERE + ('Taze_Berlin_Fernsehturm_TV_tower_silhouette_'
                      'single_isolated_s_'
                      '1b11c973-02c0-4408-9cd9-5caf55a3044d_1.png')

# Der Farbton, der in die PNGs eingebacken wird: sehr dunkel, leicht
# kuehl - Nachtstadt, nicht Druckerschwaerze. Im CSS liegen die Bilder
# zusaetzlich als Maske, dort gilt die background-color; dieser Wert
# hier zaehlt nur, wenn eine Datei einmal direkt als Bild benutzt wird.
TINTE = (10, 13, 18)

# Der Fernsehturm in der Skyline. Grosszuegig um die Kugel herum
# gemessen (Schaft 1386..1407, Kugel 1376..1417).
TURM_X0, TURM_X1 = 1373, 1420
# Bis hierhin wird der Turm weggenommen; ab hier ist das Haeuserband
# ohnehin fast geschlossen (99% dunkel) und die Kerbe wird gefuellt.
TURM_SCHNITT_Y = 505


def messe_punkte(grau):
    """Schwarz- und Weisspunkt aus dem Histogramm.

    Der Weisspunkt ist der haeufigste Wert in der oberen Haelfte - das
    ist der Grund, der den Grossteil der Flaeche ausmacht. Ein paar
    Prozent Sicherheitsabstand nach innen, damit Rauschen im Grund
    (beim Turmbild streuen einzelne Pixel bis 255) sauber auf Alpha 0
    fallen.
    """
    hist = grau.histogram()
    weiss = max(range(128, 256), key=lambda i: hist[i])
    schwarz = min((i for i in range(0, 128) if hist[i]), default=0)
    return schwarz + 2, weiss - 3


def freistellen(grau, tinte=TINTE):
    """Grauwertbild -> RGBA: dunkel wird deckend, hell wird transparent."""
    schwarz, weiss = messe_punkte(grau)
    spanne = max(weiss - schwarz, 1)

    # Nachschlagetabelle statt Rechnung je Pixel - 1,2 Mio Pixel in
    # Python einzeln waere unnoetig langsam.
    tabelle = []
    for wert in range(256):
        alpha = round((weiss - wert) * 255 / spanne)
        alpha = min(255, max(0, alpha))
        # Alles unter 6 auf null. Der Grund der Midjourney-Bilder
        # rauscht um ein, zwei Stufen; das ergibt Alpha 1..2 - unsichtbar,
        # aber getbbox() zaehlt es als Inhalt und der Zuschnitt bleibt
        # dann viel zu weit (beim Turm 490px statt gut 110px Breite).
        tabelle.append(0 if alpha < 6 else alpha)

    alpha = grau.point(tabelle)
    bild = Image.new('RGBA', grau.size, tinte + (0,))
    bild.putalpha(alpha)
    return bild


def beschneiden(bild, rand=0):
    """Auf den sichtbaren Inhalt zuschneiden."""
    kasten = bild.getchannel('A').getbbox()
    if not kasten:
        return bild
    links, oben, rechts, unten = kasten
    return bild.crop((max(0, links - rand), max(0, oben - rand),
                      min(bild.width, rechts + rand),
                      min(bild.height, unten + rand)))


def baue_skyline():
    grau = Image.open(SKYLINE_QUELLE).convert('L')
    px = grau.load()

    # Turm weg - oberhalb der Dachlinie steht er frei.
    for y in range(0, TURM_SCHNITT_Y):
        for x in range(TURM_X0, TURM_X1 + 1):
            px[x, y] = 255

    # Und die Kerbe darunter zu, damit die Haeuserzeile durchlaeuft.
    # Die Nachbarn links und rechts haben dort Dachhoehe 503..507.
    for y in range(TURM_SCHNITT_Y, grau.height):
        for x in range(TURM_X0, TURM_X1 + 1):
            px[x, y] = 0

    bild = freistellen(grau)

    # Das massive Bodenband (Zeilen 515..567, ueber die ganze Breite
    # deckend) faellt weg: im Hero sitzt die Zeile auf der Unterkante,
    # ein 50px hoher schwarzer Balken darunter waere nur ein Streifen.
    # Bei 518 stehen alle Haeuser noch vollstaendig.
    bild = bild.crop((0, 0, bild.width, 518))
    bild = beschneiden(bild)

    ziel = HERE + 'skyline-silhouette.png'
    bild.save(ziel, optimize=True)
    print(f'{ziel}  {bild.size}')


def baue_turm():
    grau = Image.open(TURM_QUELLE).convert('L')
    bild = beschneiden(freistellen(grau))
    ziel = HERE + 'fernsehturm-silhouette.png'
    bild.save(ziel, optimize=True)
    print(f'{ziel}  {bild.size}')


if __name__ == '__main__':
    baue_skyline()
    baue_turm()
