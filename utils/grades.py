def get_grade(points):

    grades = [
        (100000, "☠️ Terrorageux"),
        (95000, "Terreur Absolue"),
        (90000, "Légende Vivante"),
        (85000, "Souverain des Duels"),
        (80000, "Empereur Céleste"),
        (75000, "Maître des Dimensions"),
        (70000, "Seigneur des Arènes"),
        (65000, "Titan du Duel"),
        (60000, "Monarque des Cartes"),
        (55000, "Héraut du Chaos"),
        (50000, "Dueliste Suprême"),
        (45000, "Exécuteur des Duels"),
        (40000, "Dominateur des Dimensions"),
        (35000, "Gardien du Millenium"),
        (30000, "Roi des Ombres"),
        (25000, "Dragon Légendaire"),
        (20000, "Empereur du Duel"),
        (15000, "Champion Dimensionnel"),
        (10000, "Seigneur du Duel"),
        (5000, "Roi des Jeux"),
        (3000, "Maître"),
        (2000, "Diamant"),
        (1500, "Platine"),
        (1000, "Or"),
        (500, "Argent"),
        (250, "Bronze"),
        (0, "Recrue")
    ]

    for seuil, grade in grades:
        if points >= seuil:
            return grade
