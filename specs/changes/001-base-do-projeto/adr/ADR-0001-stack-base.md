# ADR-0001 — Stack base

- Status: aceito
- Data: 2026-10-19
- Mudança de origem: 001-base-do-projeto

## Contexto
Decisões aprovadas pelo dono do produto para o MVP. O mesmo dono mantém o Sistema Vinculus e a Jalapão Store.

## Decisão
Backend Django 5.2 + DRF em Python 3.13 com uv; PostgreSQL 17; frontend Next.js + TypeScript (PWA) a partir da
mudança do front; deploy por Docker Compose na VPS com HTTPS pelo Traefik central.

## Alternativas consideradas
| Opção | Prós | Contras |
|---|---|---|
| FastAPI | leve | o Vinculus foi migrado de FastAPI para Django (spec 001 dele); voltar divergiria do padrão do dono |
| Node/Express | uma linguagem só | sem o Admin e o ORM prontos do Django; fora do padrão do dono |

## Consequências
Reaproveita pipeline, padrões e conhecimento do Vinculus. Dependência nova exige ADR.
