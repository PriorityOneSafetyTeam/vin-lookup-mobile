const CACHE_NAME = 'vin-lookup-v1';
const ASSETS = [
  '/',
  '/manifest.json'
];

// Perform installation and force asset caching to satisfy Chrome rules
self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(ASSETS);
    }).then(() => {
      return self.skipWaiting();
    })
  );
});

// Force the service worker to activate immediately on the phone
self.addEventListener('activate', (e) => {
  e.waitUntil(self.clients.claim());
});

// Intercept fetch requests smoothly to fulfill PWA structural rules
self.addEventListener('fetch', (e) => {
  e.respondWith(
    fetch(e.request).catch(() => {
      return caches.match(e.request);
    })
  );
});
