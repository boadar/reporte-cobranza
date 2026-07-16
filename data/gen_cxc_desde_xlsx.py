# -*- coding: utf-8 -*-
"""Convierte el xlsx de CxC a data/cxc.csv.
- Resuelve el codigo de cliente por nombre normalizado contra clientes.csv.
- Agrega Fecha de la factura (col A), la Tasa BCV de esa fecha (del historico),
  IVA Bs. = IVA $ x Tasa, y 25% IVA = IVA Bs. x 0.25.
Uso: python gen_cxc_desde_xlsx.py "<ruta del cxc.xlsx>"
"""
import openpyxl, csv, unicodedata, re, os, sys, datetime, collections

D = os.path.dirname(os.path.abspath(__file__))
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(D, 'cxc_origen.xlsx')
CLI = os.path.join(D, 'clientes.csv')
TAS = os.path.join(D, 'tasas_bcv.csv')
OUT = os.path.join(D, 'cxc.csv')


def norm(s):
    s = unicodedata.normalize('NFD', str(s))
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn').lower()
    s = re.sub(r'[^a-z0-9]+', ' ', s).strip()
    s = re.sub(r'\b(c a|ca|compania anonima|s a|sa|srl|rl|cia)\b', '', s).strip()
    return re.sub(r'\s+', ' ', s)


idx = {}
with open(CLI, encoding='utf-8') as f:
    for row in csv.DictReader(f):
        idx.setdefault(norm(row['Nombre']), row['Codigo'])

tasas = {}
with open(TAS, encoding='utf-8') as f:
    for row in csv.DictReader(f):
        if row['USD']:
            tasas[row['Fecha']] = float(row['USD'])

wb = openpyxl.load_workbook(SRC, data_only=True)
ws = wb.active


def d2s(v):
    return v.strftime('%d/%m/%Y') if isinstance(v, datetime.datetime) else (str(v).strip() if v is not None else '')


def num(v):
    return round(float(v), 2) if isinstance(v, (int, float)) else None


rows, sin_cod, sin_tasa = [], collections.Counter(), 0
for r in ws.iter_rows(min_row=2, values_only=True):
    if r[1] is None:
        continue
    nombre = str(r[3]).strip() if r[3] else ''
    cod = idx.get(norm(nombre), '')
    if not cod:
        sin_cod[nombre] += 1
    fecha = r[0] if isinstance(r[0], datetime.datetime) else None
    iso = fecha.date().isoformat() if fecha else ''
    tasa = tasas.get(iso)
    if fecha and tasa is None:
        sin_tasa += 1
    iva = num(r[12])
    iva_bs = round(iva * tasa, 2) if (iva is not None and tasa) else None
    iva25 = round(iva_bs * 0.25, 2) if iva_bs is not None else None
    base = num(r[11])
    total = num(r[15])
    rows.append([
        cod, nombre, str(r[1]).strip(), str(r[2]).strip() if r[2] else '',
        d2s(fecha),                              # A  Fecha de la factura
        round(tasa, 4) if tasa else '',          # Tasa BCV de la fecha de la factura
        d2s(r[9]),                               # J  Fecha de Vencimiento
        base if base is not None else '',        # L  Base $
        iva if iva is not None else '',          # M  IVA $
        iva_bs if iva_bs is not None else '',    # IVA Bs.  = IVA $ x Tasa
        iva25 if iva25 is not None else '',      # 25% IVA  = IVA Bs. x 0.25
        total if total is not None else '',      # P  Total por Pagar
        str(r[16]).strip() if r[16] else '',     # Q  Observacion
    ])

with open(OUT, 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['Codigo', 'Cliente', 'Factura', 'Tipo', 'FechaFactura', 'TasaFact',
                'Vencimiento', 'Base', 'IVA', 'IVABs', 'IVA25', 'TotalPorPagar', 'Observacion'])
    w.writerows(rows)

con = sum(1 for r in rows if r[0])
print('facturas:', len(rows), '| con codigo:', con, '| sin codigo:', len(rows) - con)
print('sin tasa (fecha fuera del historico):', sin_tasa)
print('clientes sin codigo:', len(sin_cod))
for n, c in sin_cod.most_common():
    print('   -', n, '(%d)' % c)
print('CSV:', OUT)
