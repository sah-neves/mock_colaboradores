# Colaboradores API

API simples construída com FastAPI para consumir o banco de dados de colaboradores. A lógica de acesso aos dados está centralizada em `colaboradores_db.py`, permitindo trocar o backend real apenas ajustando caminhos ou credenciais.

# Acesse a documentação interativa em [http://localhost:8002/docs](http://localhost:8002/docs).

# Endpoints principais

- `GET /colaboradores` — Lista colaboradores com suas skills.
- `POST /colaboradores` — Simula criação de colaborador (mock).
- `GET /colaboradores/{id}` — Detalha um colaborador por ID.
- `DELETE /colaboradores/{id}` — Remove colaborador.
- `POST /colaboradores/{id}/projetos/{project_id}` — Inscreve em projeto.
- `DELETE /colaboradores/{id}/projetos/{project_id}` — Remove do projeto.
- `GET /projetos/{project_id}/colaboradores` — Lista IDs dos inscritos.

# Próximos passos sugeridos

- Substituir `colaboradores_db.py` pelas implementações reais mantendo a mesma interface.
- Adicionar autenticação básica caso seja necessário para ambientes externos.

# Exemplo de corpo para criação (`POST /colaboradores`)

```json
{
  "nome": "Maria Souza",
  "email": "maria.souza@example.com",
  "cargo": "Desenvolvedora Backend",
  "level": "advanced",
  "skills": [
    {
      "nome": "Python",
      "nivel": "advanced"
    },
    {
      "nome": "Django",
      "nivel": "intermediate"
    }
  ]
}
```

Para agilizar testes (por exemplo no Postman), você também pode reutilizar o arquivo `exemplos_post_colaboradores.json`, que contém várias requisições `POST /colaboradores` prontas para importar.

