# ADR-0002 — Visibilidade filtrada no servidor

- Status: aceito
- Data: 2026-10-19
- Mudança de origem: 001-base-do-projeto (decisão de fundação, vale para todo o produto)

## Contexto
O produto existe para guardar o que duas pessoas escrevem e controlar quanto o parceiro lê. A especificação de
origem exige que texto privado ou fora do trecho escolhido nunca seja enviado ao cliente.

## Decisão
O banco guarda o texto integral. O backend decide o que sai: registro `private` não devolve texto; registro
`partial` devolve só o intervalo escolhido; destaques e comentários só existem sobre o texto visível. Um único
ponto de leitura (service) aplica a regra, e nenhum endpoint monta resposta de registro por fora dele.

## Alternativas consideradas
| Opção | Prós | Contras |
|---|---|---|
| Esconder no front | simples | o texto continua no tráfego e nas ferramentas do navegador |
| Criptografar por registro com chave do autor | forte | complexidade e perda de recuperação; fora do escopo do MVP |

## Consequências
Todo endpoint que devolve texto tem teste de API provando que o texto escondido não aparece (Art. 12). Cache do
navegador e service worker não guardam texto de registro.
