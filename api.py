from typing import List

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field

from colaboradores_db import (
    delete_colaborador,
    desinscrever_colaborador_de_projeto,
    get_all_colaboradores,
    get_colaborador_by_id,
    get_colaboradores_inscritos_em_projeto,
    init_database,
    inscrever_colaborador_em_projeto,
)


class HabilidadePayload(BaseModel):
    nome: str = Field(..., min_length=1)
    nivel: str = Field(..., regex="^(beginner|intermediate|advanced)$")


class ColaboradorBase(BaseModel):
    email: EmailStr
    nome: str = Field(..., min_length=1)
    cargo: str = Field(..., min_length=1)
    level: str = Field(..., regex="^(beginner|intermediate|advanced)$")
    skills: List[HabilidadePayload] = Field(default_factory=list)


app = FastAPI(title="Colaboradores API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def ao_iniciar() -> None:
    init_database()


@app.get("/colaboradores", response_model=List[ColaboradorBase])
def listar_colaboradores():
    colaboradores = get_all_colaboradores()
    return colaboradores


@app.get("/colaboradores/{colab_id}", response_model=ColaboradorBase)
def obter_colaborador(colab_id: int):
    colaborador = get_colaborador_by_id(colab_id)
    if not colaborador:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Colaborador com id {colab_id} não encontrado.",
        )
    return colaborador


@app.delete("/colaboradores/{colab_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_colaborador(colab_id: int):
    deleted = delete_colaborador(colab_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Colaborador com id {colab_id} não encontrado.",
        )
    return None


@app.post("/colaboradores/{colab_id}/projetos/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def inscrever_em_projeto(colab_id: int, project_id: int):
    sucesso = inscrever_colaborador_em_projeto(colab_id, project_id)
    if not sucesso:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não foi possível inscrever o colaborador no projeto.",
        )
    return None


@app.delete(
    "/colaboradores/{colab_id}/projetos/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def desinscrever_de_projeto(colab_id: int, project_id: int):
    sucesso = desinscrever_colaborador_de_projeto(colab_id, project_id)
    if not sucesso:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Associação entre colaborador e projeto não encontrada.",
        )
    return None


@app.get("/projetos/{project_id}/colaboradores", response_model=List[int])
def listar_colaboradores_do_projeto(project_id: int):
    return get_colaboradores_inscritos_em_projeto(project_id)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8002)

