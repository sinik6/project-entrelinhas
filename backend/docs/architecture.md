# Arquitetura do backend

Django 5.2 + DRF, Python 3.13, PostgreSQL 17. Decisões em [`docs/adr/`](../../docs/adr/); regras de
negócio em [`docs/dominio/`](../../docs/dominio/README.md).

## Pastas
```
backend/
├── config/
│   ├── settings/   base · dev · test · prod (cada um importa base e ajusta só o que muda)
│   ├── urls.py     Admin (com prefixo da VPS) + /api/v1/
│   └── api_v1.py   cada app de domínio registra suas rotas aqui
├── apps/
│   └── common/     health check e utilidades compartilhadas
└── tests/          testes transversais (configuração)
```

## Camadas de um app de domínio
`models` · `services` (regra de negócio, não importa DRF) · `serializers` · `views` (só traduz HTTP) ·
`urls` · `tests`. Cálculo puro em `domain.py`. Sem repositórios artificiais.

## Configuração
- Valores sensíveis e dependentes do ambiente vêm de variáveis (`env()` em `settings/base.py`);
  sem padrão, a ausência é erro.
- `DJANGO_PREFIXO_URL=entrelinhas` põe o Admin em `/entrelinhas/admin/` e os estáticos em
  `/entrelinhas/django-static/`. Vazio em desenvolvimento.
- `ATOMIC_REQUESTS` ligado: cada request é uma transação.

## Visibilidade (T0302/T0303)
Um único service lê registros e aplica `full` / `private` / `partial` (ADR-002). Nenhuma view ou
serializer devolve `body` por fora dele.
