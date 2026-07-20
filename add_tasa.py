# -*- coding: utf-8 -*-
"""Agrega la tasa de un dia y la publica SIN generar una version nueva de la app.

La app trae las tasas incrustadas como respaldo, pero al abrir busca tasas.json
en el servidor y mezcla lo nuevo. Por eso aqui solo hay que tocar el CSV, volver
a generar tasas.json y subir esos dos archivos.

Uso:
    python add_tasa.py 2026-07-20 736.9339 843.1998
    python add_tasa.py 2026-07-20 736.9339 843.1998 --push
    python add_tasa.py 2026-07-20 736.9339 843.1998 --fin-de-semana   # llena tambien sab y dom previos

Para cambiar la app (pantallas, calculos, plantillas de banco) sigue haciendo
falta build.py con el numero de version subido.
"""
import csv, os, sys, json, shutil, datetime, subprocess

APP = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(os.path.dirname(APP), 'data', 'tasas_bcv.csv')   # maestra, fuera del repo
REPO = os.path.join(APP, 'data', 'tasas_bcv.csv')                    # copia del repo
DIAS = ['Lunes', 'Martes', 'Miercoles', 'Jueves', 'Viernes', 'Sabado', 'Domingo']


def load(path):
    rows = {}
    if os.path.exists(path):
        with open(path, newline='', encoding='utf-8') as f:
            for r in csv.DictReader(f):
                rows[r['Fecha']] = r
    return rows


def save(path, rows):
    with open(path, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['Fecha', 'Dia', 'USD', 'EUR'])
        for k in sorted(rows):
            r = rows[k]
            w.writerow([k, r['Dia'], r['USD'], r['EUR']])


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    push = '--push' in sys.argv
    finde = '--fin-de-semana' in sys.argv
    if len(args) < 2:
        print(__doc__)
        return 1
    fecha, usd = args[0], float(args[1])
    eur = float(args[2]) if len(args) > 2 else None

    rows = load(BASE)
    dias = [datetime.date.fromisoformat(fecha)]
    if finde:                       # el sabado y el domingo previos llevan la misma tasa
        d = dias[0]
        for k in (1, 2):
            prev = d - datetime.timedelta(days=k)
            if prev.weekday() >= 5:
                dias.append(prev)
    for d in dias:
        k = d.isoformat()
        rows[k] = {'Dia': DIAS[d.weekday()],
                   'USD': repr(round(usd, 4)),
                   'EUR': '' if eur is None else repr(round(eur, 4))}
        print('  guardado %s %s  USD=%s  EUR=%s' % (k, DIAS[d.weekday()], rows[k]['USD'], rows[k]['EUR'] or '-'))
    save(BASE, rows)
    shutil.copyfile(BASE, REPO)

    tas = {}
    with open(REPO, newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            tas[r['Fecha']] = [float(r['USD']) if r['USD'] else None,
                               float(r['EUR']) if r['EUR'] else None]
    with open(os.path.join(APP, 'tasas.json'), 'w', encoding='utf-8') as f:
        json.dump(tas, f, ensure_ascii=False, separators=(',', ':'))
    print('OK  tasas.json regenerado: %d dias (sin cambiar la version de la app)' % len(tas))

    if push:
        msg = 'tasas BCV al %s (USD %s)' % (fecha, rows[fecha]['USD'])
        for cmd in (['git', 'add', 'tasas.json', 'data/tasas_bcv.csv'],
                    ['git', 'commit', '-m', msg],
                    ['git', 'push']):
            r = subprocess.run(cmd, cwd=APP)
            if r.returncode != 0:
                print('  fallo:', ' '.join(cmd))
                return 1
        print('OK  publicado')
    return 0


if __name__ == '__main__':
    sys.exit(main())
