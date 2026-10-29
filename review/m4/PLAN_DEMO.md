# Plan sugerido para Demo Day — Digitdeck

Orientación docente, no formato oficial. Tres prioridades; el resto queda en backlog. La decisión de quién asume cada una es del equipo.

## P0 — Que el pipeline arranque fuera de Windows

- **Qué podría ocurrir durante la demo:** en Colab o en un servidor Linux (URL pública de S15), el notebook se detiene en la celda 9 con `AssertionError: El split de test no es el de M1.` y no llega a `ver()`.
- **Evidencia exacta:** celda 9 de `Entregables/M4/pipeline/ENTREGABLE.ipynb` @ `6afab21`; con los parquet públicos de ESCI, el código tal cual da `331ee032…` en macOS y el `lineterminator="\r\n"` da `4d31950e…` (el de M1).
- **Cambio mínimo recomendado:** la línea de C1 (PR correctivo). Correr el notebook completo una vez en Colab T4 y guardar la versión de paquetes.
- **Qué NO hace falta rehacer:** el hash de M1, el catálogo ni las cifras de M4.
- **Cómo verificar el cierre:** la celda 9 imprime `coincide con M1: True` en Colab y el notebook llega a la tabla de delta sin intervención (salvo el token, si se mantiene).
- **Relación con la nota:** criterio de la entrega (S13: correr desde cero en Colab) y recomendación final.

## P1 — No afirmar con una lectura que no identifica el producto

- **Qué podría ocurrir durante la demo:** una foto sin producto o borrosa termina en "Sí, lo tenemos" (img_10: asientos de inodoro Roca para una playa; img_11: auriculares cualquiera), o un producto distinto se presenta como el exacto (img_06 en M4.1, img_03 en M4).
- **Evidencia exacta:** `Resultados/salidas_m4.json` (`ver_json` sin marca ni modelo y apertura "afirma"), `scorecard_m4.csv` (`afirmacion_falsa_m4`), INFORME_M4 §7.
- **Cambio mínimo recomendado:** la regla que el equipo ya propuso: si no hay marca ni modelo, pedir el dato antes de buscar (C2, opt-in); cuando la ficha no es el producto leído, usar la apertura de "parecidos".
- **Qué NO hace falta rehacer:** cambiar de VLM, reentrenar el reranker o rediseñar el enrutador.
- **Cómo verificar el cierre:** con img_10, img_11 y al menos 3 fotos nuevas sin producto o ilegibles, ninguna respuesta empieza por "Sí, lo tenemos"; img_07 sigue respondiendo.
- **Relación con la nota:** recomendación final.

## P1 — Una sola versión y cifras que se sostengan

- **Qué podría ocurrir durante la demo:** se cita el `scorecard_m4.csv` antiguo o se presenta M4.1 (7/12) como resultado medido, cuando se ajustó sobre los mismos 12 casos.
- **Evidencia exacta:** `Entregables/M4/Resultados/scorecard_m4.csv` difiere del oficial en img_01 e img_07; positivos D3: M3 sola 1/6, M4 1/6, M4.1 2/6.
- **Cambio mínimo recomendado:** retirar o renombrar el scorecard antiguo; elegir la versión de la demo y medirla en 5–6 fotos nuevas no vistas, con denominadores y latencia.
- **Qué NO hace falta rehacer:** el eval set de 12 casos ni el harness.
- **Cómo verificar el cierre:** un único scorecard por versión, tabla con casos nuevos separada de los 12 originales.
- **Relación con la nota:** recomendación final.

## Narrativa sugerida

Problema ("lo tengo en la mano y no sé cómo se llama") → caso real (img_07 o img_08) → qué aporta la foto (consulta construida desde lo visto, menos afirmaciones falsas) → calidad y costo (D3 con denominadores, +1,4 s por foto) → peor caso (img_10) y cómo responde ahora → límites (catálogo histórico, sin stock, VLM de 2B).
