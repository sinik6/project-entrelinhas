---
id: 001-base-do-projeto
titulo: Base do projeto (API, banco, CI e deploy na VPS)
status: em-revisao
tamanho: P2
risco: medio
capacidades: [base]
autor: jpjamal
criado: 2026-10-23
---

# Requisitos — Base do projeto

## Contexto e objetivo
O Entrelinhas precisa de uma fundação antes de qualquer funcionalidade: uma API que sobe com banco, testes
que rodam sempre da mesma forma e um caminho automático e seguro até a VPS compartilhada. O leitor
principal é o desenvolvedor (`jpjamal`); o outro dev, `sinik6`, é dono do repositório no GitHub.
Nesta mudança só o Django Admin fica público em `https://jpsys.duckdns.org/entrelinhas`; o front chega depois.
Cobre as tarefas T0101, T0102 e T0103 da especificação de origem.

## Suposições
| Suposição | Status |
|---|---|
| O repositório é `github.com/sinik6/project-entrelinhas`; `jpjamal` é colaborador | confirmada pelo usuário (2026-10-23) |
| O ambiente `production` do GitHub é criado por quem é admin do repositório | pendente de confirmação |
| A chave SSH de deploy é uma chave nova, dedicada ao projeto, instalada como linha própria no `authorized_keys` da VPS | pendente de confirmação |
| ASVS L2 como nível de segurança | pendente de confirmação |
| Commits direto na `main`, sem PR, e sem Git flow com `develop` | pendente de confirmação |
| Contrato da API escrito à mão nesta mudança, sem gerador de OpenAPI (evita dependência nova) | pendente de confirmação |

## Métricas de sucesso
- O ciclo "commit na `main` → publicado na VPS" termina sem passo manual e em menos de 15 minutos.
- 100% dos critérios desta spec têm teste ou evidência registrada na validação.

## Glossário
| Termo | Significado |
|---|---|
| Health check | verificação de saúde: resposta que confirma que a API e o banco estão de pé |
| CI | integração contínua: lint, checagens, testes e build a cada commit |
| VPS | servidor compartilhado com Jalapão Store e Vinculus |
| Traefik central | proxy do repositório `traefikproxy` que termina o HTTPS e roteia por rótulos |
| Ambiente `production` | área do GitHub com as variáveis e os segredos do deploy |

## Papéis e autorização
| Papel | Ação | Recurso | Permitido? | Condição |
|---|---|---|---|---|
| Qualquer cliente | consultar a verificação de saúde | health check | sim | sem autenticação, sem dado sensível |
| Qualquer cliente | acessar qualquer outra rota da API | API | não | exige autenticação (NFR-SEC-1) |
| Desenvolvedor | disparar publicação manual | workflow de deploy | sim | quem tem permissão de escrita no repositório e o ambiente `production` configurado |
| Admin do repositório | criar o ambiente e os segredos do GitHub | ambiente `production` | sim | só admin |

## Histórias e critérios de aceite

### US-1 — Saber se o sistema está de pé
**Como** desenvolvedor, **quero** uma verificação de saúde, **para** o deploy e o monitor saberem se a API e o banco respondem.

- **REQ-1.1** QUANDO um cliente consultar a verificação de saúde sem estar autenticado, O sistema DEVE responder com sucesso e com o estado "ok".
- **REQ-1.2** SE o banco de dados não aceitar consultas, ENTÃO O sistema DEVE responder à verificação de saúde com falha.

### US-2 — Configuração segura
**Como** dono do produto, **quero** que produção nunca suba com configuração de desenvolvimento, **para** não expor sessões.

- **REQ-2.1** SE a chave secreta de produção não estiver definida, ENTÃO O sistema DEVE recusar iniciar em modo de produção.

### US-3 — Publicar com segurança
**Como** desenvolvedor, **quero** que um commit aprovado chegue sozinho à VPS, **para** não depender de passos manuais.

- **REQ-3.1** QUANDO um commit chegar à ramificação principal, O sistema de integração DEVE executar lint, checagens, testes e a construção da imagem.
- **REQ-3.2** QUANDO a integração de um commit da ramificação principal for aprovada, O pipeline DEVE publicar esse mesmo commit na VPS.
- **REQ-3.3** QUANDO a publicação terminar, O sistema DEVE responder à tela de login do Admin por HTTPS, pelo domínio e pelo IP.
- **REQ-3.4** QUANDO a publicação terminar, O sistema DEVE redirecionar HTTP para HTTPS no endereço do Admin.
- **REQ-3.5** QUANDO uma publicação começar, O sistema DEVE gravar um backup do banco antes de aplicar migrações.
- **REQ-3.6** QUANDO um novo backup for gravado, O sistema DEVE manter apenas os 10 mais recentes.

### US-4 — Ambiente local
**Como** desenvolvedor, **quero** subir tudo com um comando, **para** trabalhar sem instalar o banco.

- **REQ-4.1** QUANDO o desenvolvedor subir o ambiente local, O sistema DEVE disponibilizar a API em `localhost:8010` com banco próprio e sem publicar a porta do banco.

## Requisitos não funcionais
- **NFR-SEC-1** O sistema DEVE exigir autenticação em toda rota da API, exceto nas declaradas públicas.
- **NFR-SEC-2** O sistema DEVE manter segredos fora do repositório e dos arquivos copiados para a VPS.

## Dados pessoais (LGPD)
Esta mudança não grava dado pessoal de usuário. O health check não devolve dado de ninguém.

## Casos de abuso
- **ABU-1** SE a integração de um commit falhar, ENTÃO O pipeline DEVE não publicá-lo.
- **ABU-2** SE um segredo obrigatório faltar no ambiente `production` do GitHub, ENTÃO O pipeline DEVE abortar antes de executar o script de publicação.
- **ABU-3** SE a rede do proxy não existir na VPS, ENTÃO O script de publicação DEVE abortar antes de parar a API.

## Fora de escopo
- Autenticação, espaços, convites, registros, destaques, fotos e lembretes (mudanças seguintes).
- Front-end e PWA.
- Backup do banco fora da própria VPS e monitoramento externo.
- Scanner de segredos e auditoria automática de dependências (pendências registradas em `security.md`).

## Esclarecimentos
| Data | Pergunta | Resposta |
|---|---|---|
| 2026-10-23 | Layout de documentação: leve (Vinculus) ou padrão da skill? | padrão da skill (usuário) |
| 2026-10-23 | Dono do repositório | `sinik6`; `jpjamal` é colaborador (usuário) |

## Checklist (G1)
- [x] Nenhum marcador de esclarecimento pendente
- [x] Todo critério em EARS, com ID e resultado observável
- [x] Erro, limite e permissões cobertos
- [x] Casos de abuso para fluxos sensíveis
- [x] Sem tecnologia citada; sem termos vagos
- [x] Sem conflito com a constituição
- [ ] Suposições pendentes confirmadas pelo usuário
