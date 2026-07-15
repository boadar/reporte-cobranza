# Reporte de Cobranza

PWA para registrar pagos de clientes desde una foto del comprobante.
Lee el comprobante con OCR, aplica plantillas por banco (Banesco, BDV, Bancaribe),
calcula el monto en $ con la tasa BCV del día y lo asigna a un cliente.

- `template.html` + `build.py` = fuente; `index.html` se genera.
- Datos embebidos: `clientes.json`, `tasas.json`.
