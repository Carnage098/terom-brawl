import os
import sqlite3
import discord

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

bot.run(TOKEN)
