# -*- coding: utf-8 -*-
"""Convierte el xlsx de CxC a data/cxc.csv resolviendo el codigo de cliente por nombre."""
import openpyxl, csv, unicodedata, re, os, datetime, collections

SRC = r'C:\Users\RONALD~1.BOA\AppData\Local\Temp\claude\C--Users-ronald-boada-OneDrive---Ofica-Representaciones--S-A-Claude\39e089dd-6432-4e05-927a-faec60c1f3ca\scratchpad\cxc.xlsx'
CLI = r'C:\Users\ronald.boada\OneDrive - Ofica Representaciones, S.A\Claude\data\clientes.csv'
OUT = r'C:\Users\ronald.boada\OneDrive - Ofica Representaciones, S.A\Claude\ReporteCobranza\data\cxc.csv'


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

wb = openpyxl.load_workbook(SRC, data_only=True)
ws = wb.active

def d2s(v):
    if isinstance(v, datetime.datetime):
        return v.strftime('%d/%m/%Y')
    return str(v).strip() if v is not None else ''

def num(v):
    return round(float(v), 2) if isinstance(v, (int, float)) else ''

rows = []
sin = collections.Counter()
for r in ws.iter_rows(min_row=2, values_only=True):
    if r[1] is None:
        continue
    nombre = str(r[3]).strip() if r[3] else ''
    cod = idx.get(norm(nombre), '')
    if not cod:
        sin[nombre] += 1
    rows.append([
        cod,                       # Codigo cliente resuelto
        nombre,                    # D Denominacion social
        str(r[1]).strip(),         # B Numero de Factura
        str(r[2]).strip() if r[2] else '',   # C Tipo de documento
        d2s(r[9]),                 # J Fecha de Ven
        num(r[11]),                # L Base
        num(r[12]),                # M IVA
        num(r[15]),                # P Total Fac X Pagar
        str(r[16]).strip() if r[16] else '',  # Q Observacion
    ])

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['Codigo', 'Cliente', 'Factura', 'Tipo', 'Vencimiento', 'Base', 'IVA', 'TotalPorPagar', 'Observacion'])
    w.writerows(rows)

conCod = sum(1 for r in rows if r[0])
print('facturas:', len(rows), '| con codigo:', conCod, '| sin codigo:', len(rows) - conCod)
print('clientes sin codigo:', len(sin))
for n, c in sin.most_common():
    print('   -', n, '(%d facturas)' % c)
print('CSV:', OUT)
