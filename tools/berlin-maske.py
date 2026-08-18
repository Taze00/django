#!/usr/bin/env python3
"""Macht aus der remove.bg-Vorschau die Maske fuer die vordere Hero-Ebene.

Warum das noetig ist: berlin-removebg-preview.png ist die Gratis-Vorschau
von remove.bg und misst nur 612x408. Im Hero wird sie auf mindestens
1440px Breite gezogen, also gut zweifach. Der Browser interpoliert dabei
linear, und aus der ohnehin kantengeglaetteten Alphakante wird ein
weicher Verlauf von rund einem Dutzend Pixeln. Sichtbar wird das dort,
wo die Dachlinie ueber den weissen Namenszug laeuft: die Haeuser sind
gestochen scharf (ihre Pixel kommen aus berlin.jpg in voller
Aufloesung), ihre Schnittkante dagegen ist ein grauer Schmier. Genau
diese Mischung liest sich als schlechte Freistellung.

Der Kniff: die Kantenglaettung der Vorlage ist kein Makel, sondern
Information - der Grauwert eines Randpixels sagt, WO in diesem Pixel die
Kante liegt. Also erst vergroessern (dabei bleibt der Verlauf erhalten
und wird glatt interpoliert), dann mit einer steilen Kennlinie wieder
zusammendruecken. Das Ergebnis ist eine Kante, die der Vorlage
subpixelgenau folgt, aber nur noch wenige Pixel breit verlaeuft - scharf
ohne Treppchen.

Nicht hochskalieren und hart schwellen (Kennlinie ganz steil): dann
faellt die Subpixel-Information weg und die Dachlinie bekommt genau die
Treppchen, die hier vermieden werden sollen.

Aufruf: python3 tools/berlin-maske.py
"""

from PIL import Image

HIER = 'static/css/images/header/'
QUELLE = HIER + 'berlin-removebg-preview.png'
ZIEL = HIER + 'berlin-maske.png'

# Vierfach. Mehr bringt nichts - die Vorlage hat nicht mehr herzugeben,
# und die Datei waechst nur. 2448x1632 deckt auch 2560px-Schirme noch
# mit Reserve ab.
FAKTOR = 4

# Die Kennlinie: Alphawerte unter UNTEN werden ganz durchsichtig, ueber
# OBEN ganz deckend, dazwischen linear. Der Abstand der beiden ist die
# Breite des Uebergangs - eng genug fuer eine scharfe Kante, weit genug,
# dass eine Kantenglaettung uebrig bleibt.
UNTEN, OBEN = 96, 160


def kennlinie(wert):
    if wert <= UNTEN:
        return 0
    if wert >= OBEN:
        return 255
    return round((wert - UNTEN) * 255 / (OBEN - UNTEN))


def main():
    quelle = Image.open(QUELLE).convert('RGBA')
    breite, hoehe = quelle.size
    gross = (breite * FAKTOR, hoehe * FAKTOR)

    alpha = quelle.getchannel('A').resize(gross, Image.LANCZOS)
    alpha = alpha.point(kennlinie)

    # Als Maske zaehlt nur der Alphakanal, die Farbe darunter ist egal -
    # durchgehend Schwarz komprimiert am besten.
    maske = Image.new('RGBA', gross, (0, 0, 0, 0))
    maske.putalpha(alpha)
    maske.save(ZIEL, optimize=True)

    print('%s -> %s  %dx%d' % (QUELLE.split('/')[-1], ZIEL.split('/')[-1],
                               *gross))


if __name__ == '__main__':
    main()
