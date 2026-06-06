import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
import os

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

@bot.event
async def on_ready():
    print(f"Connecté en tant que {bot.user}")

    try:
        synced = await bot.tree.sync()
        print(f"{len(synced)} commandes synchronisées")
    except Exception as e:
        print(e)

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS joueurs (
    user_id TEXT PRIMARY KEY,
    pseudo TEXT,
    points INTEGER DEFAULT 1000,
    victoires INTEGER DEFAULT 0,
    defaites INTEGER DEFAULT 0,
    serie INTEGER DEFAULT 0,
    grade TEXT DEFAULT 'Or'
)
""")

conn.commit()

@bot.tree.command(name="inscription")
async def inscription(interaction: discord.Interaction):

    user_id = str(interaction.user.id)
    pseudo = interaction.user.name

    cursor.execute(
        "SELECT * FROM joueurs WHERE user_id = ?",
        (user_id,)
    )

    joueur = cursor.fetchone()

    if joueur:
        await interaction.response.send_message(
            "Tu es déjà inscrit !",
            ephemeral=True
        )
        return

    cursor.execute(
        """
        INSERT INTO joueurs
        (user_id, pseudo)
        VALUES (?, ?)
        """,
        (user_id, pseudo)
    )

    conn.commit()

    await interaction.response.send_message(
        "⚔️ Bienvenue sur TeRom-Brawl !",
        ephemeral=True
    )
  
@bot.tree.command(name="profil")
async def profil(interaction: discord.Interaction):

    user_id = str(interaction.user.id)

    cursor.execute(
        "SELECT * FROM joueurs WHERE user_id = ?",
        (user_id,)
    )

    joueur = cursor.fetchone()

    if not joueur:
        await interaction.response.send_message(
            "Tu n'es pas inscrit.",
            ephemeral=True
        )
        return

    await interaction.response.send_message(
        f"""
🎖️ Grade : {joueur[6]}
📈 Points : {joueur[2]}

✅ Victoires : {joueur[3]}
❌ Défaites : {joueur[4]}

🔥 Série : {joueur[5]}
"""
    )

from database import init_db

init_db()

bot.run(TOKEN)
