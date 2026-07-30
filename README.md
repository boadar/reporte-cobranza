# Reporte de Cobranza

PWA para registrar pagos de clientes desde una foto o PDF del comprobante.
Lee el comprobante con OCR (imágenes) o texto (PDF), aplica plantillas por banco
(Banesco, BDV, Bancaribe), calcula el monto en $ con la tasa BCV del día,
sugiere el cliente por el nombre del archivo y lo asigna a un cliente.

**App en vivo:** https://boadar.github.io/reporte-cobranza/

## App unificada (3 pestañas)

La app reúne dos herramientas de cobranza en un solo lugar, con barra de pestañas abajo:

- **Inicio / Cobranzas** — lectura de comprobantes por OCR, asignación a cliente/factura y reporte por correo (el flujo original).
- **Análisis** — el "Control de Cobranza Local" (`control-local.html`): carga un Excel/CSV de cuentas por cobrar, muestra facturas vencidas / por vencer / notas de crédito / pendientes, filtra por vendedor, año/mes y cliente, y exporta el reporte por vendedor (HTML individual o ZIP de todos).

`control-local.html` es una app autocontenida (funciona también abierta suelta). Se integra
embebida en un `<iframe>` dentro de la pestaña Análisis, así que no comparte estilos ni
variables con la PWA. Su botón "📸 Reportar con Comprobante" salta a la pantalla OCR de la
PWA cuando está embebido, o abre la app en vivo si se usa suelta. Está precacheada en el
service worker para funcionar offline.

## Estructura

- `template.html` — fuente de la verdad (marcadores `__CLIENTES__`, `__TASAS__`, `__PWA_HEAD__`, `__PWA_HOOK__`).
- `build.py` — regenera los JSON desde `data/*.csv`, inyecta todo y genera `index.html` + `manifest.webmanifest` + `sw.js`.
- `data/clientes.csv` — base de clientes (`Codigo`, `Nombre`).
- `data/tasas_bcv.csv` — tasas BCV por día (`Fecha`, `Dia`, `USD`, `EUR`).
- `data/cxc.csv` — facturas pendientes por cobrar (`Codigo`, `Cliente`, `Factura`, `Tipo`, `Vencimiento`, `Base`, `IVA`, `TotalPorPagar`, `Observacion`). Montos en **$**. El `Codigo` se resuelve por nombre desde el archivo CxC original.
- `index.html`, `manifest.webmanifest`, `sw.js`, `icon-*.png` — generados / assets.

## Cómo actualizar (incluso desde Claude Code en la web)

1. **Cambiar la app:** editar `template.html`.
2. **Agregar tasas nuevas:** agregar filas a `data/tasas_bcv.csv` (formato `2026-07-16,Jueves,730.12,835.40`).
3. **Actualizar clientes:** reemplazar `data/clientes.csv`.
3b. **Actualizar facturas pendientes:** reemplazar `data/cxc.csv` (se genera desde el `cxc <fecha>.xlsx` original: cols B=Factura, C=Tipo, D=Cliente, J=Vencimiento, L=Base, M=IVA, P=Total x Pagar, Q=Observación; el código de cliente se resuelve por nombre normalizado).
4. Subir el número de `CACHE_NAME` en `build.py` (ej. `-v3` → `-v4`) para refrescar el caché de los teléfonos.
5. Correr `python build.py`.
6. Commit + push a `main`. GitHub Pages reconstruye en 1-2 min.

## Notas

- Primera carga necesita internet (descarga el motor OCR); luego funciona offline.
- Las cobranzas se guardan localmente en el teléfono (localStorage) y se exportan a CSV.
- Base consolidada multi-vendedor: pendiente (requiere un backend en la nube).
