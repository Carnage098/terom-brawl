import os
import sqlite3
import random
import discord

from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
from datetime import datetime
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)
pending_matches = {}
conn = sqlite3.connect("database.db")
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS joueurs (
    user_id TEXT PRIMARY KEY,
    pseudo TEXT NOT NULL,
    points INTEGER DEFAULT 0,
    victoires INTEGER DEFAULT 0,
    defaites INTEGER DEFAULT 0,
    serie INTEGER DEFAULT 0,
    streak_max INTEGER DEFAULT 0,
    grade TEXT DEFAULT 'Recrue',
    teromik_coins INTEGER DEFAULT 0
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS historique_duels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    joueur1 TEXT,
    joueur2 TEXT,
    resultat TEXT,
    plateforme TEXT,
    date TEXT
)
""")
try:
    cursor.execute("""
    ALTER TABLE joueurs
    ADD COLUMN dernier_daily TEXT
    """)
except:
    pass
cursor.execute("""
CREATE TABLE IF NOT EXISTS matchs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    joueur_id TEXT,
    adversaire_id TEXT,
    plateforme TEXT,
    resultat TEXT,
    points INTEGER,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS saisons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT,
    date_debut TEXT,
    date_fin TEXT,
    active INTEGER DEFAULT 1
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS trophees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    joueur_id TEXT,
    nom TEXT,
    date_obtention TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS equipes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT UNIQUE,
    points INTEGER DEFAULT 0
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS inventaire (
    user_id TEXT,
    objet TEXT
)
""")


cursor.execute("""
CREATE TABLE IF NOT EXISTS titres (
    user_id TEXT PRIMARY KEY,
    titre TEXT
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS jackpot_global (
    id INTEGER PRIMARY KEY,
    montant INTEGER DEFAULT 0
)
""")

cursor.execute("""
INSERT OR IGNORE INTO jackpot_global (
    id,
    montant
)
VALUES (1, 0)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS defis (
    lanceur_id TEXT,
    cible_id TEXT
)
""")

conn.commit()
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
@bot.event
async def on_ready():

    print(f"✅ Connecté en tant que {bot.user}")

    try:
        synced = await bot.tree.sync()
        print(f"✅ {len(synced)} commandes synchronisées")
    except Exception as e:
        print(e)

@bot.tree.command(
    name="inscription",
    description="S'inscrire à TeRom-Brawl"
)
async def inscription(interaction: discord.Interaction):

    await interaction.response.defer(ephemeral=True)

    user_id = str(interaction.user.id)
    pseudo = interaction.user.display_name

    cursor.execute(
        "SELECT * FROM joueurs WHERE user_id=?",
        (user_id,)
    )

    joueur = cursor.fetchone()

    if joueur:
        await interaction.followup.send(
            "❌ Tu es déjà inscrit à TeRom-Brawl.",
            ephemeral=True
        )
        return

    cursor.execute(
        """
        INSERT INTO joueurs (
            user_id,
            pseudo
        )
        VALUES (?, ?)
        """,
        (
            user_id,
            pseudo
        )
    )

    conn.commit()

    cursor.execute("SELECT COUNT(*) FROM joueurs")
    print("JOUEURS :", cursor.fetchone()[0])

    await interaction.followup.send(
        f"⚔️ Bienvenue sur TeRom-Brawl !\n\n"
        f"👤 Joueur : {pseudo}\n\n"
        f"🎖️ Grade : Recrue\n"
        f"📈 Points : 0\n\n"
        f"Bonne chance dans l'arène !",
        ephemeral=True
    )
@bot.tree.command(
    name="profil",
    description="Voir ton profil"
)
async def profil(interaction: discord.Interaction):

    user_id = str(interaction.user.id)

    cursor.execute(
        "SELECT * FROM joueurs WHERE user_id=?",
        (user_id,)
    )

    joueur = cursor.fetchone()

    if not joueur:
        await interaction.response.send_message(
            "❌ Tu n'es pas inscrit à TeRom-Brawl.",
            ephemeral=True
        )
        return

    points = joueur[2]
    victoires = joueur[3]
    defaites = joueur[4]
    serie = joueur[5]
    coins = joueur[8]
    meilleure_serie = joueur[6]
    grade = get_grade(points)

    cursor.execute("""
    SELECT objet
    FROM inventaire
    WHERE user_id=?
    AND objet='🏆 Terrorageux All Time'
    """, (user_id,))

    trophee = cursor.fetchone()

    if trophee:
        ligne_trophee = "\n🏆 Terrorageux All Time\n"
    else:
        ligne_trophee = ""

    cursor.execute("""
    SELECT titre
    FROM titres
    WHERE user_id=?
    """, (user_id,))

    titre_data = cursor.fetchone()

    if titre_data:
        titre = titre_data[0]
    else:
        titre = "Aucun"

    total_matchs = victoires + defaites

    if total_matchs > 0:
        ratio = round((victoires / total_matchs) * 100)
    else:
        ratio = 0

    cursor.execute("""
    SELECT COUNT(*) + 1
    FROM joueurs
    WHERE points > ?
    """, (points,))

    rang = cursor.fetchone()[0]

    await interaction.response.send_message(
        f"""
👤 **{joueur[1]}**

👑 Titre : {titre}
{ligne_trophee}

🏆 Rang : #{rang}

🎖️ Grade : {grade}
📈 Points : {points}

✅ Victoires : {victoires}
❌ Défaites : {defaites}

📊 Ratio : {ratio}%

🔥 Série actuelle : {serie}

🏅 Meilleure série : {meilleure_serie}

🪙 TeRomik Coins : {coins}
""",
        ephemeral=True
    )
@bot.tree.command(
    name="resultat",
    description="Déclarer un résultat de duel"
)
@app_commands.describe(
    resultat="Victoire ou Défaite",
    plateforme="Plateforme utilisée",
    adversaire="Ton adversaire"
)
@app_commands.choices(
    resultat=[
        app_commands.Choice(name="Victoire", value="victoire"),
        app_commands.Choice(name="Défaite", value="defaite")
    ],
    plateforme=[
        app_commands.Choice(name="YGO Omega", value="omega"),
        app_commands.Choice(name="Dueling Book", value="duelingbook"),
        app_commands.Choice(name="EDOPro", value="edopro"),
        app_commands.Choice(name="Master Duel", value="masterduel"),
        app_commands.Choice(name="Remote Duel", value="remote")
    ]
)
async def resultat(
    interaction: discord.Interaction,
    resultat: app_commands.Choice[str],
    plateforme: app_commands.Choice[str],
    adversaire: discord.Member
):

    user_id = str(interaction.user.id)

    cursor.execute(
        "SELECT * FROM joueurs WHERE user_id=?",
        (user_id,)
    )
    joueur = cursor.fetchone()

    if not joueur:
        await interaction.response.send_message(
            "❌ Tu dois être inscrit.",
            ephemeral=True
        )
        return

    if adversaire.id == interaction.user.id:
        await interaction.response.send_message(
            "❌ Tu ne peux pas te défier toi-même.",
            ephemeral=True
        )
        return

    cursor.execute(
        "SELECT * FROM joueurs WHERE user_id=?",
        (str(adversaire.id),)
    )
    adversaire_db = cursor.fetchone()

    if not adversaire_db:
        await interaction.response.send_message(
            "❌ Cet adversaire n'est pas inscrit.",
            ephemeral=True
        )
        return

    gain = random.randint(10, 100)
    perte = random.randint(1, 50)

    def generer_coins():
        roll = random.randint(1, 100)

        if roll <= 50:
            return random.randint(50, 150)
        elif roll <= 80:
            return random.randint(151, 300)
        elif roll <= 95:
            return random.randint(301, 600)
        elif roll <= 99:
            return random.randint(601, 900)

        return 1000

    coins_gagnes_joueur = generer_coins()
    coins_gagnes_adv = generer_coins()

    points_joueur = joueur[2]
    victoires_joueur = joueur[3]
    defaites_joueur = joueur[4]
    serie_joueur = joueur[5]
    streak_max_joueur = joueur[6]
    coins_joueur = joueur[8]

    points_adv = adversaire_db[2]
    victoires_adv = adversaire_db[3]
    defaites_adv = adversaire_db[4]
    serie_adv = adversaire_db[5]
    coins_adv = adversaire_db[8]

    if resultat.value == "victoire":
        points_joueur += gain
        victoires_joueur += 1
        serie_joueur += 1

        if serie_joueur > streak_max_joueur:
            streak_max_joueur = serie_joueur

        points_adv = max(0, points_adv - perte)
        defaites_adv += 1
        serie_adv = 0

        gagnant = interaction.user.mention
        perdant = adversaire.mention

    else:
        points_joueur = max(0, points_joueur - perte)
        defaites_joueur += 1
        serie_joueur = 0

        points_adv += gain
        victoires_adv += 1
        serie_adv += 1

        gagnant = adversaire.mention
        perdant = interaction.user.mention

    coins_joueur += coins_gagnes_joueur
    coins_adv += coins_gagnes_adv

    grade_joueur = get_grade(points_joueur)
    grade_adv = get_grade(points_adv)

    cursor.execute("""
    UPDATE joueurs
    SET points=?,
        victoires=?,
        defaites=?,
        serie=?,
        streak_max=?,
        grade=?,
        teromik_coins=?
    WHERE user_id=?
    """, (
        points_joueur,
        victoires_joueur,
        defaites_joueur,
        serie_joueur,
        streak_max_joueur,
        grade_joueur,
        coins_joueur,
        user_id
    ))

    cursor.execute("""
    UPDATE joueurs
    SET points=?,
        victoires=?,
        defaites=?,
        serie=?,
        grade=?,
        teromik_coins=?
    WHERE user_id=?
    """, (
        points_adv,
        victoires_adv,
        defaites_adv,
        serie_adv,
        grade_adv,
        coins_adv,
        str(adversaire.id)
    ))

    cursor.execute("""
    INSERT INTO matchs (
        joueur_id,
        adversaire_id,
        plateforme,
        resultat,
        points
    )
    VALUES (?, ?, ?, ?, ?)
    """, (
        user_id,
        str(adversaire.id),
        plateforme.value,
        resultat.value,
        gain if resultat.value == "victoire" else -perte
    ))
    cursor.execute("""
    INSERT INTO historique_duels (
        joueur1,
        joueur2,
        resultat,
        plateforme,
        date
    )
    VALUES (?, ?, ?, ?, ?)
    """, (
        interaction.user.display_name,
        adversaire.display_name,
        resultat.value,
        plateforme.value,
        datetime.now().strftime("%d/%m/%Y %H:%M")
    ))
cursor.execute("""
INSERT INTO historique_duels (
    joueur1,
    joueur2,
    resultat,
    plateforme,
    date
)
VALUES (?, ?, ?, ?, ?)
""", (
    interaction.user.display_name,
    adversaire.display_name,
    resultat.value,
    plateforme.value,
    datetime.now().strftime("%d/%m/%Y %H:%M")
))
# ⚔️ Centurion (100 victoires)

if victoires_joueur >= 100:

    cursor.execute("""
    INSERT INTO inventaire (
        user_id,
        objet
    )
    SELECT ?, ?
    WHERE NOT EXISTS (
        SELECT 1
        FROM inventaire
        WHERE user_id=?
        AND objet=?
    )
    """, (
        user_id,
        "⚔️ Centurion",
        user_id,
        "⚔️ Centurion"
    ))

# 🔥 Invaincu (20 victoires de suite)

if streak_max_joueur >= 20:

    cursor.execute("""
    INSERT INTO inventaire (
        user_id,
        objet
    )
    SELECT ?, ?
    WHERE NOT EXISTS (
        SELECT 1
        FROM inventaire
        WHERE user_id=?
        AND objet=?
    )
    """, (
        user_id,
        "🔥 Invaincu",
        user_id,
        "🔥 Invaincu"
    ))

# 💰 Magnat (100 000 Coins)

if coins_joueur >= 100000:

    cursor.execute("""
    INSERT INTO inventaire (
        user_id,
        objet
    )
    SELECT ?, ?
    WHERE NOT EXISTS (
        SELECT 1
        FROM inventaire
        WHERE user_id=?
        AND objet=?
    )
    """, (
        user_id,
        "💰 Magnat",
        user_id,
        "💰 Magnat"
    ))

# ☠️ Terrorageux (100 000 points)

if points_joueur >= 100000:

    cursor.execute("""
    INSERT INTO inventaire (
        user_id,
        objet
    )
    SELECT ?, ?
    WHERE NOT EXISTS (
        SELECT 1
        FROM inventaire
        WHERE user_id=?
        AND objet=?
    )
    """, (
        user_id,
        "☠️ Terrorageux",
        user_id,
        "☠️ Terrorageux"
    ))
    conn.commit()
titres_debloques.append("⚔️ Centurion")

jackpot_message = ""

if coins_gagnes_joueur == 1000:
        jackpot_message += "\n🎰 JACKPOT DU JOUEUR ! +1000 Coins"

if coins_gagnes_adv == 1000:
        jackpot_message += "\n🎰 JACKPOT DE L'ADVERSAIRE ! +1000 Coins"

    await interaction.response.send_message(
        f"⚔️ Duel enregistré\n\n"
        f"🏆 Gagnant : {gagnant}\n"
        f"📈 Gain : +{gain} points\n\n"
        f"💀 Perdant : {perdant}\n"
        f"📉 Perte : -{perte} points\n\n"
        f"👤 {interaction.user.display_name} : +{coins_gagnes_joueur} Coins\n"
        f"👤 {adversaire.display_name} : +{coins_gagnes_adv} Coins\n"
        f"{jackpot_message}\n\n"
        f"🎮 Plateforme : {plateforme.name}"
    )
@bot.tree.command(
    name="classement",
    description="Voir le classement TeRom-Brawl"
)
async def classement(interaction: discord.Interaction):

    cursor.execute("""
    SELECT pseudo, points
    FROM joueurs
    ORDER BY points DESC
    LIMIT 10
    """)

    joueurs = cursor.fetchall()

    if not joueurs:
        await interaction.response.send_message(
            "❌ Aucun joueur inscrit."
        )
        return

    message = "🏆 **Classement TeRom-Brawl**\n\n"

    medailles = ["🥇", "🥈", "🥉"]

    for index, joueur in enumerate(joueurs, start=1):

        pseudo = joueur[0]
        points = joueur[1]

        if index <= 3:
            rang = medailles[index - 1]
        else:
            rang = f"#{index}"

        message += (
            f"{rang} **{pseudo}**\n"
            f"📈 {points} points\n\n"
        )

    await interaction.response.send_message(message)

@bot.tree.command(
    name="stats",
    description="Voir les statistiques globales"
)
async def stats(interaction: discord.Interaction):

    cursor.execute("SELECT COUNT(*) FROM joueurs")
    nb_joueurs = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM matchs")
    nb_matchs = cursor.fetchone()[0]

    cursor.execute("""
    SELECT pseudo, points
    FROM joueurs
    ORDER BY points DESC
    LIMIT 1
    """)

    leader = cursor.fetchone()

    if leader:
        leader_nom = leader[0]
        leader_points = leader[1]
    else:
        leader_nom = "Aucun"
        leader_points = 0

    await interaction.response.send_message(
        f"""
📊 **Statistiques TeRom-Brawl**

👥 Joueurs inscrits : **{nb_joueurs}**

⚔️ Matchs joués : **{nb_matchs}**

👑 Leader actuel : **{leader_nom}**

📈 Points du leader : **{leader_points}**
"""
    )

@bot.tree.command(
    name="historique",
    description="Voir les 10 derniers duels"
)
async def historique(interaction: discord.Interaction):

    cursor.execute("""
    SELECT joueur_id,
           adversaire_id,
           plateforme,
           resultat
    FROM matchs
    ORDER BY id DESC
    LIMIT 10
    """)

    matchs = cursor.fetchall()

    if not matchs:
        await interaction.response.send_message(
            "❌ Aucun duel enregistré."
        )
        return

    message = "⚔️ **10 derniers duels**\n\n"

    plateformes = {
        "omega": "YGO Omega",
        "duelingbook": "Dueling Book",
        "edopro": "EDOPro",
        "masterduel": "Master Duel",
        "remote": "Remote Duel"
    }

    for match in matchs:

        joueur_id = int(match[0])
        adversaire_id = int(match[1])

        joueur = bot.get_user(joueur_id)
        adversaire = bot.get_user(adversaire_id)

        joueur_nom = joueur.name if joueur else "Inconnu"
        adversaire_nom = adversaire.name if adversaire else "Inconnu"

        resultat = "🏆" if match[3] == "victoire" else "💀"

        plateforme = plateformes.get(
            match[2],
            match[2]
        )

        message += (
            f"{resultat} {joueur_nom} vs {adversaire_nom}\n"
            f"🎮 {plateforme}\n\n"
        )

    await interaction.response.send_message(message)

@bot.tree.command(
    name="fiche",
    description="Voir la fiche d'un joueur"
)
async def fiche(
    interaction: discord.Interaction,
    joueur: discord.Member
):

    cursor.execute(
        "SELECT * FROM joueurs WHERE user_id=?",
        (str(joueur.id),)
    )

    data = cursor.fetchone()

    if not data:
        await interaction.response.send_message(
            "❌ Ce joueur n'est pas inscrit."
        )
        return

    points = data[2]
    victoires = data[3]
    defaites = data[4]

    total = victoires + defaites

    if total > 0:
        ratio = round((victoires / total) * 100)
    else:
        ratio = 0

    cursor.execute("""
    SELECT COUNT(*) + 1
    FROM joueurs
    WHERE points > ?
    """, (points,))

    rang = cursor.fetchone()[0]

    await interaction.response.send_message(
        f"""
👤 **{joueur.display_name}**

🏆 Rang : #{rang}
🎖️ Grade : {get_grade(points)}
📈 Points : {points}

✅ Victoires : {victoires}
❌ Défaites : {defaites}

📊 Ratio : {ratio}%

🔥 Série : {data[5]}
🪙 TeRomik Coins : {data[8]}
"""
    )
@bot.tree.command(
    name="convertir",
    description="Convertir des TeRomik Coins en points"
)
async def convertir(
    interaction: discord.Interaction,
    montant: int
):

    user_id = str(interaction.user.id)

    cursor.execute(
        "SELECT * FROM joueurs WHERE user_id=?",
        (user_id,)
    )

    joueur = cursor.fetchone()

    if not joueur:
        await interaction.response.send_message(
            "❌ Tu n'es pas inscrit.",
            ephemeral=True
        )
        return

    if montant <= 0:
        await interaction.response.send_message(
            "❌ Montant invalide.",
            ephemeral=True
        )
        return

    coins = joueur[8]

    if montant > coins:
        await interaction.response.send_message(
            f"❌ Tu ne possèdes que {coins} TeRomik Coins.",
            ephemeral=True
        )
        return

    points_gagnes = montant // 100

    if points_gagnes <= 0:
        await interaction.response.send_message(
            "❌ Il faut au moins 100 coins pour obtenir 1 point.",
            ephemeral=True
        )
        return

    nouveaux_coins = coins - montant
    nouveaux_points = joueur[2] + points_gagnes

    nouveau_grade = get_grade(nouveaux_points)

    cursor.execute("""
    UPDATE joueurs
    SET points=?,
        teromik_coins=?,
        grade=?
    WHERE user_id=?
    """, (
        nouveaux_points,
        nouveaux_coins,
        nouveau_grade,
        user_id
    ))

    conn.commit()

    await interaction.response.send_message(
        f"""
💱 Conversion effectuée

🪙 Coins dépensés : {montant}

📈 Points gagnés : +{points_gagnes}

💰 Coins restants : {nouveaux_coins}

🎖️ Grade actuel : {nouveau_grade}
"""
    )
@bot.tree.command(
    name="daily",
    description="Récupérer ta récompense quotidienne"
)
async def daily(interaction: discord.Interaction):

    user_id = str(interaction.user.id)

    cursor.execute(
        "SELECT * FROM joueurs WHERE user_id=?",
        (user_id,)
    )

    joueur = cursor.fetchone()

    if not joueur:
        await interaction.response.send_message(
            "❌ Tu n'es pas inscrit.",
            ephemeral=True
        )
        return

    dernier_daily = joueur[9]

    maintenant = datetime.utcnow()

    if dernier_daily:

        dernier_daily = datetime.fromisoformat(dernier_daily)

        if maintenant - dernier_daily < timedelta(hours=24):

            restant = timedelta(hours=24) - (
                maintenant - dernier_daily
            )

            heures = restant.seconds // 3600
            minutes = (restant.seconds % 3600) // 60

            await interaction.response.send_message(
                f"⏳ Tu pourras récupérer ton prochain daily dans {heures}h {minutes}min.",
                ephemeral=True
            )
            return

    gain = random.randint(250, 1000)

    nouveaux_coins = joueur[8] + gain

    cursor.execute("""
    UPDATE joueurs
    SET teromik_coins=?,
        dernier_daily=?
    WHERE user_id=?
    """, (
        nouveaux_coins,
        maintenant.isoformat(),
        user_id
    ))

    conn.commit()

    await interaction.response.send_message(
        f"""
🎁 Récompense quotidienne

🪙 +{gain} TeRomik Coins

💰 Nouveau solde : {nouveaux_coins}
"""
    )

@bot.tree.command(
    name="roulette",
    description="Miser des TeRomik Coins"
)
async def roulette(
    interaction: discord.Interaction,
    mise: int
):

    user_id = str(interaction.user.id)

    cursor.execute(
        "SELECT * FROM joueurs WHERE user_id=?",
        (user_id,)
    )

    joueur = cursor.fetchone()

    if not joueur:
        await interaction.response.send_message(
            "❌ Tu n'es pas inscrit.",
            ephemeral=True
        )
        return

    if mise <= 0:
        await interaction.response.send_message(
            "❌ Mise invalide.",
            ephemeral=True
        )
        return

    coins = joueur[8]

    if mise > coins:
        await interaction.response.send_message(
            f"❌ Tu ne possèdes que {coins} TeRomik Coins.",
            ephemeral=True
        )
        return


    cursor.execute("""
    SELECT montant
    FROM jackpot_global
    WHERE id=1
    """)

    jackpot = cursor.fetchone()[0]

    jackpot += mise // 20

    cursor.execute("""
    UPDATE jackpot_global
    SET montant=?
    WHERE id=1
    """, (jackpot,))

    roll = random.randint(1, 100)

    if roll <= 50:
        gain = -mise
        resultat = "💥 PERDU"

    elif roll <= 85:
        gain = mise
        resultat = "🎉 GAGNÉ x2"

    elif roll <= 95:
        gain = mise * 2
        resultat = "🔥 GAGNÉ x3"

    elif roll <= 99:
        gain = mise * 4
        resultat = "💎 GAGNÉ x5"

    else:
        gain = mise * 9
        resultat = "🎰 JACKPOT x10"

    nouveaux_coins = coins + gain

    jackpot_message = ""
cursor.execute("""
INSERT INTO inventaire (
    user_id,
    objet
)
SELECT ?, ?
WHERE NOT EXISTS (
    SELECT 1
    FROM inventaire
    WHERE user_id=?
    AND objet=?
)
""", (
    user_id,
    "🎰 Béni du Jackpot",
    user_id,
    "🎰 Béni du Jackpot"
))
    if random.randint(1, 5000) == 1:

        cursor.execute("""
        SELECT montant
        FROM jackpot_global
        WHERE id=1
        """)

        jackpot = cursor.fetchone()[0]

        nouveaux_coins += jackpot

        cursor.execute("""
        UPDATE jackpot_global
        SET montant=0
        WHERE id=1
        """)

       jackpot_message += """

🏆 TITRE SECRET DÉBLOQUÉ

🎰 Béni du Jackpot

"Les probabilités se sont inclinées devant toi."
"""

    cursor.execute("""
    UPDATE joueurs
    SET teromik_coins=?
    WHERE user_id=?
    """, (
        nouveaux_coins,
        user_id
    ))

    conn.commit()

    await interaction.response.send_message(
        f"""
🎲 Roulette TeRom-Brawl

👤 {interaction.user.mention}

💰 Mise : {mise}

{resultat}

🪙 Variation : {gain:+}

💼 Nouveau solde : {nouveaux_coins}

{jackpot_message}
"""
    )
@bot.tree.command(
    name="shop",
    description="Voir la boutique TeRom-Brawl"
)
async def shop(interaction: discord.Interaction):

    await interaction.response.send_message(
        """
🛒 **Boutique TeRom-Brawl**

📈 Booster Points — 2000 Coins

⚔️ Booster +50 Victoires — 10000 Coins

❤️ TeRomik Fan — 5000 Coins

⚔️ Terochasseur de Duels — 10000 Coins

🔥 Maître Tero — 25000 Coins

👑 TeroRoi de l'Arène — 50000 Coins

🌌 Tero-Seigneur des Dimensions — 100000 Coins

🏆 Terrorageux All Time — 100000 Coins
"""
    )
@bot.tree.command(
    name="acheter",
    description="Acheter un objet de la boutique"
)
@app_commands.choices(
    objet=[
        app_commands.Choice(
            name="📈 Booster Points (2000 Coins)",
            value="booster_points"
        ),
        app_commands.Choice(
            name="⚔️ Booster de Victoires (10000 Coins)",
            value="booster_victoires"
        ),
        app_commands.Choice(
            name="✍️ Booster Signé par TeRomik (15000 Coins)",
            value="booster_teromik"
        ),
        app_commands.Choice(
            name="❤️ TeRomik Fan (5000 Coins)",
            value="teromik_fan"
        ),
        app_commands.Choice(
            name="⚔️ Terochasseur de Duels (10000 Coins)",
            value="terochasseur"
        ),
        app_commands.Choice(
            name="🔥 Maître Tero (25000 Coins)",
            value="maitre_tero"
        ),
        app_commands.Choice(
            name="👑 TeroRoi de l'Arène (50000 Coins)",
            value="teroroi"
        ),
        app_commands.Choice(
            name="🌌 Tero-Seigneur des Dimensions (100000 Coins)",
            value="tero_seigneur"
        ),
        app_commands.Choice(
            name="🏆 Terrorageux All Time (100000 Coins)",
            value="terrorageux_all_time"
        )
    ]
)
async def acheter(
    interaction: discord.Interaction,
    objet: app_commands.Choice[str]
):

    objet = objet.value

    user_id = str(interaction.user.id)

    cursor.execute(
        "SELECT * FROM joueurs WHERE user_id=?",
        (user_id,)
    )

    joueur = cursor.fetchone()

    if not joueur:
        await interaction.response.send_message(
            "❌ Tu n'es pas inscrit.",
            ephemeral=True
        )
        return

    coins = joueur[8]

    prix = {
        "booster_points": 2000,
        "booster_victoires": 10000,
        "booster_teromik": 15000,
        "teromik_fan": 5000,
        "terochasseur": 10000,
        "maitre_tero": 25000,
        "teroroi": 50000,
        "tero_seigneur": 100000,
        "terrorageux_all_time": 100000
    }

    if coins < prix[objet]:
        await interaction.response.send_message(
            f"❌ Il te faut {prix[objet]} Coins.",
            ephemeral=True
        )
        return

    coins -= prix[objet]

    # BOOSTER POINTS
    if objet == "booster_points":

        roll = random.randint(1, 100)

        if roll <= 50:
            gain = random.randint(100, 500)
        elif roll <= 80:
            gain = random.randint(501, 2000)
        elif roll <= 95:
            gain = random.randint(2001, 5000)
        elif roll <= 99:
            gain = random.randint(5001, 8000)
        else:
            gain = random.randint(8001, 10000)

        nouveaux_points = joueur[2] + gain

        cursor.execute("""
        UPDATE joueurs
        SET points=?,
            teromik_coins=?,
            grade=?
        WHERE user_id=?
        """, (
            nouveaux_points,
            coins,
            get_grade(nouveaux_points),
            user_id
        ))

        citation = ""

        if gain >= 8000:

            citations = [
                '📜 "C\'est impossible ! Personne n\'a pu gagner autant de points !"\n— Seito Kaiba\n\n💼 Woah ! Avec ça, tu peux acheter la Kaiba Corp !',
                '📜 "Grand frère ! Quelqu\'un vient de gagner une quantité absurde de points !"\n— Mokuba Kaiba',
                '📜 "Même Slifer le Dragon Céleste, le Dragon Ailé de Râ et Obélisk le Tourmenteur n\'avaient pas prévu cela !"\n— Marik Ishtar',
                '📜 "ERREUR SYSTÈME : cette récompense dépasse les limites autorisées."\n— Kaiba Corp',
                '📜 "ERREUR SYSTÈME : les comptables de la Kaiba Corp ont demandé un arrêt immédiat de cette distribution."\n— Kaiba Corp'
            ]

            citation = random.choice(citations)

        elif gain >= 5000:

            citation = (
                '📜 "Même les dimensions tremblent devant une telle récompense."\n'
                '— Tero-Seigneur des Dimensions'
            )

        elif gain >= 2000:

            citation = (
                '📜 "Voilà un exploit qui mérite le respect."\n'
                '— Jack Atlas'
            )

        conn.commit()

        await interaction.response.send_message(
            f"""
📈 Booster ouvert !

🎲 Gain obtenu : +{gain} points

💰 Coins restants : {coins}

{citation}
"""
        )

        return

    # BOOSTER VICTOIRES
    if objet == "booster_victoires":

        nouvelles_victoires = joueur[3] + 50
        nouveaux_points = joueur[2] + 1000
        nouveau_grade = get_grade(nouveaux_points)

        cursor.execute("""
        UPDATE joueurs
        SET victoires=?,
            points=?,
            grade=?,
            teromik_coins=?
        WHERE user_id=?
        """, (
            nouvelles_victoires,
            nouveaux_points,
            nouveau_grade,
            coins,
            user_id
        ))

        conn.commit()

        await interaction.response.send_message(
            f"""
⚔️ Booster utilisé !

🏆 +50 Victoires
📈 +1000 Points

💰 Coins restants : {coins}
"""
        )

        return

    # BOOSTER SIGNÉ PAR TEROMIK
    if objet == "booster_teromik":

        nouvelles_victoires = joueur[3] + 50
        nouveaux_points = joueur[2] + 25000
        nouveau_grade = get_grade(nouveaux_points)

        citations = [
            "📜 \"Une seule signature peut changer le cours du temps.\"\n— TeRomik",
            "📜 \"La Duel Academy te remercie pour cet achat !\"\n— TeRomik",
            "📜 \"Je signerai n'importe lequel de vos boosters, du moment qu'il ne vous envoie pas dans le Royaume des Ombres.\"\n— TeRomik"
        ]

        citation = random.choice(citations)

        cursor.execute("""
        UPDATE joueurs
        SET victoires=?,
            points=?,
            grade=?,
            teromik_coins=?
        WHERE user_id=?
        """, (
            nouvelles_victoires,
            nouveaux_points,
            nouveau_grade,
            coins,
            user_id
        ))

        conn.commit()

        await interaction.response.send_message(
            f"""
✍️ Booster Signé par TeRomik utilisé !

🏆 +50 Victoires
📈 +25 000 Points

🎖️ Nouveau grade : {nouveau_grade}

{citation}

💰 Coins restants : {coins}
"""
        )

        return

    # TITRES ET TROPHÉES

    noms = {
        "teromik_fan": "❤️ TeRomik Fan",
        "terochasseur": "⚔️ Terochasseur de Duels",
        "maitre_tero": "🔥 Maître Tero",
        "teroroi": "👑 TeroRoi de l'Arène",
        "tero_seigneur": "🌌 Tero-Seigneur des Dimensions",
        "terrorageux_all_time": "🏆 Terrorageux All Time"
    }

    cursor.execute("""
    INSERT INTO inventaire (
        user_id,
        objet
    )
    VALUES (?, ?)
    """, (
        user_id,
        noms[objet]
    ))

    cursor.execute("""
    UPDATE joueurs
    SET teromik_coins=?
    WHERE user_id=?
    """, (
        coins,
        user_id
    ))

    conn.commit()

    await interaction.response.send_message(
        f"""
✅ Achat effectué !

Objet obtenu :

{noms[objet]}

💰 Coins restants : {coins}
"""
    )

@bot.tree.command(
    name="equiper",
    description="Équiper un titre"
)
async def equiper(
    interaction: discord.Interaction,
    titre: str
):
    user_id = str(interaction.user.id)
    cursor.execute("""
    SELECT objet
    FROM inventaire
    WHERE user_id=?
    """, (user_id,))

    objets = [o[0] for o in cursor.fetchall()]

    if titre not in objets:
        await interaction.response.send_message(
            "❌ Tu ne possèdes pas ce titre.",
            ephemeral=True
        )
        return

    cursor.execute("""
    INSERT OR REPLACE INTO titres (
        user_id,
        titre
    )
    VALUES (?, ?)
    """, (
        user_id,
        titre
    ))
@bot.tree.command(
    name="inscrire_joueur",
    description="Inscrire un joueur à TeRom-Brawl"
)
async def inscrire_joueur(
    interaction: discord.Interaction,
    joueur: discord.Member
):

    # Remplace par ton ID Discord
    ADMIN_ID = 1455129598571450452

    if interaction.user.id != ADMIN_ID:
        await interaction.response.send_message(
            "❌ Tu n'as pas la permission d'utiliser cette commande.",
            ephemeral=True
        )
        return

    user_id = str(joueur.id)
    pseudo = joueur.name

    cursor.execute(
        "SELECT * FROM joueurs WHERE user_id=?",
        (user_id,)
    )

    existe = cursor.fetchone()

    if existe:
        await interaction.response.send_message(
            f"❌ {joueur.mention} est déjà inscrit.",
            ephemeral=True
        )
        return

    cursor.execute("""
    INSERT INTO joueurs (
        user_id,
        pseudo
    )
    VALUES (?, ?)
    """, (
        user_id,
        pseudo
    ))

    conn.commit()

    await interaction.response.send_message(
        f"""
✅ Joueur inscrit

👤 {joueur.mention}

🎖️ Grade : Recrue
📈 Points : 0
🪙 Coins : 0
"""
    )

@bot.tree.command(
    name="debug_joueurs",
    description="Debug"
)
async def debug_joueurs(interaction: discord.Interaction):

    cursor.execute("SELECT * FROM joueurs")

    joueurs = cursor.fetchall()

    await interaction.response.send_message(
        f"Nombre de joueurs : {len(joueurs)}"
    )

@bot.tree.command(
    name="mes_duels",
    description="Voir tes 20 derniers duels"
)
async def mes_duels(interaction: discord.Interaction):

    pseudo = interaction.user.display_name

    cursor.execute("""
    SELECT joueur1, joueur2, resultat, plateforme, date
    FROM historique_duels
    WHERE joueur1=? OR joueur2=?
    ORDER BY id DESC
    LIMIT 20
    """, (
        pseudo,
        pseudo
    ))

    duels = cursor.fetchall()

    if not duels:
        await interaction.response.send_message(
            "❌ Aucun duel enregistré."
        )
        return

    message = f"📜 Historique de {pseudo}\n\n"

    for duel in duels:

        joueur1 = duel[0]
        joueur2 = duel[1]
        resultat = duel[2]
        plateforme = duel[3]
        date = duel[4]

        message += (
            f"⚔️ {joueur1} vs {joueur2}\n"
            f"🏆 {resultat}\n"
            f"💻 {plateforme}\n"
            f"📅 {date}\n\n"
        )

    await interaction.response.send_message(message)

@bot.tree.command(
    name="rivalite",
    description="Voir ton historique contre un joueur"
)
async def rivalite(
    interaction: discord.Interaction,
    joueur: discord.Member
):

    moi = interaction.user.display_name
    lui = joueur.display_name

    cursor.execute("""
    SELECT joueur1, joueur2, resultat
    FROM historique_duels
    WHERE
    (joueur1=? AND joueur2=?)
    OR
    (joueur1=? AND joueur2=?)
    """, (
        moi,
        lui,
        lui,
        moi
    ))

    duels = cursor.fetchall()

    if not duels:
        await interaction.response.send_message(
            "❌ Aucun affrontement trouvé."
        )
        return

    mes_victoires = 0
    ses_victoires = 0

    for duel in duels:

        joueur1 = duel[0]
        joueur2 = duel[1]
        resultat = duel[2]

        if joueur1 == moi and resultat == "victoire":
            mes_victoires += 1

        elif joueur1 == lui and resultat == "victoire":
            ses_victoires += 1

        elif joueur1 == moi and resultat == "defaite":
            ses_victoires += 1

        elif joueur1 == lui and resultat == "defaite":
            mes_victoires += 1

    message = "🔥 **Rivalité Détectée !**\n\n"

    if len(duels) >= 20:
        message += "⚔️ Rivalité légendaire\n\n"
    elif len(duels) >= 10:
        message += "⚔️ Rivalité intense\n\n"
    elif len(duels) >= 5:
        message += "⚔️ Rivalité naissante\n\n"

    message += (
        f"👤 {moi} : {mes_victoires} victoires\n\n"
        f"👤 {lui} : {ses_victoires} victoires\n\n"
        f"📜 Total des affrontements : {len(duels)}"
    )

    await interaction.response.send_message(message)


@bot.tree.command(
    name="legendes",
    description="Voir les légendes de TeRom-Brawl"
)
async def legendes(interaction: discord.Interaction):

    # Plus de points
    cursor.execute("""
    SELECT pseudo, points
    FROM joueurs
    ORDER BY points DESC
    LIMIT 1
    """)
    roi_points = cursor.fetchone()

    # Plus de victoires
    cursor.execute("""
    SELECT pseudo, victoires
    FROM joueurs
    ORDER BY victoires DESC
    LIMIT 1
    """)
    roi_victoires = cursor.fetchone()

    # Plus grosse série
    cursor.execute("""
    SELECT pseudo, streak_max
    FROM joueurs
    ORDER BY streak_max DESC
    LIMIT 1
    """)
    roi_serie = cursor.fetchone()

    # Plus riche
    cursor.execute("""
    SELECT pseudo, teromik_coins
    FROM joueurs
    ORDER BY teromik_coins DESC
    LIMIT 1
    """)
    roi_coins = cursor.fetchone()

    await interaction.response.send_message(
        f"""
🏆 **Légendes de TeRom-Brawl**

👑 Roi des Points
{roi_points[0]} — {roi_points[1]} points

⚔️ Maître des Victoires
{roi_victoires[0]} — {roi_victoires[1]} victoires

🔥 Seigneur des Séries
{roi_serie[0]} — {roi_serie[1]} victoires consécutives

💰 Magnat des Coins
{roi_coins[0]} — {roi_coins[1]} Coins
"""
    )
@bot.tree.command(
    name="jackpot",
    description="Voir le Jackpot Mondial"
)
async def jackpot(interaction: discord.Interaction):

    cursor.execute("""
    SELECT montant
    FROM jackpot_global
    WHERE id=1
    """)

    montant = cursor.fetchone()[0]

    await interaction.response.send_message(
        f"""
🎰 Jackpot Mondial

💰 Montant actuel :
{montant} Coins
"""
    )

@bot.tree.command(
    name="topcoins",
    description="Voir les joueurs les plus riches"
)
async def topcoins(interaction: discord.Interaction):

    cursor.execute("""
    SELECT pseudo, teromik_coins
    FROM joueurs
    ORDER BY teromik_coins DESC
    LIMIT 10
    """)

    joueurs = cursor.fetchall()

    if not joueurs:
        await interaction.response.send_message(
            "❌ Aucun joueur inscrit."
        )
        return

    message = "💰 **Fortune TeRom-Brawl**\n\n"

    medailles = ["🥇", "🥈", "🥉"]

    for index, joueur in enumerate(joueurs, start=1):

        pseudo = joueur[0]
        coins = joueur[1]

        if index <= 3:
            rang = medailles[index - 1]
        else:
            rang = f"#{index}"

        message += (
            f"{rang} **{pseudo}**\n"
            f"🪙 {coins} Coins\n\n"
        )

    await interaction.response.send_message(message)



@bot.tree.command(
    name="fortune",
    description="Voir la richesse globale de TeRom-Brawl"
)
async def fortune(interaction: discord.Interaction):

    cursor.execute("""
    SELECT SUM(teromik_coins)
    FROM joueurs
    """)
    total = cursor.fetchone()[0] or 0

    cursor.execute("""
    SELECT COUNT(*)
    FROM joueurs
    """)
    nb_joueurs = cursor.fetchone()[0]

    moyenne = round(total / nb_joueurs) if nb_joueurs > 0 else 0

    cursor.execute("""
    SELECT pseudo, teromik_coins
    FROM joueurs
    ORDER BY teromik_coins DESC
    LIMIT 1
    """)
    riche = cursor.fetchone()

    await interaction.response.send_message(
        f"""
💰 **Fortune de TeRom-Brawl**

🪙 Coins en circulation :
{total}

👥 Joueurs inscrits :
{nb_joueurs}

📈 Fortune moyenne :
{moyenne} Coins

👑 Joueur le plus riche :
{riche[0]} — {riche[1]} Coins
"""
    )
@bot.tree.command(
    name="defier",
    description="Défier un joueur"
)
async def defier(
    interaction: discord.Interaction,
    joueur: discord.Member
):
    pending_matches[str(joueur.id)] = str(interaction.user.id)
    if joueur.id == interaction.user.id:
        await interaction.response.send_message(
            "❌ Tu ne peux pas te défier toi-même."
        )
        return

    cursor.execute("""
    INSERT INTO defis (
        lanceur_id,
        cible_id
    )
    VALUES (?, ?)
    """, (
        str(interaction.user.id),
        str(joueur.id)
    ))

    conn.commit()

    await interaction.response.send_message(
        f"""
⚔️ Défi envoyé !

👤 {joueur.mention}

Il peut maintenant utiliser /accepter
"""
    )
@bot.tree.command(
    name="accepter",
    description="Accepter un défi"
)
async def accepter(interaction: discord.Interaction):

    cursor.execute("""
    SELECT lanceur_id
    FROM defis
    WHERE cible_id=?
    """, (
        str(interaction.user.id),
    ))

    defi = cursor.fetchone()

    if not defi:
        await interaction.response.send_message(
            "❌ Aucun défi en attente."
        )
        return

    lanceur = await bot.fetch_user(
        int(defi[0])
    )

    cursor.execute("""
    DELETE FROM defis
    WHERE cible_id=?
    """, (
        str(interaction.user.id),
    ))

    conn.commit()

    await interaction.response.send_message(
        f"""
🔥 Duel accepté !

⚔️ {interaction.user.mention}
VS
⚔️ {lanceur.mention}

Utilisez ensuite /resultat pour déclarer le vainqueur.
"""
    )
@bot.tree.command(
    name="refuser",
    description="Refuser un défi"
)
async def refuser(interaction: discord.Interaction):

    cursor.execute("""
    DELETE FROM defis
    WHERE cible_id=?
    """, (
        str(interaction.user.id),
    ))

    conn.commit()

    await interaction.response.send_message(
        "❌ Défi refusé."
    )

bot.run(TOKEN)
