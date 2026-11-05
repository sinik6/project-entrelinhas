# ADR-0007 — Fotos em volume privado, recodificadas com Pillow

- Status: aceito (usuário, 2026-11-05: "Sim, 004" ao pedir a implementação; proposto pelo agente por delegação)
- Data: 2026-11-05
- Mudança de origem: 004-fotos

## Contexto
A origem aceitava "armazenamento privado compatível com S3 ou volume privado via Django". O Vinculus usa o SILO (bucket) da VPS. Para duas pessoas,
o SILO exige rede `infra_storage`, bucket e credenciais por projeto.

## Decisão
1. As fotos ficam num volume Docker (`fotos_data`) montado na API e são servidas só por endpoint autenticado.
2. A API valida e **recodifica** toda imagem com Pillow antes de gravar (descarta metadados e conteúdo extra).
3. Pillow entra em `backend/pyproject.toml` com versão travada em `uv.lock`, verificada no PyPI antes de instalar (Art. 11).

## Consequências
- Sem serviço novo e sem credencial nova; backup do volume junto do banco no `deploy.sh`.
- Migrar para S3/SILO depois exige trocar o armazenamento por trás do mesmo serviço (um ponto só: `fotos/servicos.py`).
- Recodificar custa CPU por envio: aceitável para 2 pessoas.

## Alternativas descartadas
- **SILO/S3 agora:** mais infraestrutura e segredo sem ganho no MVP.
- **Guardar o arquivo como veio:** mantém EXIF/GPS e conteúdo extra; contradiz o Art. 9.
- **Só validar com `ImageField`:** abre a imagem mas não neutraliza trailers nem metadados.
