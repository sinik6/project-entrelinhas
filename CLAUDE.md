# Entrelinhas — orientação do projeto

Leia [`AGENTS.md`](AGENTS.md): é a porta de entrada deste projeto (steering, specs, comandos e fronteiras).

Regras que valem sempre, repetidas aqui porque o contexto precisa delas:

- Spec antes do código, em `specs/changes/NNN-slug/`; uma tarefa pequena por vez; sem expansão de escopo.
- Texto `private` ou fora do trecho `partial` nunca sai na resposta da API; todo endpoint que devolve texto
  de registro tem teste provando isso.
- Toda validação existe no backend (422 com teste de API).
- Commits: Conventional Commits, autor exclusivo `jpjamal <jpfisica3@gmail.com>`, sem coautores nem
  atribuição de IA. Só commitar ou dar push quando o dono mandar.
- Segredos fora do Git; chave privada de deploy nunca no chat nem no repositório.
- Ambiente local (Windows): ver `specs/steering/tech.md` (portas ocupadas, PostgreSQL descartável, uv).
