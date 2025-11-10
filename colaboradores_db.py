import sqlite3
from typing import List, Dict, Optional

DB_PATH = "colaboradores.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_database():
    """Cria tabelas se não existirem"""
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

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS colaborador_projetos (
            colaborador_id INTEGER NOT NULL,
            projeto_id INTEGER NOT NULL,
            PRIMARY KEY (colaborador_id, projeto_id),
            FOREIGN KEY (colaborador_id) REFERENCES colaboradores(id) ON DELETE CASCADE
        )
    """)

    conn.commit()
    conn.close()


# funções para colaboradores
def get_all_colaboradores() -> List[Dict]:
    """Retorna todos os colaboradores com suas skills"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM colaboradores ORDER BY id")
    colaboradores = []

    for row in cursor.fetchall():
        colab_id = row["id"]
        skills = get_skills_do_colaborador(colab_id)
        colaboradores.append({
            "id": colab_id,
            "email": row["email"],
            "nome": row["nome"],
            "cargo": row["cargo"],
            "level": row["level"],
            "skills": skills
        })

    conn.close()
    return colaboradores


def create_colaborador(email: str, nome: str, cargo: str, level: str, skills: List[Dict]) -> Dict:
    """Cria um novo colaborador e associa suas skills"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO colaboradores (email, nome, cargo, level)
            VALUES (?, ?, ?, ?)
        """, (email, nome, cargo, level))
        colab_id = cursor.lastrowid

        # Inserir skills
        for skill in skills:
            skill_nome = skill["nome"].strip()
            skill_nivel = skill["nivel"].strip()

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
    """Busca colaborador pelo ID"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM colaboradores WHERE id = ?", (colab_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None

    skills = get_skills_do_colaborador(colab_id)
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
    """Remove colaborador do banco"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM colaboradores WHERE id = ?", (colab_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


# skills do colaborador
def get_skills_do_colaborador(colab_id: int) -> List[Dict]:
    """Busca skills de um colaborador"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.nome, cs.nivel
        FROM colaborador_skills cs
        JOIN skills s ON cs.skill_id = s.id
        WHERE cs.colaborador_id = ?
    """, (colab_id,))
    skills = [{"nome": s["nome"], "nivel": s["nivel"]} for s in cursor.fetchall()]
    conn.close()
    return skills


# funcoes para projetos
def add_colaborador_to_projeto(colab_id: int, projeto_id: int) -> Dict[str, int]:
    """Adiciona colaborador a um projeto"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Verifica se colaborador existe
        cursor.execute("SELECT 1 FROM colaboradores WHERE id = ?", (colab_id,))
        if cursor.fetchone() is None:
            raise LookupError("Colaborador não encontrado")

        # Insere vínculo com projeto
        cursor.execute("""
            INSERT INTO colaborador_projetos (colaborador_id, projeto_id)
            VALUES (?, ?)
        """, (colab_id, projeto_id))

        conn.commit()
        return {"colaborador_id": colab_id, "project_id": projeto_id}

    except sqlite3.IntegrityError as e:
        conn.rollback()
        if "UNIQUE constraint failed" in str(e):
            raise ValueError("Colaborador já inscrito neste projeto")
        raise
    finally:
        conn.close()


def remove_colaborador_de_projeto(colab_id: int, projeto_id: int) -> bool:
    """Remove colaborador de um projeto"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM colaborador_projetos
        WHERE colaborador_id = ? AND projeto_id = ?
    """, (colab_id, projeto_id))

    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


def get_colaboradores_por_projeto(projeto_id: int) -> List[int]:
    """Lista IDs de colaboradores vinculados a um projeto"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT colaborador_id
        FROM colaborador_projetos
        WHERE projeto_id = ?
        ORDER BY colaborador_id
    """, (projeto_id,))

    colaboradores = [row["colaborador_id"] for row in cursor.fetchall()]
    conn.close()
    return colaboradores