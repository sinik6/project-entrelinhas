// Service worker do Entrelinhas (spec 010). Faz UMA coisa: mostrar o aviso diário e abrir o app ao toque nele.
// Não usa `fetch`, nem `caches`, nem `indexedDB`: nada do diário é guardado no aparelho (NFR-LEMB-2, Art. 12).

self.addEventListener('install', (evento) => {
  evento.waitUntil(self.skipWaiting());
});

self.addEventListener('activate', (evento) => {
  evento.waitUntil(self.clients.claim());
});

// A carga é genérica de propósito (a notificação aparece com o celular bloqueado): título, corpo e a rota a abrir.
self.addEventListener('push', (evento) => {
  let carga = {};
  try {
    carga = evento.data ? evento.data.json() : {};
  } catch (_) {
    carga = {};
  }
  const titulo = typeof carga.titulo === 'string' ? carga.titulo : 'Entrelinhas';
  const corpo = typeof carga.corpo === 'string' ? carga.corpo : 'Hora de escrever o seu dia.';
  const url = typeof carga.url === 'string' && carga.url.startsWith('#/') ? carga.url : '#/hoje';
  evento.waitUntil(
    self.registration.showNotification(titulo, {
      body: corpo,
      icon: 'icons/Icon-192.png',
      badge: 'icons/Icon-192.png',
      tag: 'lembrete-diario',
      data: { url },
    }),
  );
});

// Toque na notificação: foca o app se já está aberto (e leva à tela Hoje); senão abre.
self.addEventListener('notificationclick', (evento) => {
  evento.notification.close();
  const rota = (evento.notification.data && evento.notification.data.url) || '#/hoje';
  const escopo = self.registration.scope;
  evento.waitUntil(
    self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then((janelas) => {
      for (const janela of janelas) {
        if (janela.url.startsWith(escopo) && 'focus' in janela) {
          return janela.focus().then((foco) => {
            if (foco && 'navigate' in foco) return foco.navigate(escopo + rota);
            return foco;
          });
        }
      }
      return self.clients.openWindow(escopo + rota);
    }),
  );
});
