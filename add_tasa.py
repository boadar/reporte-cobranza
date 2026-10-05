# -*- coding: utf-8 -*-
"""Agrega la tasa de un dia y la publica SIN generar una version nueva de la app.

La app trae las tasas incrustadas como respaldo, pero al abrir busca tasas.json
en el servidor y mezcla lo nuevo. Por eso aqui solo hay que tocar el CSV, volver
a generar tasas.json y subir esos dos archivos.

Uso:
    python add_tasa.py 2026-07-20 736.9339 843.1998
    python add_tasa.py 2026-07-20 736.9339 843.1998 --push
    python add_tasa.py 2026-07-20 736.9339 843.1998 --fin-de-semana   # llena tambien sab y dom previos

PUBLICACION A PRUEBA DE CONFLICTOS (--push):
    El boton "referencial" de la app tambien escribe tasas.json (via la API de
    GitHub). Para que los dos publicadores NO choquen, al publicar la rutina:
      - se pone SIEMPRE sobre lo ultimo del remoto (sin rebase, sin quedar colgada),
      - UNE las fechas que solo trajo el boton (no las pierde),
      - en las fechas compartidas MANDA la rutina (el valor del CSV/BCV),
      - reintenta si otro publicador se adelanta.
    Guarda de seguridad: si el repo tiene cambios/commits ajenos (p. ej. un cambio
    de index.html sin subir), NO hace reset; publica en modo simple o avisa.

Para cambiar la app (pantallas, calculos, plantillas de banco) sigue haciendo
falta build.py con el numero de version subido.
"""
import csv, os, sys, json, shutil, datetime, subprocess, time

APP = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(os.path.dirname(APP), 'data', 'tasas_bcv.csv')   # maestra, fuera del repo
REPO = os.path.join(APP, 'data', 'tasas_bcv.csv')                    # copia del repo
DIAS = ['Lunes', 'Martes', 'Miercoles', 'Jueves', 'Viernes', 'Sabado', 'Domingo']
DATA_FILES = {'tasas.json', 'data/tasas_bcv.csv'}
TASAS_JSON = os.path.join(APP, 'tasas.json')


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


def csv_to_tas(path):
    """Diccionario { 'AAAA-MM-DD': [usd, eur] } a partir del CSV."""
    tas = {}
    with open(path, newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            tas[r['Fecha']] = [float(r['USD']) if r['USD'] else None,
                               float(r['EUR']) if r['EUR'] else None]
    return tas


def write_tasas(tas):
    """Escribe tasas.json ordenado por fecha (diffs estables)."""
    ordenado = {k: tas[k] for k in sorted(tas)}
    with open(TASAS_JSON, 'w', encoding='utf-8') as f:
        json.dump(ordenado, f, ensure_ascii=False, separators=(',', ':'))


def git(*cmd):
    return subprocess.run(['git', *cmd], cwd=APP, capture_output=True, text=True)


def git_show(ref):
    r = git('show', ref)
    return r.stdout if r.returncode == 0 else None


def solo_cambios_de_datos():
    """True si el repo solo difiere en los archivos de tasas (sin trabajo ajeno
    sin subir). Evita que un reset destructivo toque, p. ej., un index.html pendiente."""
    r = git('status', '--porcelain', '--untracked-files=no')
    for line in r.stdout.splitlines():
        f = line[3:].strip().strip('"')
        if f and f not in DATA_FILES:
            return False
    git('fetch', 'origin', 'main')
    r = git('log', '--name-only', '--pretty=format:', 'origin/main..HEAD')
    for f in (x.strip().strip('"') for x in r.stdout.splitlines() if x.strip()):
        if f not in DATA_FILES:
            return False
    return True


def publicar(msg, csv_derived):
    """Publica tasas.json + CSV uniendo con lo del remoto y reintentando."""
    if not solo_cambios_de_datos():
        # Hay cambios/commits ajenos sin subir: no arriesgamos un reset. Modo simple.
        for cmd in (('add', 'tasas.json', 'data/tasas_bcv.csv'),
                    ('commit', '-m', msg), ('push',)):
            if git(*cmd).returncode != 0:
                print('  AVISO: no se pudo publicar en modo simple (hay cambios ajenos en el repo).')
                print('         Sube manualmente con: git pull --rebase && git push')
                return 1
        print('OK  publicado (modo simple)')
        return 0

    for intento in range(1, 7):
        git('fetch', 'origin', 'main')
        remote_txt = git_show('origin/main:tasas.json')
        try:
            remote = json.loads(remote_txt) if remote_txt else {}
        except Exception:
            remote = {}
        # Union: parte de lo del remoto (fechas referenciales del boton) y encima
        # el CSV de la rutina, que MANDA en las fechas compartidas.
        final = dict(remote)
        final.update(csv_derived)
        # Alinear a lo ultimo del remoto y reaplicar nuestros dos archivos encima.
        git('reset', '--hard', 'origin/main')
        shutil.copyfile(BASE, REPO)   # el CSV maestro (fuera del repo) conserva la fila nueva
        write_tasas(final)
        git('add', 'tasas.json', 'data/tasas_bcv.csv')
        if git('diff', '--cached', '--quiet').returncode == 0:
            print('OK  sin cambios por publicar (el remoto ya estaba al dia)')
            return 0
        if git('commit', '-m', msg).returncode != 0:
            print('  fallo el commit')
            return 1
        if git('push').returncode == 0:
            print('OK  publicado (%d dias)' % len(final))
            return 0
        print('  push rechazado (otro publicador se adelanto); reintentando %d/6...' % intento)
        time.sleep(1.5)
    print('  AVISO: no se pudo publicar tras 6 intentos. Sube manualmente: git pull --rebase && git push')
    return 1


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

    csv_derived = csv_to_tas(REPO)
    write_tasas(csv_derived)   # version local (sin union; se unira al publicar)
    print('OK  tasas.json regenerado: %d dias (sin cambiar la version de la app)' % len(csv_derived))

    if push:
        msg = 'tasas BCV al %s (USD %s)' % (fecha, rows[fecha]['USD'])
        return publicar(msg, csv_derived)
    return 0


if __name__ == '__main__':
    sys.exit(main())
