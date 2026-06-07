import os
import sqlite3
import random
import discord

from discord.ext import commands
from discord import app_commands

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

    user_id = str(interaction.user.id)
    pseudo = interaction.user.name

    cursor.execute(
        "SELECT * FROM joueurs WHERE user_id=?",
        (user_id,)
    )

    joueur = cursor.fetchone()

    if joueur:
        await interaction.response.send_message(
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

    await interaction.response.send_message(
        f"""
⚔️ Bienvenue sur TeRom-Brawl !

👤 Joueur : {pseudo}

🎖️ Grade : Recrue
📈 Points : 0

Bonne chance dans l'arène !
""",
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

    points_joueur = joueur[2]
    victoires_joueur = joueur[3]
    defaites_joueur = joueur[4]
    serie_joueur = joueur[5]

    points_adv = adversaire_db[2]
    victoires_adv = adversaire_db[3]
    defaites_adv = adversaire_db[4]
    serie_adv = adversaire_db[5]
    streak_max_joueur = joueur[6]

if resultat.value == "victoire":

    points_joueur += gain
    victoires_joueur += 1
    serie_joueur += 1

    if serie_joueur > streak_max_joueur:
        streak_max_joueur = serie_joueur

    points_adv -= perte

    if points_adv < 0:
        points_adv = 0

    defaites_adv += 1
    serie_adv = 0

    gagnant = interaction.user.mention
    perdant = adversaire.mention

else:

    points_joueur -= perte

    if points_joueur < 0:
        points_joueur = 0

    defaites_joueur += 1
    serie_joueur = 0

    points_adv += gain
    victoires_adv += 1
    serie_adv += 1

    gagnant = adversaire.mention
    perdant = interaction.user.mention

grade_joueur = get_grade(points_joueur)
grade_adv = get_grade(points_adv)


cursor.execute("""
    UPDATE joueurs
    SET points=?,
    victoires=?,
    defaites=?,
    serie=?,
    streak_max=?,
    grade=?
    WHERE user_id=?
    """, (
    points_joueur,
    victoires_joueur,
    defaites_joueur,
    serie_joueur,
    streak_max_joueur,
    grade_joueur,
    user_id
))
                   
cursor.execute("""
    UPDATE joueurs
    SET points=?,
        victoires=?,
        defaites=?,
        serie=?,
        grade=?
    WHERE user_id=?
    """, (
        points_adv,
        victoires_adv,
        defaites_adv,
        serie_adv,
        grade_adv,
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

conn.commit()

    await interaction.response.send_message(
        f"""
⚔️ Duel enregistré

🏆 Gagnant : {gagnant}
📈 Gain : +{gain}

💀 Perdant : {perdant}
📉 Perte : -{perte}

🎮 Plateforme : {plateforme.name}
"""
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

