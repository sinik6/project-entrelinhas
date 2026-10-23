# Constituição de desenvolvimento

## Para o sistema todo

1. **Especificar antes de implementar.** Toda mudança tem pasta em `docs/specs/NNN-nome/`:
   `spec.md` (comportamento, aceitação, não objetivos) → `plan.md` → `tasks.md` →
   `validation.md` (evidência). Mudança de escopo altera a spec primeiro; spec, testes e docs
   mudam no mesmo commit.
2. **Privacidade filtrada no servidor.** Texto de registro `private`, ou fora do trecho de um
   registro `partial`, nunca vai na resposta HTTP do Django. A filtragem é do backend; esconder
   no front não conta. Todo endpoint que devolve texto de registro tem teste de API provando que
   o texto escondido não aparece (nem em lista, nem em detalhe, nem em destaque ou comentário).
3. **Sem expansão automática de escopo.** Só o que está na spec e no roadmap é implementado.
   Uma tarefa pequena por vez, na ordem de `docs/roadmap.md`.
4. **Espaço de exatamente duas pessoas.** Um espaço nunca passa de 2 membros, garantido no
   backend. Recurso de outro espaço responde 404, nunca 403 (não revela que existe).
5. **Toda validação existe no backend.** O front pode repetir a regra para avisar antes de
   enviar, mas serializer/service responde 422, com teste de API que prova.
6. **Nenhum segredo no repositório.** Produção não sobe sem `DJANGO_SECRET_KEY`; `.env*` fora do Git.
7. **Commits** em Conventional Commits, autor exclusivo `jpjamal <jpfisica3@gmail.com>`, sem
   coautores nem atribuição de assistente.
8. **Código e docs em português** (domínio, docstrings, comentários); infraestrutura pode usar
   termos em inglês (`Service`, `QuerySet`, `ViewSet`, `hook`, `component`).
9. **Documentação no lugar certo:** regra de negócio em `docs/dominio/`; "como é feito" em
   `backend/docs/` (e `frontend/docs/` quando existir).

## Backend

10. **Regra de negócio mora no service.** Views só traduzem HTTP; services não importam DRF nem
    montam resposta; cálculo puro fica em `domain.py`. Sem repositórios artificiais.
11. **Um app por domínio** em `backend/apps/`; camadas: models · services · serializers · views · urls · tests.
12. **Escrita multi-passo é atômica.** `ATOMIC_REQUESTS` ligado; concorrência se resolve no banco
    (constraint ou `select_for_update`).

## Frontend (a partir da T0304)

13. **A tela nunca é a única barreira.** Esconder botão ou texto é conforto; a permissão real é do backend.
14. **Sessão só em cookie `HttpOnly`**, pelo BFF do Next; nada de `localStorage` para sessão ou texto de registro.
15. **Celular primeiro.** Toda tela funciona em 360px e como app instalado.

## Processo de especificação

16. **Critérios numerados e testados.** A aceitação da `spec.md` numera cada critério com o número
    da spec (`001-C1`, `001-C2`…). Cada critério tem ao menos um teste que cita o número no nome
    ou na docstring, e o `validation.md` lista critério → evidência.
17. **Sem decisão silenciosa.** O que o agente supõe vai para a seção "Suposições" da spec e é
    confirmado pelo usuário antes do plano.
18. **Mudança de risco analisa ameaças.** Spec que toca visibilidade, acesso, convites, upload ou
    migração que altera dados ganha a seção "Ameaças" no `plan.md`: o que pode dar errado →
    defesa → teste que prova (ver `docs/seguranca.md`).
19. **Revisão do usuário fecha a spec.** Spec com "Revisão do usuário" em aberto em `tasks.md`
    não está concluída. Nada é declarado testado ou publicado sem evidência no `validation.md`.

## Fronteiras do agente

| Sempre | Perguntar antes | Nunca |
|---|---|---|
| ler esta constituição, `docs/dominio/` e `backend/docs/architecture.md` | migração que altera ou apaga dados | commitar segredo, `.env` ou senha |
| teste de API provando que texto escondido não vaza | dependência nova (exige ADR) | coautor ou atribuição de IA no commit |
| rodar as checagens de `docs/tecnologia.md` antes de concluir | commit ou push na `main` (dispara deploy) | validar só na tela |
| atualizar a spec antes do código quando o rumo muda | mexer em infra, Traefik, deploy ou segredos do GitHub | enviar texto `private` ou fora do trecho `partial` na API |
| registrar suposições na spec | mudar a regra de visibilidade ou o limite de 2 membros | marcar tarefa como concluída sem evidência |
