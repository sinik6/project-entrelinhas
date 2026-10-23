# ADR-001 — Stack base

**Status:** aceita (decisões aprovadas para o MVP, 2026-10-19).

## Decisão
- Backend: Django 5.2 + Django REST Framework, Python 3.13, uv.
- Banco: PostgreSQL 17.
- Frontend (T0304 em diante): Next.js + TypeScript, PWA, com BFF.
- Deploy: Docker Compose na VPS compartilhada, HTTPS pelo Traefik central.

## Por quê
Mesma stack do Sistema Vinculus e da Jalapão Store, mantidas pelo mesmo dono: reaproveita
padrões, pipeline de deploy e conhecimento.

## Consequências
Nenhuma dependência nova sem ADR. Padrões de código, CI e deploy seguem o Vinculus.
