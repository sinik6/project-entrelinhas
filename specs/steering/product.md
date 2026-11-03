# Produto — Entrelinhas

## Propósito
Aplicativo web instalável (PWA) para **duas pessoas** compartilharem escrita diária, fotos de textos
manuscritos, trechos selecionados e comentários contextuais. Cada pessoa decide, a cada entrega,
quanto do que escreveu o parceiro pode ler.

Textos originais do dono do produto: [`especificacao-origem.md`](../origem/especificacao-origem.md) (2026-10-19) e [`visao-complementar-2026-11-03.md`](../origem/visao-complementar-2026-11-03.md).

## Usuários e papéis
| Papel | Objetivo principal | Volume aproximado |
|---|---|---|
| Autor | escrever o registro do dia e escolher a visibilidade ao entregar | 1 pessoa por registro |
| Parceiro | ler o que lhe foi liberado, destacar trechos e comentar | 1 pessoa por grupo |

Cada grupo de escrita tem no máximo 2 pessoas no MVP; ambas são autor e parceiro, conforme o registro. Cada pessoa
tem uma cor de perfil (obrigatória), mostrada nos comentários e no calendário.

## Capacidades principais
| Capacidade | Spec viva | Estado |
|---|---|---|
| base (API, banco, CI, deploy, administrador inicial) | — (sai ao arquivar a 001 e a 002) | no ar |
| acesso-espaco (contas, perfil, cor, grupo de escrita) | — | planejada |
| fotos | — | planejada |
| registros | — | planejada |
| destaques | — | planejada |
| calendario | — | planejada |
| lembretes (PWA e push) | — | planejada |
| grupos de estudo e leitura | — | futura, fora do MVP |

O detalhe, as dependências e a ordem estão em [`specs/capability-map.md`](../capability-map.md).

## Decisões aprovadas para o MVP
Next.js + TypeScript (PWA responsivo); Django + DRF; PostgreSQL; Docker Compose em VPS com HTTPS;
fotos em armazenamento privado; lembrete por Web Push às 21h30 no fuso do usuário; grupo de escrita de até dois
participantes no MVP; registro só vale com foto do manuscrito e texto digitado; visibilidade `full`, `private` ou `partial`; destaques e comentários estilo Kindle.

## Objetivos de negócio e métricas
Uso pessoal de duas pessoas; sem meta comercial. Métrica de qualidade: nenhum caso em que texto
escondido apareça na resposta da API (Art. 12).

## Restrições
LGPD aplica-se (texto íntimo e fotos são dados pessoais, possivelmente sensíveis). Idioma: português
do Brasil. Plataformas: navegadores atuais no celular e no computador, e instalação como PWA.
Hospedagem: VPS compartilhada com Jalapão Store e Vinculus, atrás do Traefik central.

## Fora do produto
Mais de 2 pessoas no grupo de escrita durante o MVP; grupos de estudo e de leitura (depois do MVP); rede social,
feed público ou compartilhamento com terceiros; qualquer coisa que as especificações de origem não peçam.
