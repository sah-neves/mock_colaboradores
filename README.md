# Colaboradores API

API simples construída com FastAPI para consumir o banco de dados de colaboradores. A lógica de acesso aos dados está centralizada em `colaboradores_db.py`, permitindo trocar o backend real apenas ajustando caminhos ou credenciais.

## Requisitos

- Python 3.10+ (testado com 3.11)
- Dependências de pacotes:
  ```bash
  pip install fastapi uvicorn pydantic
  ```

## Inicialização

1. Inicialize o banco (opcional; a API também chama isso ao subir):
   ```bash
   python colaboradores_db.py
   ```
   > Caso queira pré-popular dados, adapte esse script com inserções manuais.

2. Inicie o servidor FastAPI:
   ```bash
   uvicorn api:app --reload --port 8002
   ```

3. Acesse a documentação interativa em [http://localhost:8002/docs](http://localhost:8002/docs).

## Endpoints principais

- `GET /colaboradores` — Lista colaboradores com suas skills.
- `GET /colaboradores/{id}` — Detalha um colaborador por ID.
- `DELETE /colaboradores/{id}` — Remove colaborador.
- `POST /colaboradores/{id}/projetos/{project_id}` — Inscreve em projeto.
- `DELETE /colaboradores/{id}/projetos/{project_id}` — Remove do projeto.
- `GET /projetos/{project_id}/colaboradores` — Lista IDs dos inscritos.

## Próximos passos sugeridos

- Substituir `colaboradores_db.py` pelas implementações reais mantendo a mesma interface.
- Adicionar autenticação básica caso seja necessário para ambientes externos.

