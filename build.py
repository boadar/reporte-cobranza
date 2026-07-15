# -*- coding: utf-8 -*-
"""Arma la app Reporte de Cobranza (PWA instalable) inyectando datos en template.html.
Genera: index.html, manifest.webmanifest, sw.js. Los iconos ya existen (icon-*.png).
Uso:  python build.py
"""
import os, re
D = os.path.dirname(os.path.abspath(__file__))
CACHE_NAME = 'reporte-cobranza-v1'  # subir el numero en cada despliegue para refrescar cache

def read(p):
    with open(os.path.join(D, p), encoding='utf-8') as f:
        return f.read()

def write(p, s):
    with open(os.path.join(D, p), 'w', encoding='utf-8') as f:
        f.write(s)

PWA_HEAD = (
    '<link rel="manifest" href="manifest.webmanifest">\n'
    '<link rel="apple-touch-icon" href="icon-180.png">\n'
    '<meta name="apple-mobile-web-app-capable" content="yes">\n'
    '<meta name="apple-mobile-web-app-status-bar-style" content="black">'
)
PWA_HOOK = (
    "<script>if('serviceWorker' in navigator){window.addEventListener('load',"
    "function(){navigator.serviceWorker.register('sw.js').catch(function(){});});}</script>"
)

tpl = read('template.html')
html = (tpl
        .replace('__CLIENTES__', read('clientes.json'))
        .replace('__TASAS__', read('tasas.json'))
        .replace('__PWA_HEAD__', PWA_HEAD)
        .replace('__PWA_HOOK__', PWA_HOOK))
# sincroniza APPVER con el numero de cache
ver = re.search(r'-v(\d+)$', CACHE_NAME).group(1)
html = re.sub(r'const APPVER\s*=\s*"[^"]*";', 'const APPVER = "v%s";' % ver, html)
write('index.html', html)

manifest = (
    '{"name":"Reporte de Cobranza","short_name":"Cobranza","start_url":"./","scope":"./",'
    '"display":"standalone","orientation":"portrait","background_color":"#282828","theme_color":"#282828",'
    '"icons":[{"src":"icon-192.png","sizes":"192x192","type":"image/png"},'
    '{"src":"icon-512.png","sizes":"512x512","type":"image/png"},'
    '{"src":"icon-512.png","sizes":"512x512","type":"image/png","purpose":"maskable"}]}'
)
write('manifest.webmanifest', manifest)

sw = (
    "const CACHE='%s';\n"
    "const ASSETS=['./','./index.html','./manifest.webmanifest','./icon-192.png','./icon-512.png','./icon-180.png'];\n"
    "self.addEventListener('install',e=>{e.waitUntil(caches.open(CACHE).then(c=>c.addAll(ASSETS)).then(()=>self.skipWaiting()));});\n"
    "self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim()));});\n"
    "self.addEventListener('fetch',e=>{const req=e.request;if(req.method!=='GET')return;\n"
    " e.respondWith(fetch(req).then(res=>{const cp=res.clone();caches.open(CACHE).then(c=>c.put(req,cp)).catch(()=>{});return res;}).catch(()=>caches.match(req).then(m=>m||caches.match('./index.html'))));});\n"
) % CACHE_NAME
write('sw.js', sw)

print('OK  index.html (%d KB) + manifest.webmanifest + sw.js  [%s]' % (len(html)//1024, CACHE_NAME))
