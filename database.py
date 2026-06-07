import sqlite3

def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS joueurs (
        user_id TEXT PRIMARY KEY,
        pseudo TEXT NOT NULL,
        points INTEGER DEFAULT 1000,
        victoires INTEGER DEFAULT 0,
        defaites INTEGER DEFAULT 0,
        serie INTEGER DEFAULT 0,
        grade TEXT DEFAULT 'Or',
        teromik_coins INTEGER DEFAULT 0
    )
    """)

    conn.commit()
    conn.close()


CREATE TABLE IF NOT EXISTS matchs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    gagnant_id TEXT,
    perdant_id TEXT,
    date_match TEXT,
    points_gagnes INTEGER
)

