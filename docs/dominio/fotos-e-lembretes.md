# Fotos manuscritas, PWA e lembretes

**Origem:** decisões aprovadas e fase 5 da especificação de origem. Tarefas T0501 e T0502.

## Regras
- **Fotos** de textos manuscritos são anexos do registro, em armazenamento **privado** (S3 compatível
  ou volume privado servido pelo Django). Só saem pela API, com login e conforme a visibilidade do
  registro: em `private`, o parceiro não recebe o anexo.
- **PWA:** o app é instalável; o service worker não guarda texto de registro nem foto.
- **Lembrete:** Web Push agendado para **21h30 no fuso configurado pelo usuário**.

## Pendências (a decidir nas specs da T0501/T0502)
- Onde ficam as fotos: bucket no SILO da VPS (padrão do Vinculus) ou volume. Tamanho e tipos aceitos.
- Em registro `partial`, se a foto é visível ao parceiro.
- Chaves VAPID e o processo que dispara o push (serviço próprio no compose, como o `vinculus-cron`).
- O que o lembrete diz, e se não é enviado quando a pessoa já entregou o registro do dia.
