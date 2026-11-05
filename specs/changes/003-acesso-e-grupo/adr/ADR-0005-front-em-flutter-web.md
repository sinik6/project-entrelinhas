# ADR-0005 — Front em Flutter web como PWA

- Status: aceito (usuário, 2026-11-03)
- Data: 2026-11-03
- Mudança de origem: 003-acesso-e-grupo
- Substitui: a parte do front do ADR-0001 (Next.js + TypeScript)

## Contexto
A especificação de origem previa Next.js. Em 2026-11-03 o usuário pediu o front em Flutter, o mesmo que já usa no `analista-b3`
(Flutter web como PWA, sem app nativo, publicado na mesma VPS).

## Decisão
Front em `frontend/`, Flutter web com o SDK dentro de um contêiner (nada instalado no Windows), versão 3.47.8 baixada do servidor
do Google e conferida por SHA-256. Estrutura por feature (`app`, `features/acesso`, `features/perfil`, `features/grupo`,
`shared/api`, `shared/ui`). O build web é servido por nginx, sem CDN. Pacotes: `dio` (HTTP), `flutter_riverpod` (estado),
`go_router` (rotas, por fragmento), e em teste `flutter_lints` e `mocktail`. Sem geração de código (`freezed`, `build_runner`).

## Alternativas consideradas
| Opção | Prós | Contras |
|---|---|---|
| Next.js + TypeScript (original) | SSR, ecossistema web | o dono não usa mais nesta linha; a parte móvel (instalar no celular) pede PWA de qualquer jeito |
| Flutter com `freezed` e geradores (como no `analista-b3`) | menos código escrito à mão | build mais pesado, mais pacotes, mais superfície; o escopo atual é pequeno |
| Flutter nativo Android | acesso a recursos do aparelho | exige Android SDK; fora do que o dono quer agora |

## Consequências
- O ADR-0001 deixa de valer para o front; vale para o resto.
- O primeiro build é lento (SDK de cerca de 1 GB); depois fica em cache de camada.
- O CSP do app precisa de `wasm-unsafe-eval` (motor do Flutter), a única exceção.
- Pacote novo exige ADR (Art. 11); este lista os seis permitidos.
