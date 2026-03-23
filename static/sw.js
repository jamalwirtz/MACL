/* ═══════════════════════════════════════════════════════════════
   MUDDO AGRO — SERVICE WORKER v1
   Provides offline caching for the product catalogue and key pages
   ═══════════════════════════════════════════════════════════════ */

const CACHE_NAME  = 'muddo-agro-v1';
const STATIC_CACHE = 'muddo-static-v1';

// Core assets to pre-cache on install
const PRECACHE = [
  '/',
  '/pesticides',
  '/herbicides',
  '/fungicides',
  '/other-products',
  '/distributors',
  '/contact',
  '/static/css/style.css',
  '/static/css/animations.css',
  '/static/css/theme.css',
  '/static/css/typography.css',
  '/static/css/print.css',
  '/static/js/main.js',
  '/static/js/modal.js',
  '/static/js/theme.js',
  '/static/images/macl_logo.png',
  '/static/manifest.json',
];

// Install — pre-cache static assets
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then(cache => cache.addAll(PRECACHE))
      .then(() => self.skipWaiting())
  );
});

// Activate — clean up old caches
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys.filter(k => k !== CACHE_NAME && k !== STATIC_CACHE)
            .map(k  => caches.delete(k))
      )
    ).then(() => self.clients.claim())
  );
});

// Fetch — network first, fall back to cache
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET, admin, agent, API, uploads
  if (request.method !== 'GET') return;
  if (['/admin', '/agent', '/api/', '/uploads/'].some(p => url.pathname.startsWith(p))) return;

  event.respondWith(
    fetch(request)
      .then(response => {
        // Cache successful HTML / CSS / JS / image responses
        if (response.ok && ['text/html','text/css','application/javascript','image/'].some(
              t => (response.headers.get('content-type') || '').startsWith(t)
            )) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(request, clone));
        }
        return response;
      })
      .catch(() => {
        // Offline fallback: serve from cache
        return caches.match(request).then(cached => {
          if (cached) return cached;
          // Fallback for HTML pages
          if (request.headers.get('accept')?.includes('text/html')) {
            return caches.match('/');
          }
        });
      })
  );
});

// Background sync — queue failed form submissions
self.addEventListener('sync', event => {
  if (event.tag === 'contact-form') {
    // Re-attempt contact form submissions when back online
    event.waitUntil(
      self.clients.matchAll().then(clients =>
        clients.forEach(c => c.postMessage({ type: 'SYNC_CONTACT' }))
      )
    );
  }
});

// Push notifications (basic setup for future use)
self.addEventListener('push', event => {
  if (!event.data) return;
  const data = event.data.json();
  event.waitUntil(
    self.registration.showNotification(data.title || 'Muddo Agro', {
      body   : data.body || 'New update from Muddo Agro Chemicals',
      icon   : '/static/images/macl_logo.png',
      badge  : '/static/images/macl_logo.png',
      tag    : 'muddo-notification',
      data   : { url: data.url || '/' },
    })
  );
});

self.addEventListener('notificationclick', event => {
  event.notification.close();
  event.waitUntil(
    clients.openWindow(event.notification.data?.url || '/')
  );
});
