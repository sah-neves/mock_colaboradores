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
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS colaborador_projetos (
            colaborador_id INTEGER NOT NULL,
            project_id INTEGER NOT NULL,
            PRIMARY KEY (colaborador_id, project_id),
            FOREIGN KEY (colaborador_id) REFERENCES colaboradores(id) ON DELETE CASCADE
        )
    """)
    
    conn.commit()
    conn.close()

def get_all_colaboradores() -> List[Dict]:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT c.id, c.email, c.nome, c.cargo, c.level
        FROM colaboradores c
        ORDER BY c.id
    """)
    
    colaboradores = []
    for row in cursor.fetchall():
        colab_id = row["id"]
        
        # Buscar skills do colaborador
        cursor.execute("""
            SELECT s.nome, cs.nivel
            FROM colaborador_skills cs
            JOIN skills s ON cs.skill_id = s.id
            WHERE cs.colaborador_id = ?
        """, (colab_id,))
        
        skills = [
            {"nome": skill_row["nome"], "nivel": skill_row["nivel"]}
            for skill_row in cursor.fetchall()
        ]
        
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

def get_colaborador_by_email(email: str) -> Optional[Dict]:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT c.id, c.email, c.nome, c.cargo, c.level
        FROM colaboradores c
        WHERE LOWER(c.email) = LOWER(?)
    """, (email,))
    
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None
    
    colab_id = row["id"]
    
    # Buscar skills do colaborador
    cursor.execute("""
        SELECT s.nome, cs.nivel
        FROM colaborador_skills cs
        JOIN skills s ON cs.skill_id = s.id
        WHERE cs.colaborador_id = ?
    """, (colab_id,))
    
    skills = [
        {"nome": skill_row["nome"], "nivel": skill_row["nivel"]}
        for skill_row in cursor.fetchall()
    ]
    
    conn.close()
    
    return {
        "id": row["id"],
        "email": row["email"],
        "nome": row["nome"],
        "cargo": row["cargo"],
        "level": row["level"],
        "skills": skills
    }

def get_colaborador_by_id(colab_id: int) -> Optional[Dict]:
    """Busca um colaborador pelo ID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT c.id, c.email, c.nome, c.cargo, c.level
        FROM colaboradores c
        WHERE c.id = ?
    """, (colab_id,))
    
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None
    
    # Buscar skills do colaborador
    cursor.execute("""
        SELECT s.nome, cs.nivel
        FROM colaborador_skills cs
        JOIN skills s ON cs.skill_id = s.id
        WHERE cs.colaborador_id = ?
    """, (colab_id,))
    
    skills = [
        {"nome": skill_row["nome"], "nivel": skill_row["nivel"]}
        for skill_row in cursor.fetchall()
    ]
    
    conn.close()
    
    return {
        "id": row["id"],
        "email": row["email"],
        "nome": row["nome"],
        "cargo": row["cargo"],
        "level": row["level"],
        "skills": skills
    }

def get_colaboradores_by_ids(colab_ids: List[int]) -> List[Dict]:
    if not colab_ids:
        return []
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    placeholders = ",".join("?" * len(colab_ids))
    cursor.execute(f"""
        SELECT c.id, c.email, c.nome, c.cargo, c.level
        FROM colaboradores c
        WHERE c.id IN ({placeholders})
    """, colab_ids)
    
    colaboradores = []
    for row in cursor.fetchall():
        colab_id = row["id"]
        
        # Buscar skills do colaborador
        cursor.execute("""
            SELECT s.nome, cs.nivel
            FROM colaborador_skills cs
            JOIN skills s ON cs.skill_id = s.id
            WHERE cs.colaborador_id = ?
        """, (colab_id,))
        
        skills = [
            {"nome": skill_row["nome"], "nivel": skill_row["nivel"]}
            for skill_row in cursor.fetchall()
        ]
        
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
    """Cria um novo colaborador"""
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
            skill_nome = skill["nome"]
            skill_nivel = skill["nivel"]
            
            # Inserir skill se não existir
            cursor.execute("""
                INSERT OR IGNORE INTO skills (nome) VALUES (?)
            """, (skill_nome,))
            
            # Pegar o ID da skill
            cursor.execute("SELECT id FROM skills WHERE nome = ?", (skill_nome,))
            skill_id = cursor.fetchone()[0]
            
            # Criar relacionamento
            cursor.execute("""
                INSERT INTO colaborador_skills (colaborador_id, skill_id, nivel)
                VALUES (?, ?, ?)
            """, (colab_id, skill_id, skill_nivel))
        
        conn.commit()
        conn.close()
        
        return get_colaborador_by_id(colab_id)
    except sqlite3.IntegrityError as e:
        conn.rollback()
        conn.close()
        raise ValueError(f"Email já existe ou violação de constraint: {e}")

def update_colaborador(colab_id: int, email: Optional[str] = None, nome: Optional[str] = None,
                       cargo: Optional[str] = None, level: Optional[str] = None,
                       skills: Optional[List[Dict]] = None) -> Optional[Dict]:
    """Atualiza um colaborador"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verificar se existe
    cursor.execute("SELECT id FROM colaboradores WHERE id = ?", (colab_id,))
    if not cursor.fetchone():
        conn.close()
        return None
    
    # Atualizar campos básicos
    updates = []
    params = []
    
    if email is not None:
        updates.append("email = ?")
        params.append(email)
    if nome is not None:
        updates.append("nome = ?")
        params.append(nome)
    if cargo is not None:
        updates.append("cargo = ?")
        params.append(cargo)
    if level is not None:
        updates.append("level = ?")
        params.append(level)
    
    if updates:
        params.append(colab_id)
        cursor.execute(f"""
            UPDATE colaboradores
            SET {', '.join(updates)}
            WHERE id = ?
        """, params)
    
    # Atualizar skills se fornecido
    if skills is not None:
        # Remover skills antigas
        cursor.execute("DELETE FROM colaborador_skills WHERE colaborador_id = ?", (colab_id,))
        
        # Inserir novas skills
        for skill in skills:
            skill_nome = skill["nome"]
            skill_nivel = skill["nivel"]
            
            cursor.execute("""
                INSERT OR IGNORE INTO skills (nome) VALUES (?)
            """, (skill_nome,))
            
            cursor.execute("SELECT id FROM skills WHERE nome = ?", (skill_nome,))
            skill_id = cursor.fetchone()[0]
            
            cursor.execute("""
                INSERT INTO colaborador_skills (colaborador_id, skill_id, nivel)
                VALUES (?, ?, ?)
            """, (colab_id, skill_id, skill_nivel))
    
    conn.commit()
    conn.close()
    
    return get_colaborador_by_id(colab_id)

def delete_colaborador(colab_id: int) -> bool:
    """Deleta um colaborador"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM colaboradores WHERE id = ?", (colab_id,))
    if not cursor.fetchone():
        conn.close()
        return False
    
    cursor.execute("DELETE FROM colaboradores WHERE id = ?", (colab_id,))
    conn.commit()
    conn.close()
    return True

def inscrever_colaborador_em_projeto(colab_id: int, project_id: int) -> bool:
    """Inscreve um colaborador em um projeto"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT OR IGNORE INTO colaborador_projetos (colaborador_id, project_id)
            VALUES (?, ?)
        """, (colab_id, project_id))
        conn.commit()
        conn.close()
        return True
    except sqlite3.Error:
        conn.rollback()
        conn.close()
        return False

def desinscrever_colaborador_de_projeto(colab_id: int, project_id: int) -> bool:
    """Remove a inscrição de um colaborador de um projeto"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        DELETE FROM colaborador_projetos
        WHERE colaborador_id = ? AND project_id = ?
    """, (colab_id, project_id))
    
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

def get_colaboradores_inscritos_em_projeto(project_id: int) -> List[int]:
    """Retorna os IDs dos colaboradores inscritos em um projeto"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT colaborador_id
        FROM colaborador_projetos
        WHERE project_id = ?
    """, (project_id,))
    
    ids = [row["colaborador_id"] for row in cursor.fetchall()]
    conn.close()
    return ids

