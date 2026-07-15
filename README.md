# Reporte de Cobranza

PWA para registrar pagos de clientes desde una foto o PDF del comprobante.
Lee el comprobante con OCR (imágenes) o texto (PDF), aplica plantillas por banco
(Banesco, BDV, Bancaribe), calcula el monto en $ con la tasa BCV del día,
sugiere el cliente por el nombre del archivo y lo asigna a un cliente.

**App en vivo:** https://boadar.github.io/reporte-cobranza/

## Estructura

- `template.html` — fuente de la verdad (marcadores `__CLIENTES__`, `__TASAS__`, `__PWA_HEAD__`, `__PWA_HOOK__`).
- `build.py` — regenera los JSON desde `data/*.csv`, inyecta todo y genera `index.html` + `manifest.webmanifest` + `sw.js`.
- `data/clientes.csv` — base de clientes (`Codigo`, `Nombre`).
- `data/tasas_bcv.csv` — tasas BCV por día (`Fecha`, `Dia`, `USD`, `EUR`).
- `index.html`, `manifest.webmanifest`, `sw.js`, `icon-*.png` — generados / assets.

## Cómo actualizar (incluso desde Claude Code en la web)

1. **Cambiar la app:** editar `template.html`.
2. **Agregar tasas nuevas:** agregar filas a `data/tasas_bcv.csv` (formato `2026-07-16,Jueves,730.12,835.40`).
3. **Actualizar clientes:** reemplazar `data/clientes.csv`.
4. Subir el número de `CACHE_NAME` en `build.py` (ej. `-v3` → `-v4`) para refrescar el caché de los teléfonos.
5. Correr `python build.py`.
6. Commit + push a `main`. GitHub Pages reconstruye en 1-2 min.

## Notas

- Primera carga necesita internet (descarga el motor OCR); luego funciona offline.
- Las cobranzas se guardan localmente en el teléfono (localStorage) y se exportan a CSV.
- Base consolidada multi-vendedor: pendiente (requiere un backend en la nube).
