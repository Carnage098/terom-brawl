import os
import sqlite3
import discord
import random
from discord.ext import commands
from discord import app_commands

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

# ==========================
# BASE DE DONNÉES
# ==========================

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

# ==========================
# GRADES
# ==========================

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

# ==========================
# BOT READY
# ==========================

@bot.event
async def on_ready():

    print(f"✅ Connecté en tant que {bot.user}")

    try:
        synced = await bot.tree.sync()
        print(f"✅ {len(synced)} commandes synchronisées")
    except Exception as e:
        print(e)

# ==========================
# INSCRIPTION
# ==========================

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
            "❌ Tu es déjà inscrit.",
            ephemeral=True
        )
        return

    cursor.execute(
        """
        INSERT INTO joueurs(user_id, pseudo)
        VALUES (?, ?)
        """,
        (user_id, pseudo)
    )

    conn.commit()

    await interaction.response.send_message(
        """
⚔️ Bienvenue sur TeRom-Brawl !

🎖️ Grade : Recrue
📈 Points : 0
        """
    )

# ==========================
# PROFIL
# ==========================

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
            "❌ Tu n'es pas inscrit.",
            ephemeral=True
        )
        return

    points = joueur[2]
    grade = get_grade(points)

    await interaction.response.send_message(
        f"""
👤 **{joueur[1]}**

🎖️ Grade : {grade}
📈 Points : {points}

✅ Victoires : {joueur[3]}
❌ Défaites : {joueur[4]}

🔥 Série : {joueur[5]}

🪙 TeRomik Coins : {joueur[7]}
"""
    )

# ==========================
# LANCEMENT
# ==========================
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
            "❌ Tu dois d'abord utiliser /inscription",
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
        "❌ Cet adversaire n'est pas inscrit à TeRom-Brawl.",
        ephemeral=True
    )
    return

    points_actuels = joueur[2]
    victoires = joueur[3]
    defaites = joueur[4]
    serie = joueur[5]

    if resultat.value == "victoire":

        gain = random.randint(10, 100)

        points_actuels += gain
        victoires += 1
        serie += 1

        message = f"""
⚔️ Duel enregistré

🏆 Victoire contre {adversaire.mention}

🎮 Plateforme : {plateforme.name}

📈 Gain : +{gain}

📊 Total : {points_actuels}
"""

    else:

        perte = random.randint(1, 50)

        points_actuels -= perte

        if points_actuels < 0:
            points_actuels = 0

        defaites += 1
        serie = 0

        message = f"""
⚔️ Duel enregistré

💀 Défaite contre {adversaire.mention}

🎮 Plateforme : {plateforme.name}

📉 Perte : -{perte}

📊 Total : {points_actuels}
"""

    grade = get_grade(points_actuels)

    cursor.execute("""
    UPDATE joueurs
    SET points=?,
        victoires=?,
        defaites=?,
        serie=?,
        grade=?
    WHERE user_id=?
    """, (
        points_actuels,
        victoires,
        defaites,
        serie,
        grade,
        user_id
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
        points_actuels
    ))

    conn.commit()

    await interaction.response.send_message(message)


bot.run(TOKEN)
