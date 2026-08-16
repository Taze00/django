"""Skills fuer die Sektion "Was ich baue" auf der Startseite.

Steht wie `projekte.py` bewusst in Python statt im Template: Reihenfolge
und Inhalte lassen sich so aendern, ohne Markup anzufassen.

Bewusst ohne Niveau-Angaben, Balken oder Prozente - nur die Nennung.
Selbsteingestufte Prozentzahlen sagen niemandem etwas und altern
schlecht; die Gruppierung allein ordnet schon genug ein.

`marke` ist die Monospace-Zeile ueber der Gruppe, im selben Ton wie die
Sektions-Metazeilen (siehe includes/sektion-meta.html).
"""

SKILLS = [
    {
        "marke": "Entwicklung",
        "eintraege": [
            "Python",
            "Java",
            "SQL",
            "HTML & CSS",
            "JavaScript",
            "Django",
            "PostgreSQL",
            "Docker",
            "Git",
        ],
    },
    {
        "marke": "Design & Content",
        "eintraege": [
            "Photoshop",
            "Premiere Pro",
            "Adobe XD",
            "Canva",
            "Content Creation",
        ],
    },
    {
        "marke": "Werkzeuge",
        "eintraege": [
            "Visual Studio Code",
            "Notion",
            "Microsoft Office",
            "Google Analytics",
            "KI-Modelle (Claude, Copilot, ChatGPT, Gemini)",
        ],
    },
]


def get_skills():
    """Skill-Gruppen in der vorgesehenen Reihenfolge.

    Setzt zusaetzlich `zeichen`: die Laenge der Gruppe in Zeichen,
    Trenner mitgezaehlt. Daraus rechnet das Template die Laufdauer des
    Bandes (siehe .skills-spur in styles.css).

    Warum nicht einfach die Zahl der Begriffe: die Baender sollen gleich
    schnell laufen, und dafuer muss die Dauer zur zurueckgelegten
    Strecke passen. "Werkzeuge" und "Design & Content" haben beide fuenf
    Eintraege, aber "KI-Modelle (Claude, Copilot, ChatGPT, Gemini)" ist
    allein so breit wie drei andere - nach Eintraegen gerechnet liefe
    das Band ueber die Haelfte schneller. Die Zeichenzahl ist ein guter
    Ersatz fuer die Breite: gemessen liegen alle drei Gruppen bei rund
    0,065 Zeichen je Pixel.
    """
    gruppen = []
    for gruppe in SKILLS:
        eintrag = dict(gruppe)
        eintraege = eintrag["eintraege"]
        # +3 je Eintrag fuer " · " zwischen den Begriffen.
        eintrag["zeichen"] = sum(len(e) for e in eintraege) + 3 * len(eintraege)
        gruppen.append(eintrag)
    return gruppen
