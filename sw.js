const CACHE='reporte-cobranza-v44';
const ASSETS=['./','./index.html','./manifest.webmanifest','./icon-192.png','./icon-512.png','./icon-180.png'];
self.addEventListener('install',e=>{e.waitUntil(caches.open(CACHE).then(c=>c.addAll(ASSETS)).then(()=>self.skipWaiting()));});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==CACHE&&k!=='shared-file').map(k=>caches.delete(k)))).then(()=>self.clients.claim()));});
self.addEventListener('fetch',e=>{const req=e.request;const u=new URL(req.url);
 if(req.method==='POST'&&u.pathname.endsWith('/share-target')){e.respondWith((async function(){try{const f=await req.formData();let file=f.get('file');if(!file){const all=f.getAll('file');file=all&&all[0];}if(file){const c=await caches.open('shared-file');await c.put('shared',new Response(file,{headers:{'content-type':file.type||'application/octet-stream','x-filename':file.name||''}}));}}catch(err){}return Response.redirect('./?shared=1',303);})());return;}
 if(req.method!=='GET')return;
 e.respondWith(fetch(req).then(res=>{const cp=res.clone();caches.open(CACHE).then(c=>c.put(req,cp)).catch(()=>{});return res;}).catch(()=>caches.match(req).then(m=>m||caches.match('./index.html'))));});
