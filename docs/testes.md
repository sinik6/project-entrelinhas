# Testes

- **Onde:** `backend/apps/<app>/tests/test_*.py` (por domínio) e `backend/tests/` (transversais).
- **Banco real:** PostgreSQL, nunca SQLite nem mock do ORM. Settings de teste em `config/settings/test.py`.
- **Teste de API:** cobre o contrato HTTP (status, corpo). Toda regra de validação tem teste que prova o 422.
- **Visibilidade:** todo endpoint que devolve texto de registro tem teste que cria um registro
  `private` e outro `partial`, lê como parceiro e confere que o texto escondido não aparece em
  nenhum ponto da resposta (constituição, regra 2).
- **Acesso cruzado:** todo recurso novo ganha teste de que outro espaço recebe 404.
- **Rastreabilidade:** cada critério `NNN-Cn` da spec aparece no nome ou na docstring de ao menos um
  teste, e no `validation.md`.
- **CI:** o mesmo conjunto roda no GitHub Actions (`.github/workflows/ci.yml`) antes de qualquer deploy.
- **Frontend e e2e:** definidos junto da T0304.
