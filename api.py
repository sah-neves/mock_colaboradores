from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import List
import requests
import uvicorn

from colaboradores_db import (
    init_database,
    get_all_colaboradores,
    get_colaborador_by_id,
    create_colaborador,
    delete_colaborador,
    add_colaborador_to_projeto,
    remove_colaborador_de_projeto,
    get_colaboradores_por_projeto,
)

# Inicializa banco de dados ao iniciar API
init_database()

app = FastAPI(title="API de Colaboradores com SQLite")

# URL da API de Projetos (Azure)
PROJETOS_API_URL = "https://bdprojetos.azurewebsites.net"

# ======== CORS ========
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ======== MODELS ========
class Skill(BaseModel):
    nome: str
    nivel: str

class ColaboradorBase(BaseModel):
    nome: str
    email: EmailStr
    cargo: str
    level: str
    skills: List[Skill]

class ColaboradorResponse(ColaboradorBase):
    id: int

class ProjectEnrollmentResponse(BaseModel):
    colaborador_id: int
    project_id: int


# ======== ROTAS ========

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

@app.get("/colaboradores", response_model=List[ColaboradorResponse])
def listar_colaboradores():
    """Listar todos os colaboradores"""
    return get_all_colaboradores()


@app.post("/colaboradores", response_model=ColaboradorResponse, status_code=status.HTTP_201_CREATED)
def criar_colaborador_endpoint(colaborador: ColaboradorBase):
    """Criar novo colaborador (local + Azure)"""
    try:
        # 1️⃣ Cria localmente
        novo = create_colaborador(
            colaborador.email,
            colaborador.nome,
            colaborador.cargo,
            colaborador.level,
            [s.dict() for s in colaborador.skills]
        )

        return novo

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/colaboradores/{colab_id}", response_model=ColaboradorResponse)
def buscar_colaborador(colab_id: int):
    """Buscar colaborador pelo ID"""
    colab = get_colaborador_by_id(colab_id)
    if not colab:
        raise HTTPException(status_code=404, detail="Colaborador não encontrado")
    return colab


@app.delete("/colaboradores/{colab_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_colaborador_endpoint(colab_id: int):
    """Deletar colaborador"""
    sucesso = delete_colaborador(colab_id)
    if not sucesso:
        raise HTTPException(status_code=404, detail="Colaborador não encontrado")
    return {"message": "Colaborador deletado com sucesso"}


@app.post(
    "/colaboradores/{colab_id}/projetos/{project_id}",
    response_model=ProjectEnrollmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def inscrever_colaborador_projeto(colab_id: int, project_id: int):
    """Inscrever colaborador em um projeto (local + API Azure)"""
    try:
        # 1️⃣ Adiciona vínculo localmente
        inscricao = add_colaborador_to_projeto(colab_id, project_id)
        
        # 2️⃣ Busca dados do colaborador
        colaborador = get_colaborador_by_id(colab_id)
        if not colaborador:
            raise HTTPException(status_code=404, detail="Colaborador não encontrado")

        # 3️⃣ Pega uma skill
        skill = colaborador["skills"][0] if colaborador["skills"] else {"nome": "geral", "nivel": "iniciante"}

        payload = {
            "collaborator_email": colaborador["email"],
            "contributed_skill_name": skill["nome"],
            "contributed_skill_level": skill["nivel"]
        }

        # 4️⃣ Envia para API de Projetos
        response = requests.post(
            f"{PROJETOS_API_URL}/projects/{project_id}/members",
            json=payload,
            timeout=10
        )

        if response.status_code not in (200, 201):
            raise HTTPException(status_code=500, detail=f"Falha ao notificar API de Projetos: {response.text}")

        return inscricao

    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Erro ao conectar à API de Projetos: {e}")


@app.delete(
    "/colaboradores/{colab_id}/projetos/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remover_colaborador_projeto(colab_id: int, project_id: int):
    """Remover colaborador de um projeto (local + API Azure)"""
    removed = remove_colaborador_de_projeto(colab_id, project_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Inscrição não encontrada")
    
    try:
        requests.delete(
            f"{PROJETOS_API_URL}/projects/{project_id}/members/{colab_id}",
            timeout=10
        )
    except requests.exceptions.RequestException:
        pass
    
    return {"message": "Inscrição removida com sucesso"}


@app.get(
    "/projetos/{project_id}/colaboradores",
    response_model=List[int],
)
def listar_colaboradores_projeto(project_id: int):
    """Listar IDs de colaboradores inscritos em um projeto"""
    return get_colaboradores_por_projeto(project_id)


@app.get("/projetos/{project_id}/colaboradores/detalhes")
def listar_colaboradores_detalhados(project_id: int):
    """Buscar detalhes dos colaboradores de um projeto"""
    try:
        colab_ids = get_colaboradores_por_projeto(project_id)
        detalhes = [get_colaborador_by_id(cid) for cid in colab_ids if get_colaborador_by_id(cid)]
        return detalhes
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ======== RUN ========
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
