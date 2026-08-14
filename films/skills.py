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
    """Skill-Gruppen in der vorgesehenen Reihenfolge."""
    return SKILLS
