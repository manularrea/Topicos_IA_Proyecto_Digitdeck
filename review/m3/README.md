# Revisión docente M3 — Digitdeck

## Referencia y alcance

Revisión técnica aprobada para publicación, sin calificación académica pública. Se evalúa M3; M1/M2 solo por su contribución a M3. Las sugerencias para M4 y Demo no son requisitos retroactivos ni condiciones para la nota. Las pruebas y propuestas docentes no son aportes atribuibles a la entrega original.

Original: `AlejandroSPosada/Topicos_IA_Proyecto_Digitdeck`; fork: `manularrea/Topicos_IA_Proyecto_Digitdeck`. Referencia evaluada: [`1ead5646a01286e9e043557aba83afec5e9c639a`](https://github.com/AlejandroSPosada/Topicos_IA_Proyecto_Digitdeck/tree/1ead5646a01286e9e043557aba83afec5e9c639a), fechada el 27/09/2026 a las 22:25:51 en Colombia, anterior al cierre. No se confunde la fecha UTC del 28 con retraso; el commit no sustituye el recibo de Interactiva.

Base académica: [S10 del curso](https://github.com/manularrea/EAFIT-SI4006/blob/753c4ac955e927172dcf4e5a710a2e0cb062f781/sesiones/s10/README.md) y rúbrica reproducida en el [README M3](https://github.com/AlejandroSPosada/Topicos_IA_Proyecto_Digitdeck/blob/1ead5646a01286e9e043557aba83afec5e9c639a/Entregables/M3/README.md). Se reconocen las dos técnicas avanzadas, herramientas, scorecard, cuatro métricas y análisis. El cálculo manual fue enseñado; no se exige biblioteca RAGAS, W&B, DSPy, ReAct ni un umbral inventado de precisión.

## Reconocimientos

**Integración efectiva.** El clasificador de pares de M1 se reutiliza como reranker y el harness de M2 se adapta a existencia y sustitutos. A/B/C comparan búsqueda densa, híbrida con RRF y reranking. El equipo declara que C→D mezcla enrutamiento, reformulación, umbrales y verificación: no atribuir su delta exclusivamente al tool use.

**Validación del evaluador.** Se documentan tres anotadores sobre 50 pares y contraste Qwen/Phi con mayoría humana, manteniendo la vara ESCI y la corrección parcial del equipo. No se afirma que todo el catálogo esté validado ni que la escala de pantallas 1–5 haya quedado plenamente calibrada.

**Trazabilidad y lectura de resultados.** Hay detalle por pregunta, denominadores, latencias, bootstrap pareado, respuestas originales y presentadas. Se distinguen casos conocidos y nuevos, se reportan regresiones y limitaciones de similares. La selección correcta de herramienta no se equipara a responder correctamente. El catálogo histórico no se presenta aquí como inventario comercial en vivo.

Fuentes: [INFORME_M3, §§2–10](https://github.com/AlejandroSPosada/Topicos_IA_Proyecto_Digitdeck/blob/1ead5646a01286e9e043557aba83afec5e9c639a/Entregables/M3/INFORME_M3.md), [notebook](https://github.com/AlejandroSPosada/Topicos_IA_Proyecto_Digitdeck/blob/1ead5646a01286e9e043557aba83afec5e9c639a/Entregables/M3/ENTREGABLE.ipynb). Las referencias c033, c035, c037 y c043 identifican el campo id de la celda, no execution_count.

## Observaciones accionables

### M3-01 — Llamadas y fallos operativos (c035/c043)

Ya existe abstención por no selección o lista vacía. El ajuste no consiste en inventar esa capacidad, sino en validar `args.consulta` sin convertir listas/objetos/números a texto y aislar excepciones del backend por caso. Una caída del índice no demuestra que no exista el producto y no debe contar como acierto de abstención.

La propuesta C1 añade una variante opt-in `D_revision`, con estado de error separado, cobertura y exclusión explícita de casos fallidos de D1/D3. Conserva herramientas, prompts, umbrales, consulta válida propuesta y presentación del equipo. No promete mejoras de calidad por esta corrección de contrato. Su incorporación debe seguir las instrucciones del PR correctivo.

### M3-02 — D3 no valida todo el texto (c033/c035/c037)

D3 está definido como pantalla y apertura. Una prueba controlada puede aprobar ambas aunque el texto cite un identificador desconocido; el lector original solo enumera ids del contexto. Una respuesta mixta puede mantener la bandera de abstención por su prefijo.

Se propone mantener D3 y añadir auditoría sintáctica separada: citas emitidas/recuperadas/desconocidas, falta de marcador con contexto y abstención no idéntica al contrato. No es una certificación semántica, de stock ni de corrección comercial. No se afirma que estos casos controlados ocurrieran en las respuestas históricas. El estado de publicación de la propuesta ejecutable C2 debe consultarse en el PR, no inferirse de este documento.

En el detalle publicado, cinco de las seis filas de D marcadas como falsas por su propia métrica de dominio tienen faithfulness=1. Es un cruce de dos criterios del equipo, no una verificación externa de inexistencia del producto. Los productos sin etiquetar son una limitación ya declarada.

### Orientación M4/Demo — Índice y documentación

La colección se reutiliza por conteo aunque cambien textos (c024/c025). El notebook YA pide reconstruir manualmente si cambia el texto. Automatizar una firma de ids/textos/configuración/modelo reforzaría esa precaución; no se demostró contaminación de la corrida entregada. Este cambio no forma parte de C1/C2.

Revisar el enlace a `ABLACIONES_M1.ipynb`, ausente de la carpeta consultada; sus resultados SÍ están incluidos. No confundir un enlace pendiente con experimentos inexistentes. Conservar la consulta original junto con la reformulación y medir cualquier alternativa antes de adoptarla. Si M4 añade visión, diferenciar atributos de imagen y ficha sin inferir stock actual.

## Evidencia y límites

El preview registró 45 comprobaciones docentes, reejecutadas antes de publicar: identidad de tres CSV completos por Git blob, 196 filas, reconstrucción de 80 celdas del scorecard y 12 deltas con IC. Se auditan agregaciones del detalle, no se repiten juicios ni toda la recuperación. Una caracterización que reproduce un defecto no es una regresión que lo corrige.

Se prepararon y probaron 68 regresiones adicionales de C1/C2 con callbacks controlados. El original del notebook no pudo clonarse por DNS; la comparación local utiliza funciones seleccionadas transcritas y claramente identificadas, no el notebook entero. No se cargaron modelos, pesos, Chroma, embeddings, GPU ni APIs. Validar un lote pequeño en el entorno real antes de incorporar cambios. La existencia local de un test no se presenta como garantía de su publicación: el PR correctivo especifica sus archivos efectivos.

## Publicación

Este PR es documental. Las propuestas ejecutables se separan de esta revisión. No se modifican `main`, notebook, corpus, modelos, D3, RAGAS ni resultados históricos. Las extensiones requieren activación explícita; no se anuncian como ya activadas en el sistema del equipo. La nota se comunica por el canal privado.
