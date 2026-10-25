# M4 - El sistema ve: foto del producto, ¿lo tenemos? (S11, S12, S13)

**SI4006 - Universidad EAFIT - 2026-2** - Maximiliano Bustamante, Valeria Frances Hornung, Sebastián Castaño, Alejandro Posada

## La pregunta del usuario

Un comprador tiene un producto en la mano, o una foto de él, y no sabe cómo se llama exactamente: *"¿Tienen este celular?"* + foto. Hasta M3, Digitdeck solo entendía texto: si la persona no sabía escribir el nombre del producto, el sistema adivinaba. Con la pregunta sola, M3 ofreció un teléfono Alcatel para la foto de un iPhone y harina de maíz para la foto de una playa.

## El patrón y el modelo

**Visión como INPUT** con **Qwen2-VL-2B-Instruct**. El catálogo de M3 (80.383 fichas de ESCI en español) **no tiene imágenes**, y SQID, la extensión de ESCI con imágenes, solo cubre el locale `us`: no hay foto contra la cual comparar la del comprador. Por eso la foto se traduce a texto y entra por la puerta que M3 ya sabe usar, que es el patrón con menos piezas nuevas.

## Dónde se enchufó

`ver()` va **antes del RAG** y el sistema de M3 no se reescribe:

1. `ver(foto)`: el VLM devuelve un JSON validado (`es_producto`, `tipo_producto`, `marca`, `modelo`, `color`, `texto_visible`).
2. Si no hay producto identificable, el sistema se abstiene ("No se aprecia en la imagen un producto que pueda buscar").
3. La **consulta se arma con los campos del JSON**; no la reescribe el enrutador (la lección de M3, donde el enrutador escribió "merienda" en vez de "Mérida").
4. El **enrutador de M3** solo decide si se busca o no (un antibiótico con receta, por ejemplo, no se busca).
5. `verificar_existencia` de M3 (híbrida BM25 + densa, reranker de M1, umbral de exacto) y el generador de M3 responden citando las fichas.
6. Sin foto, `sistema_multimodal` llama a `sistema_D` de M3 **tal cual**.

Cada respuesta con foto lleva un **estado** (respuesta, sin resultados, abstención del enrutador, válvula, error de formato, error operativo). Los errores no cuentan como abstención correcta (revisión de M3, M3-01).

## La tabla de delta

Corrida local de referencia (RTX 5060 Ti 16 GB), desde cero. M3 = sistema D de M3; con foto, M3 recibe la pregunta sola. Techo = M3 con la pregunta que escribiría alguien que sabe qué es el producto. **M4.1** es una variante diseñada después de ver la primera corrida.

| Grupo | M3 | M4 | M4.1 (post hoc) | Techo | Lectura |
|---|---|---|---|---|---|
| Sin foto (49 de M3): aciertos D3 | 17/49 | 17/49 | igual a M4 | | ¿empeoró lo viejo? No: 49/49 respuestas idénticas |
| Sin foto: nDCG@10 existencia | 0,453 | 0,453 | igual a M4 | | |
| Con foto (12): aciertos, **D3 de M3 (oficial)** | 3/12 | 4/12 | 7/12 | 8/10 | ¿se responden ahora? Algunas; lejos del techo |
| Con foto: regla del CSV, 1 de 3 (complemento) | 3/12 | 5/12 | 9/12 | 10/10 | |
| Con foto: primera cita es el producto (complemento) | 3/12 | 5/12 | 8/12 | 10/10 | |
| Adversariales (4) | 2/4 | 1/4 | 4/4 | | ¿se negó cuando debía? M4 no; M4.1 sí |
| Afirmaciones falsas con foto | 8 | 5 | 2 | 0 | ¿dijo que sí sin tenerlo? |
| Latencia media con foto | 2,33 s | 3,77 s (ver 1,72 s) | 4,59 s (ver 3,05 s) | | ¿cuánto cuesta ver? +1,44 s por caso |
| Latencia p95 con foto | 5,15 s | 5,95 s | 6,48 s | | |
| Peor caso | | img_10 | img_06 (y img_05) | | ver abajo |

Modelo más pesado: el VLM, con 2.209 M de parámetros. Pico de memoria de GPU: 9,95 GB. Tabla completa en [`Resultados/delta_m4.csv`](Resultados/delta_m4.csv); caso por caso en [`scorecard_m4.csv`](scorecard_m4.csv).

## El peor caso

**M4, img_10 (una playa, sin ningún producto).** `ver()` respondió `{"es_producto": true, "tipo_producto": "rocas"}`, la búsqueda con la consulta "rocas" devolvió fichas de la marca Roca y el sistema contestó "Sí, lo tenemos" con bisagras y asientos de inodoro. **Leyó mal la foto** (la válvula escrita en el prompt no bastó) **y buscó con una sola palabra genérica**. Qué haríamos: exigir que el JSON traiga al menos marca o modelo antes de buscar, y medir la válvula en más fotos sin producto.

**M4.1, img_06 (Nintendo Switch 2, que no está en el catálogo).** El VLM leyó "control de videojuegos Nintendo Switch" y el sistema afirmó tener mandos Pro Controller: es una **afirmación falsa**. La foto no tiene texto y el VLM no distingue generaciones de consola (en M4, el texto visible "Nintendo Switch" fue inventado). La regla automática del notebook (nota y campos) señala img_05 (estufa leída como termómetro), pero ahí el sistema solo ofreció parecidos; img_06 es el fallo más grave.

## Los límites

- **No diagnostica ni decide:** el VLM describe; quien decide si es el producto es el catálogo y, al final, la persona.
- **Foto y ficha, por separado y sin inferir stock:** la respuesta termina con lo que se vio en la foto y aclara que las fichas son del catálogo histórico de ESCI (Amazon España), no del inventario actual.
- **La válvula no está garantizada:** en M4 el VLM convirtió una playa en "rocas"; con el antibiótico (img_09) el enrutador no se negó y la abstención vino del umbral.
- **No se genera ninguna imagen**, así que no aplica la etiqueta de "imagen generada".
- **Datos personales:** las 12 fotos son de Wikimedia Commons y Unsplash, con licencia libre, sin caras ni documentos personales y sin metadatos EXIF. Autor y licencia en [`eval_set/fuentes_imagenes.csv`](eval_set/fuentes_imagenes.csv). El sistema no guarda la foto: en las salidas solo queda el JSON de `ver()`.
- **Sesgo de contexto:** img_08 (Pony Malta, una bebida de malta latinoamericana) mide qué pasa con un producto latinoamericano en un catálogo de Amazon España.
- **12 casos.** Un caso más o menos mueve 8 puntos porcentuales; M4.1 se ajustó mirando estos mismos casos.
