# Produto — Entrelinhas

## Propósito
Aplicativo web instalável (PWA) para **duas pessoas** compartilharem escrita diária, fotos de textos
manuscritos, trechos selecionados e comentários contextuais. Cada pessoa decide, a cada entrega,
quanto do que escreveu o parceiro pode ler.

Texto original recebido do dono do produto: [`specs/origem/especificacao-origem.md`](../origem/especificacao-origem.md).

## Usuários e papéis
| Papel | Objetivo principal | Volume aproximado |
|---|---|---|
| Autor | escrever o registro do dia e escolher a visibilidade ao entregar | 1 pessoa por registro |
| Parceiro | ler o que lhe foi liberado, destacar trechos e comentar | 1 pessoa por espaço |

Cada espaço tem exatamente 2 pessoas; ambas são autor e parceiro, conforme o registro.

## Capacidades principais
| Capacidade | Spec viva | Estado |
|---|---|---|
| base (API, banco, CI, deploy) | — (sai ao arquivar a 001) | em construção |
| acesso-espaco | — | planejada |
| registros | — | planejada |
| destaques | — | planejada |
| fotos-lembretes | — | planejada |

O detalhe, as dependências e a ordem estão em [`specs/capability-map.md`](../capability-map.md).

## Decisões aprovadas para o MVP
Next.js + TypeScript (PWA responsivo); Django + DRF; PostgreSQL; Docker Compose em VPS com HTTPS;
fotos em armazenamento privado; lembrete por Web Push às 21h30 no fuso do usuário; exatamente dois
participantes; visibilidade `full`, `private` ou `partial`; destaques e comentários estilo Kindle.

## Objetivos de negócio e métricas
Uso pessoal de duas pessoas; sem meta comercial. Métrica de qualidade: nenhum caso em que texto
escondido apareça na resposta da API (Art. 12).

## Restrições
LGPD aplica-se (texto íntimo e fotos são dados pessoais, possivelmente sensíveis). Idioma: português
do Brasil. Plataformas: navegadores atuais no celular e no computador, e instalação como PWA.
Hospedagem: VPS compartilhada com Jalapão Store e Vinculus, atrás do Traefik central.

## Fora do produto
Mais de 2 pessoas por espaço; rede social, feed público ou compartilhamento com terceiros; qualquer
coisa que a especificação de origem não peça.
