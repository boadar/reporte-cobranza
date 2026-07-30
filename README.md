# Reporte de Cobranza

App de cobranza en dos partes, servidas juntas como una sola PWA instalable:

- **`index.html` — Control de Cobranza (pantalla de inicio).** Muestra facturas vencidas /
  por vencer / notas de crédito / pendientes, filtra por vendedor, año/mes y cliente, y
  exporta el reporte por vendedor (HTML individual o ZIP de todos). Es el archivo
  `control_cobranza_final`. Al abrir, **carga la cartera automáticamente desde GitHub**
  (`cartera.json` + `tasas.json`), igual que el lector de pagos; si esos archivos no
  existen o no hay señal, se puede cargar el Excel/CSV a mano como antes.
- **`comprobante.html` — Reporte con Comprobante (OCR).** Se abre desde el botón
  "📸 Reportar con Comprobante" del control. Lee el comprobante con OCR (imágenes) o
  texto (PDF), aplica plantillas por banco (Banesco, BDV, Bancaribe, Mercantil…),
  calcula el monto en $ con la tasa BCV del día y lo asigna a un cliente. Tiene un
  botón "‹ Volver" que regresa al control.

**App en vivo:** https://boadar.github.io/reporte-cobranza/

## Estructura

- `template.html` — fuente de la verdad del lector OCR (marcadores `__CLIENTES__`, `__TASAS__`, `__PWA_HEAD__`, `__PWA_HOOK__`).
- `build.py` — regenera los JSON desde `data/*.csv`, inyecta todo y genera `comprobante.html` (el lector OCR) + `manifest.webmanifest` + `sw.js`.
- `index.html` — el Control de Cobranza (pantalla de inicio). Es un archivo autónomo; NO lo genera `build.py`, se edita directo.
- `data/clientes.csv` — base de clientes (`Codigo`, `Nombre`).
- `data/tasas_bcv.csv` — tasas BCV por día (`Fecha`, `Dia`, `USD`, `EUR`).
- `data/cxc.csv` — facturas pendientes por cobrar (`Codigo`, `Cliente`, `Factura`, `Tipo`, `Vencimiento`, `Base`, `IVA`, `TotalPorPagar`, `Observacion`). Montos en **$**. El `Codigo` se resuelve por nombre desde el archivo CxC original.
- `comprobante.html`, `manifest.webmanifest`, `sw.js`, `icon-*.png` — generados / assets.
- `cartera.json` — cartera del Control de Cobranza (arreglo de documentos con
  `Denominación social`, `Numero de Factura`, `Tipo de documento`, `ESTATUS`,
  `Fecha de Ven`, `Total Fac X Pagar`, `Base`, `IVA`, `Observacion`,
  `Secretario de ventas`). Lo lee `index.html` al abrir. Se genera cargando el Excel de
  cuentas por cobrar en la app y pulsando **"💾 GENERAR cartera.json (publicar)"**, y
  luego subiéndolo al repo. (No lo produce `build.py`.)

## Cómo actualizar (incluso desde Claude Code en la web)

1. **Cambiar la app:** editar `template.html`.
2. **Agregar tasas nuevas:** agregar filas a `data/tasas_bcv.csv` (formato `2026-07-16,Jueves,730.12,835.40`).
3. **Actualizar clientes:** reemplazar `data/clientes.csv`.
3b. **Actualizar facturas pendientes:** reemplazar `data/cxc.csv` (se genera desde el `cxc <fecha>.xlsx` original: cols B=Factura, C=Tipo, D=Cliente, J=Vencimiento, L=Base, M=IVA, P=Total x Pagar, Q=Observación; el código de cliente se resuelve por nombre normalizado).
3c. **Actualizar la cartera del Control de Cobranza:** abrir la app, cargar el Excel de
    cuentas por cobrar, pulsar **"💾 GENERAR cartera.json (publicar)"**, y subir el
    `cartera.json` descargado al repo (reemplaza el anterior). No hace falta subir versión:
    la app lo lee al abrir. (Debe traer la columna `Secretario de ventas` para agrupar por vendedor.)
4. Subir el número de `CACHE_NAME` en `build.py` (ej. `-v3` → `-v4`) para refrescar el caché de los teléfonos.
5. Correr `python build.py`.
6. Commit + push a `main`. GitHub Pages reconstruye en 1-2 min.

## Notas

- Primera carga necesita internet (descarga el motor OCR); luego funciona offline.
- Las cobranzas se guardan localmente en el teléfono (localStorage) y se exportan a CSV.
- Base consolidada multi-vendedor: pendiente (requiere un backend en la nube).
