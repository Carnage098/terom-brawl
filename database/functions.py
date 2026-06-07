import sqlite3

def get_conn():
    return sqlite3.connect("database.db")

def get_joueur(user_id):
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM joueurs WHERE user_id = ?",
        (str(user_id),)
    )

    joueur = cursor.fetchone()

    conn.close()

    return joueur

def ajouter_joueur(user_id, pseudo):
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO joueurs (user_id, pseudo)
        VALUES (?, ?)
    """, (str(user_id), pseudo))

    conn.commit()
    conn.close()

def update_points(user_id, points):
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE joueurs
        SET points = ?
        WHERE user_id = ?
    """, (points, str(user_id)))

    conn.commit()
    conn.close()

