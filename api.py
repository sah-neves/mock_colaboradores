from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, EmailStr
from typing import List, Optional
import uvicorn

from colaboradores_db import (
    init_database,
    get_all_colaboradores,
    get_colaborador_by_id,
    create_colaborador,
    delete_colaborador,
)

# Inicializa banco de dados ao iniciar API
init_database()

app = FastAPI(title="API de Colaboradores com SQLite")

# models
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


# routes
@app.get("/colaboradores", response_model=List[ColaboradorResponse])
def listar_colaboradores():
    """Listar todos os colaboradores"""
    return get_all_colaboradores()


@app.post("/colaboradores", response_model=ColaboradorResponse, status_code=status.HTTP_201_CREATED)
def criar_colaborador_endpoint(colaborador: ColaboradorBase):
    """Criar novo colaborador"""
    try:
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


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)