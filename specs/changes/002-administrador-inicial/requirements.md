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

### US-2 — Não criar conta fraca ou sem senha
**Como** dono do produto, **quero** que o deploy recuse configuração insegura, **para** nunca haver um administrador com senha fraca.

- **REQ-2.1** SE a senha não estiver definida, ENTÃO O sistema DEVE recusar criar o usuário e encerrar o comando com erro.
- **REQ-2.2** SE a senha não atender à política de senhas do sistema, ENTÃO O sistema DEVE recusar criar o usuário e encerrar o comando com erro.
- **REQ-2.3** SE o nome de usuário ou o e-mail não estiverem definidos, ENTÃO O sistema DEVE recusar criar o usuário e encerrar o comando com erro.
- **REQ-2.4** SE o comando encerrar com erro durante o deploy, ENTÃO O sistema DEVE manter a API parada e interromper a publicação.

## Requisitos não funcionais
- **NFR-SEC-1** O sistema DEVE manter a senha fora do repositório, dos logs do deploy e do ambiente da API em execução.
- **NFR-SEC-2** O sistema DEVE gravar a senha apenas como hash.

## Dados pessoais (LGPD)
| Dado | Finalidade | Base legal | Retenção | Quem acessa |
|---|---|---|---|---|
| E-mail do administrador | identificar e contatar quem opera o sistema | execução do serviço (administração) | enquanto a conta existir | o próprio administrador |
| Hash da senha | autenticar | execução do serviço | enquanto a conta existir | ninguém lê; só o sistema compara |

## Casos de abuso
- **ABU-1** SE o comando for executado, ENTÃO O sistema DEVE não escrever a senha na saída nem nos logs.
- **ABU-2** SE já existir um usuário comum com o nome configurado, ENTÃO O sistema DEVE recusar sem promovê-lo a superusuário.
- **ABU-3** SE a senha configurada estiver vazia ou tiver só espaços, ENTÃO O sistema DEVE recusar criar o usuário.
- **ABU-4** SE o mesmo endereço de origem enviar mais de 5 tentativas de login ao Admin em um minuto, ENTÃO O sistema DEVE recusar as tentativas seguintes até a janela terminar.

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

## Checklist (G1)
- [x] Nenhum marcador de esclarecimento pendente
- [x] Todo critério em EARS, com ID e resultado observável
- [x] Erro, vazio, limite e permissões cobertos
- [x] Casos de abuso para fluxos sensíveis
- [x] Sem tecnologia citada; sem termos vagos
- [x] Sem conflito com a constituição
- [x] Suposições pendentes confirmadas pelo usuário
