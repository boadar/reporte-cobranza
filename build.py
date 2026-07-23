# -*- coding: utf-8 -*-
"""Arma la app Reporte de Cobranza (PWA instalable).
1) Regenera clientes.json y tasas.json desde data/*.csv (si existen).
2) Inyecta los datos en template.html -> index.html.
3) Genera manifest.webmanifest y sw.js. Los iconos ya existen (icon-*.png).
Uso:  python build.py
Para actualizar datos: editar data/clientes.csv o data/tasas_bcv.csv y correr build.py.
"""
import os, re, csv, json, sys, subprocess
D = os.path.dirname(os.path.abspath(__file__))
CACHE_NAME = 'reporte-cobranza-v54'  # subir el numero en cada despliegue para refrescar cache

def read(p):
    with open(os.path.join(D, p), encoding='utf-8') as f:
        return f.read()

def write(p, s):
    with open(os.path.join(D, p), 'w', encoding='utf-8') as f:
        f.write(s)

def gen_data():
    """Regenera clientes.json / tasas.json desde data/*.csv cuando existan."""
    cli_csv = os.path.join(D, 'data', 'clientes.csv')
    tas_csv = os.path.join(D, 'data', 'tasas_bcv.csv')
    if os.path.exists(cli_csv):
        cli = []
        with open(cli_csv, encoding='utf-8') as f:
            for r in csv.DictReader(f):
                cli.append([r['Codigo'], r['Nombre']])
        write('clientes.json', json.dumps(cli, ensure_ascii=False, separators=(',', ':')))
        print('  clientes.json regenerado:', len(cli))
    if os.path.exists(tas_csv):
        tas = {}
        with open(tas_csv, encoding='utf-8') as f:
            for r in csv.DictReader(f):
                usd = float(r['USD']) if r['USD'] else None
                eur = float(r['EUR']) if r['EUR'] else None
                tas[r['Fecha']] = [usd, eur]
        write('tasas.json', json.dumps(tas, ensure_ascii=False, separators=(',', ':')))
        print('  tasas.json regenerado:', len(tas))
    cxc_csv = os.path.join(D, 'data', 'cxc.csv')
    if os.path.exists(cxc_csv):
        fac = {}
        n = 0
        with open(cxc_csv, encoding='utf-8') as f:
            for r in csv.DictReader(f):
                cod = (r['Codigo'] or '').strip()
                if not cod:
                    continue
                def fnum(x):
                    try:
                        return float(x)
                    except Exception:
                        return 0.0
                fac.setdefault(cod, []).append({
                    'f': r['Factura'], 't': r['Tipo'], 'v': r['Vencimiento'],
                    'fd': r.get('FechaFactura', ''), 'tf': fnum(r.get('TasaFact', '')),
                    'b': fnum(r['Base']), 'i': fnum(r['IVA']),
                    'ib': fnum(r.get('IVABs', '')), 'i25': fnum(r.get('IVA25', '')),
                    'p': fnum(r['TotalPorPagar']), 'o': r['Observacion'],
                })
                n += 1
        write('facturas.json', json.dumps(fac, ensure_ascii=False, separators=(',', ':')))
        print('  facturas.json regenerado:', n, 'facturas /', len(fac), 'clientes')

gen_data()

# --solo-datos: actualiza clientes/tasas/facturas y los publica SIN tocar la app.
# La app los busca al arrancar, asi que no hace falta subir el numero de version.
if '--solo-datos' in sys.argv:
    if '--push' in sys.argv:
        msg = 'datos: clientes / tasas / facturas al dia'
        for cmd in (['git', 'add', 'clientes.json', 'tasas.json', 'facturas.json', 'data'],
                    ['git', 'commit', '-m', msg],
                    ['git', 'push']):
            if subprocess.run(cmd, cwd=D).returncode != 0:
                print('  fallo:', ' '.join(cmd))
                raise SystemExit(1)
        print('OK  datos publicados (la app no cambia de version)')
    else:
        print('OK  datos regenerados. Agrega --push para publicarlos.')
    raise SystemExit(0)

PWA_HEAD = (
    '<link rel="manifest" href="manifest.webmanifest">\n'
    '<link rel="apple-touch-icon" href="icon-180.png">\n'
    '<meta name="apple-mobile-web-app-capable" content="yes">\n'
    '<meta name="apple-mobile-web-app-status-bar-style" content="black">'
)
PWA_HOOK = (
    "<script>if('serviceWorker' in navigator){"
    "var __hadCtrl=!!navigator.serviceWorker.controller,__reloaded=false;"
    "navigator.serviceWorker.addEventListener('controllerchange',function(){"
    "if(__hadCtrl&&!__reloaded){__reloaded=true;window.location.reload();}});"
    "window.addEventListener('load',function(){"
    "navigator.serviceWorker.register('sw.js').then(function(reg){reg.update();"
    "setInterval(function(){reg.update();},1800000);}).catch(function(){});});}</script>"
)

tpl = read('template.html')
html = (tpl
        .replace('__CLIENTES__', read('clientes.json'))
        .replace('__TASAS__', read('tasas.json'))
        .replace('__FACTURAS__', read('facturas.json'))
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
    '{"src":"icon-512.png","sizes":"512x512","type":"image/png","purpose":"maskable"}],'
    '"share_target":{"action":"./share-target","method":"POST","enctype":"multipart/form-data",'
    '"params":{"title":"title","text":"text","url":"url","files":[{"name":"file","accept":["image/*","application/pdf"]}]}}}'
)
write('manifest.webmanifest', manifest)

sw = (
    "const CACHE='%s';\n"
    "const ASSETS=['./','./index.html','./manifest.webmanifest','./icon-192.png','./icon-512.png','./icon-180.png'];\n"
    "self.addEventListener('install',e=>{e.waitUntil(caches.open(CACHE).then(c=>c.addAll(ASSETS)).then(()=>self.skipWaiting()));});\n"
    "self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==CACHE&&k!=='shared-file').map(k=>caches.delete(k)))).then(()=>self.clients.claim()));});\n"
    "self.addEventListener('fetch',e=>{const req=e.request;const u=new URL(req.url);\n"
    " if(req.method==='POST'&&u.pathname.endsWith('/share-target')){e.respondWith((async function(){try{const f=await req.formData();let file=f.get('file');if(!file){const all=f.getAll('file');file=all&&all[0];}if(file){const c=await caches.open('shared-file');await c.put('shared',new Response(file,{headers:{'content-type':file.type||'application/octet-stream','x-filename':file.name||''}}));}}catch(err){}return Response.redirect('./?shared=1',303);})());return;}\n"
    " if(req.method!=='GET')return;\n"
    " e.respondWith(fetch(req).then(res=>{const cp=res.clone();caches.open(CACHE).then(c=>c.put(req,cp)).catch(()=>{});return res;}).catch(()=>caches.match(req).then(m=>m||caches.match('./index.html'))));});\n"
) % CACHE_NAME
write('sw.js', sw)

print('OK  index.html (%d KB) + manifest.webmanifest + sw.js  [%s]' % (len(html)//1024, CACHE_NAME))










