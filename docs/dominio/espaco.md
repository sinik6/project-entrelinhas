# Acesso, espaço e convites

**Origem:** fases 2 da especificação de origem. Tarefas T0201 e T0202.

## Regras
- O **espaço** (`spaces`) reúne exatamente **duas pessoas**. Nunca mais de 2 membros.
- Autenticação nativa do Django: sessão com cookie `HttpOnly` (ADR-004).
- Entrada no espaço por **convite**.
- Todo registro, destaque e comentário pertence a um espaço; quem não é membro não os vê.

## Pendências (a decidir na spec da T0201/T0202)
- Como o convite é criado e aceito (link, código, e-mail) e quando expira.
- O que acontece quando um dos dois sai do espaço.
- Fuso horário por usuário (necessário para o lembrete das 21h30, T0502).
