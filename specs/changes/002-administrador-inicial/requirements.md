---
id: 002-administrador-inicial
titulo: Administrador inicial criado pelo deploy
status: em-revisao
tamanho: P2
risco: alto
capacidades: [base]
autor: jpjamal
criado: 2026-10-28
---

# Requisitos — Administrador inicial criado pelo deploy

## Contexto e objetivo
O sistema está publicado em `https://jpsys.duckdns.org/entrelinhas`, mas o banco da VPS não tem nenhum usuário:
a tela de login do Admin abre e ninguém entra. O dono precisa de uma conta de administrador para operar o
Admin, criada pelo próprio deploy, sem digitar senha em terminal e sem senha no repositório.
Esta mudança toca autenticação e privilégio máximo, então tem risco alto e modelo de ameaças.
As contas das duas pessoas do diário **não** entram aqui: nascem na mudança de acesso e espaço.

## Suposições
| Suposição | Status |
|---|---|
| Um único superusuário, do dono do produto | confirmada (usuário, 2026-10-28) |
| Senha vem de um segredo do ambiente `production` do GitHub | confirmada (usuário, 2026-10-28) |
| O projeto continua com o modelo de usuário padrão do sistema; a mudança de acesso e espaço guarda fuso e preferências em perfil separado | confirmada (usuário, 2026-10-28) |
| Nome de usuário e e-mail do administrador vêm de variáveis do ambiente `production` (não ficam no repositório) | confirmada (usuário, 2026-10-28) |
| A senha só é lida na hora de criar a conta; contas já existentes nunca têm a senha trocada por este comando | confirmada (usuário, 2026-10-28) |
| A política de senhas do sistema vale para esta conta, sem exceção de teste; comprimento mínimo de 12 caracteres | confirmada (usuário, 2026-10-28) |
| Em 2026-11-03 o usuário escreveu no chat que o agente deveria decidir por conta própria o que ficasse em aberto, sem outro dev, e usar um agente específico para a verificação, sem precisar dele. Com base nisso o agente decidiu ABU-4, REQ-2.5, REQ-1.4, e-mail no log e senha sempre exigida | delegação dada pelo usuário em chat; **decisões ratificadas pelo usuário em 2026-11-03** (tasks.md, T-6.8) |

## Métricas de sucesso
- Depois do primeiro deploy com os valores configurados, o dono entra no Admin sem nenhum passo manual na VPS.
- Repetir o deploy 10 vezes não altera a conta nem a senha.

## Glossário
| Termo | Significado |
|---|---|
| Administrador inicial | superusuário criado pelo deploy, com acesso total ao Admin |
| Superusuário | usuário com todas as permissões do sistema |
| Política de senhas | regras de validação de senha do sistema (tamanho mínimo, senha comum, só números) |
| Ambiente `production` | área do GitHub com as variáveis e os segredos do deploy |

## Papéis e autorização
| Papel | Ação | Recurso | Permitido? | Condição |
|---|---|---|---|---|
| Administrador inicial | entrar no Admin e gerir dados | Admin | sim | com o nome e a senha configurados |
| Anônimo | criar conta ou pedir privilégio | Admin | não | não existe cadastro público |
| Quem tem permissão de escrita no repositório | disparar o deploy | workflow de deploy | sim | ambiente `production` configurado |
| Admin do repositório | criar ou trocar o segredo da senha | ambiente `production` | sim | só admin |

## Histórias e critérios de aceite

### US-1 — Entrar no Admin depois do deploy
**Como** dono do produto, **quero** que o deploy crie meu administrador, **para** operar o Admin sem acessar a VPS por terminal.

- **REQ-1.1** QUANDO o deploy terminar e não existir usuário com o nome configurado, O sistema DEVE criar um superusuário com esse nome, o e-mail e a senha configurados.
- **REQ-1.2** QUANDO o usuário com o nome configurado já existir e for superusuário, O sistema DEVE manter a senha, o e-mail e as permissões dele sem alteração.
- **REQ-1.3** QUANDO a conta criada fizer login no Admin com a senha configurada, O sistema DEVE conceder acesso ao Admin.
- **REQ-1.4** QUANDO o superusuário existente com o nome configurado estiver inativo, O sistema DEVE avisar na saída de erro, sem alterar a conta.

### US-2 — Não criar conta fraca ou sem senha
**Como** dono do produto, **quero** que o deploy recuse configuração insegura, **para** nunca haver um administrador com senha fraca.

- **REQ-2.1** SE a senha não estiver definida, ENTÃO O sistema DEVE recusar e encerrar o comando com erro, sem criar nem alterar usuário.
- **REQ-2.2** SE a senha não atender à política de senhas do sistema, ENTÃO O sistema DEVE recusar e encerrar o comando com erro, sem criar nem alterar usuário.
- **REQ-2.3** SE o nome de usuário ou o e-mail não estiverem definidos ou forem inválidos, ENTÃO O sistema DEVE recusar e encerrar o comando com erro, sem criar nem alterar usuário.
- **REQ-2.4** SE a criação do administrador encerrar com erro depois de a API ser parada, ENTÃO O sistema DEVE manter a API parada e interromper a publicação.
- **REQ-2.5** QUANDO um deploy começar, O sistema DEVE conferir nome, e-mail e senha do administrador antes de parar a API e, se a conferência recusar, abortar o deploy com a API no ar.

## Requisitos não funcionais
- **NFR-SEC-1** O sistema DEVE manter a senha fora do repositório, dos logs do deploy e do ambiente da API em execução.
- **NFR-SEC-2** O sistema DEVE gravar a senha apenas como hash.

## Dados pessoais (LGPD)
| Dado | Finalidade | Base legal | Retenção | Quem acessa |
|---|---|---|---|---|
| E-mail do administrador | identificar e contatar quem opera o sistema | execução do serviço (administração) | enquanto a conta existir | o próprio administrador e quem lê o log do Actions (a variable aparece no cabeçalho do passo) |
| Hash da senha | autenticar | execução do serviço | enquanto a conta existir | ninguém lê; só o sistema compara |

## Casos de abuso
- **ABU-1** SE o comando for executado, ENTÃO O sistema DEVE não escrever a senha na saída nem nos logs.
- **ABU-2** SE já existir um usuário comum com o nome configurado (sem diferenciar maiúsculas de minúsculas nem a forma Unicode), ENTÃO O sistema DEVE recusar sem promovê-lo a superusuário.
- **ABU-3** SE a senha configurada estiver vazia ou tiver só espaços, ENTÃO O sistema DEVE recusar criar o usuário.
- **ABU-4** SE o mesmo endereço de origem enviar mais de 5 tentativas de login seguidas ao Admin por um mesmo endereço de acesso (domínio ou IP), ENTÃO O sistema DEVE recusar as seguintes, liberando no máximo uma a cada 12 segundos.

## Fora de escopo
- Contas das duas pessoas do diário, login do app e convites (mudança de acesso e espaço).
- Recuperação de senha, troca obrigatória no primeiro acesso, verificação em duas etapas e rotação automática.
- Mais de um administrador e criação de outros superusuários.
- Alterar a senha de uma conta existente por este comando.

## Esclarecimentos
| Data | Pergunta | Resposta |
|---|---|---|
| 2026-10-28 | Quais contas o deploy cria? | só o superusuário do dono |
| 2026-10-28 | De onde vem a senha? | segredo do ambiente `production` no GitHub |
| 2026-10-28 | Modelo de usuário? | padrão do sistema, com perfil separado na mudança de acesso e espaço |
| 2026-10-28 | Comprimento mínimo da senha (G2) | 12 caracteres |
| 2026-10-28 | Força bruta no Admin (G2) | limite de 5 tentativas por minuto por endereço, no Traefik (ABU-4) |
| 2026-10-28 | ABU-3 citava uma senha padrão que o projeto não tem (G2) | reescrito como senha vazia ou só espaços |
| 2026-11-03 | ABU-4: o limite recusa "até a janela terminar" ou é balde de fichas? (auditoria M2) | medido no ar: balde de 5 fichas com recarga de 1 a cada ~12 s, e o domínio e o IP têm baldes separados; o ABU-4 foi reescrito para isso (agente, por delegação) |
| 2026-11-03 | Uma recusa de senha deve derrubar o Admin? (auditoria M3) | não: nasce o REQ-2.5, a conferência antes de parar a API; o REQ-2.4 fica só para o que só aparece depois (agente, por delegação) |
| 2026-11-03 | O e-mail do administrador aparece no log do Actions (auditoria M4) | aceito: é variable, visível a quem lê o repositório; a senha não é variable (agente, por delegação) |

## Checklist (G1)
- [x] Nenhum marcador de esclarecimento pendente
- [x] Todo critério em EARS, com ID e resultado observável
- [x] Erro, vazio, limite e permissões cobertos
- [x] Casos de abuso para fluxos sensíveis
- [x] Sem tecnologia citada; sem termos vagos
- [x] Sem conflito com a constituição
- [x] Suposições pendentes confirmadas pelo usuário
