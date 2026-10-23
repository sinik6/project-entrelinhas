# ADR-002 — Visibilidade filtrada no servidor

**Status:** aceita (constituição da especificação de origem).

## Decisão
O texto de um registro `private`, ou a parte fora do trecho de um registro `partial`, nunca é
enviado na resposta HTTP do Django. O banco guarda o texto integral; o backend decide o que sai.
A filtragem acontece na camada de service/serializer de leitura, e nenhum endpoint monta resposta
de registro por fora dela.

## Por quê
Esconder no front deixaria o texto no tráfego e no cache do navegador: qualquer pessoa com as
ferramentas do navegador o leria. O produto existe para guardar o que se escreve; o vazamento
destrói a confiança.

## Consequências
- Um único ponto de leitura de registros (service) para listas, detalhes, destaques e comentários.
- Todo endpoint novo que devolve texto tem teste de API provando que o texto escondido não aparece.
- Cache e service worker não guardam texto de registro (ver `docs/seguranca.md`).
