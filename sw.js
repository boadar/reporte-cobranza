const CACHE='reporte-cobranza-v33';
const ASSETS=['./','./index.html','./manifest.webmanifest','./icon-192.png','./icon-512.png','./icon-180.png'];
self.addEventListener('install',e=>{e.waitUntil(caches.open(CACHE).then(c=>c.addAll(ASSETS)).then(()=>self.skipWaiting()));});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim()));});
self.addEventListener('fetch',e=>{const req=e.request;if(req.method!=='GET')return;
 e.respondWith(fetch(req).then(res=>{const cp=res.clone();caches.open(CACHE).then(c=>c.put(req,cp)).catch(()=>{});return res;}).catch(()=>caches.match(req).then(m=>m||caches.match('./index.html'))));});
