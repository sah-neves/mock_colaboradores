import sqlite3
from typing import List, Dict, Optional

DB_PATH = "colaboradores.db"


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS colaboradores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            nome TEXT NOT NULL,
            cargo TEXT NOT NULL,
            level TEXT NOT NULL CHECK(level IN ('beginner', 'intermediate', 'advanced'))
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS colaborador_skills (
            colaborador_id INTEGER NOT NULL,
            skill_id INTEGER NOT NULL,
            nivel TEXT NOT NULL CHECK(nivel IN ('beginner', 'intermediate', 'advanced')),
            PRIMARY KEY (colaborador_id, skill_id),
            FOREIGN KEY (colaborador_id) REFERENCES colaboradores(id) ON DELETE CASCADE,
            FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE
        )
    """)

    conn.commit()
    conn.close()


def get_all_colaboradores() -> List[Dict]:
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM colaboradores ORDER BY id")
    colaboradores = []
    for row in cursor.fetchall():
        colab_id = row["id"]
        cursor.execute("""
            SELECT s.nome, cs.nivel
            FROM colaborador_skills cs
            JOIN skills s ON cs.skill_id = s.id
            WHERE cs.colaborador_id = ?
        """, (colab_id,))
        skills = [{"nome": s["nome"], "nivel": s["nivel"]} for s in cursor.fetchall()]
        colaboradores.append({
            "id": row["id"],
            "email": row["email"],
            "nome": row["nome"],
            "cargo": row["cargo"],
            "level": row["level"],
            "skills": skills
        })

    conn.close()
    return colaboradores


def create_colaborador(email: str, nome: str, cargo: str, level: str, skills: List[Dict]) -> Dict:
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO colaboradores (email, nome, cargo, level)
            VALUES (?, ?, ?, ?)
        """, (email, nome, cargo, level))
        colab_id = cursor.lastrowid

        for skill in skills:
            skill_nome = skill["nome"]
            skill_nivel = skill["nivel"]

            cursor.execute("INSERT OR IGNORE INTO skills (nome) VALUES (?)", (skill_nome,))
            cursor.execute("SELECT id FROM skills WHERE nome = ?", (skill_nome,))
            skill_id = cursor.fetchone()[0]

            cursor.execute("""
                INSERT INTO colaborador_skills (colaborador_id, skill_id, nivel)
                VALUES (?, ?, ?)
            """, (colab_id, skill_id, skill_nivel))

        conn.commit()
        return get_colaborador_by_id(colab_id)
    except sqlite3.IntegrityError as e:
        conn.rollback()
        raise ValueError(f"Erro ao criar colaborador: {e}")
    finally:
        conn.close()


def get_colaborador_by_id(colab_id: int) -> Optional[Dict]:
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM colaboradores WHERE id = ?", (colab_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None

    cursor.execute("""
        SELECT s.nome, cs.nivel
        FROM colaborador_skills cs
        JOIN skills s ON cs.skill_id = s.id
        WHERE cs.colaborador_id = ?
    """, (colab_id,))
    skills = [{"nome": s["nome"], "nivel": s["nivel"]} for s in cursor.fetchall()]
    conn.close()

    return {
        "id": row["id"],
        "email": row["email"],
        "nome": row["nome"],
        "cargo": row["cargo"],
        "level": row["level"],
        "skills": skills
    }


def delete_colaborador(colab_id: int) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM colaboradores WHERE id = ?", (colab_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted