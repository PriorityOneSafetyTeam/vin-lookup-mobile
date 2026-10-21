// Minimal service worker required to satisfy Chrome mobile app installation rules
self.addEventListener('install', (e) => {
  self.skipWaiting();
});

self.addEventListener('fetch', (e) => {
  // Pass network requests through normally
  e.respondWith(fetch(e.request));
});
