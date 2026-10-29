# Revisión docente M4 — Digitdeck

## Referencia y alcance

Revisión técnica de M4 (integración visual + evaluación), sin calificación académica pública. Referencia evaluada: [`6afab21`](https://github.com/AlejandroSPosada/Topicos_IA_Proyecto_Digitdeck/tree/6afab21) (`main`, 25/10/2026 01:15 hora de Colombia, anterior al cierre del 25/10 23:59). Base académica: S13 (entregables y rúbrica de M4) y S15 (cierre). Las sugerencias para Demo Day no son requisitos retroactivos de M4. Las pruebas y propuestas docentes no son aportes atribuibles a la entrega. Las celdas del notebook se cuentan **desde 0**.

## Reconocimientos

**Integración visual efectiva y trazable.** `ver()` (Qwen2-VL-2B, celda 40) produce un JSON validado cuyos campos construyen la consulta que recibe `verificar_existencia` de M3 (celda 41, `correr_foto`). La salida visual cambia la búsqueda y la respuesta, y se conserva en `salidas_m4.json` (`ver_json`, `consulta_desde_foto`, `pregunta_aumentada`).

**Regresión controlada.** Sin foto, `sistema_multimodal` delega en `sistema_D`. Las 49 respuestas y pantallas sin foto coinciden con `M3/Resultados/salidas_sistemas.json` (comprobado desde los artefactos).

**Seguimiento de la revisión de M3.** Estados `sin_producto`, `abstencion_dominio`, `sin_resultados`, `error_formato` y `error_operativo` con cobertura y exclusión de errores (M3-01); auditoría sintáctica de citas al lado de D3 sin alterar su definición (M3-02); foto y ficha separadas, con aviso de catálogo histórico (orientación M4).

**Evaluación honesta.** Línea base "pregunta sola" y "techo" con pregunta escrita, D3 oficial más dos complementos declarados, latencia por etapa, ablación de "describir antes", procedencia y licencia por imagen, sin EXIF, y una variante post hoc (M4.1) declarada como optimista. El peor caso se analiza con causa y propuesta.

## Observaciones accionables

### M4-01 — El notebook se detiene fuera de Windows (celda 9)

El `assert` del hash del split usa `to_csv(index=False)`, cuyo fin de línea depende del sistema operativo. Con los parquet públicos de ESCI y el código exacto de la celda, en macOS/Linux el hash es `331ee032…` y el notebook se detiene; con `lineterminator="\r\n"` coincide con el de M1 (`4d31950e…`). INFORME_M4 §9.2 menciona esta corrección, pero no está en el notebook entregado. S13 pide que el pipeline corra desde cero en Colab. Propuesta C1 en el PR correctivo (una línea). Las celdas posteriores no se ejecutaron en esta revisión.

### M4-02 — La válvula de `ver()` no basta para no buscar (celda 41)

El equipo ya lo identifica en el peor caso (img_10). En los artefactos, la búsqueda se lanza con lecturas sin marca ni modelo en img_05, img_10 e img_11 (M4), y tres de esas respuestas afirman "Sí, lo tenemos". Ver no es decidir: sugerimos implementar la regla que ustedes proponen (pedir el dato que falta antes de buscar) y medirla con fotos nuevas. La proyección sobre sus artefactos está en la propuesta C2; es post hoc y no mejora los positivos.

### M4-03 — Similar, exacto y disponibilidad

Con foto, el sistema siempre usa `verificar_existencia`, aun en "¿Venden estufas como esta?" (alcance declarado). En img_06 (Switch 2), M4.1 responde "Sí, lo tenemos" con mandos Pro Controller; en img_03, M4 afirma unos EarPods para unos AirPods. Para la demo, conviene que un producto distinto se presente como "parecido" y nunca con la apertura de existencia. El aviso de catálogo histórico ya separa existencia en catálogo de disponibilidad.

### M4-04 — Dos `scorecard_m4.csv`

`Entregables/M4/scorecard_m4.csv` (el que escribe la celda 60 y coincide con `delta_m4.csv`) y `Entregables/M4/Resultados/scorecard_m4.csv` (corrida anterior, otro esquema, distinto en img_01 e img_07). Retirar o renombrar el segundo evita citar cifras que no son las del informe.

### M4-05 — Lectura del delta

Con D3, M4 acierta 1 de 6 positivos, igual que M3 con la pregunta sola; el +1 global viene de no afirmar en img_06 e img_08, y img_06 acierta por accidente (lo reconocen). Sugerimos presentar el aporte visual como "menos afirmaciones falsas y consulta construida desde la foto", con denominadores, y no como mejora de acierto en positivos. M4.1 debe confirmarse con fotos no vistas.

## Evidencia y límites

Nivel alcanzado: **recalculado desde artefactos** (scorecard, delta, latencias media/p95, regresión 49/49, estados, imágenes, EXIF) y **componente real** solo para la celda 9 con datos ESCI públicos. No se cargaron VLM, generador, reranker ni Chroma; no se usó GPU, credenciales ni APIs de pago. No se repitió la inferencia ni se juzgó de nuevo el etiquetado. El video de Teams no se verificó por este canal.

## Publicación

Este PR es documental. Las propuestas ejecutables (C1, C2) van en un PR separado y requieren activación explícita. No se modifican `main`, cifras, CSV ni salidas históricas. La nota se comunica por el canal privado.
