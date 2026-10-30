# Revisión M4: integración visual y evaluación

**Repositorio:** `AlejandroSPosada/Topicos_IA_Proyecto_Digitdeck` · **Commit revisado:** [`6afab21`](https://github.com/AlejandroSPosada/Topicos_IA_Proyecto_Digitdeck/tree/6afab2140abcf712dea14339f5e98f8e448b6828) (`main`, 25-oct 01:15, hora de Colombia), carpeta `Entregables/M4/`.

Esta revisión es técnica. La calificación se comunica por canal privado. Las sugerencias no son requisitos retroactivos ni cambian los criterios que ustedes fijaron antes de correr. Las celdas del notebook se cuentan **desde 0**; los enlaces a líneas usan la vista de texto del `.ipynb`.

---

## 1. Cómo se verificó

Niveles: **L** = lectura · **R** = recálculo desde sus artefactos · **E** = ejecución real · **D** = prueba con dobles o proyección sobre sus artefactos (sin volver a correr modelos).

| Qué | Cómo | Nivel | Resultado |
|---|---|---|---|
| Scorecard y delta con foto | Recálculo de `scorecard_m4.csv` frente a `Resultados/delta_m4.csv` (D3, CSV, cita, adversariales, falsas, latencia media/p95) | R | 11/11 cifras coinciden |
| Regresión sin foto | `Resultados/salidas_m4.json` frente a `M3/Resultados/salidas_sistemas.json` | R | 49/49 respuestas y 49/49 primeras pantallas idénticas |
| Celda 9 (hash del split de test) | Su código exacto con los parquet públicos de ESCI, en macOS | E | Se detiene fuera de Windows (M4-01); con una línea, coincide con M1 |
| `ver()` (M4) y `ver_dos_pasos()` (M4.1) | Celdas 40 y 43 ejecutadas sin cambios con Qwen2-VL-2B real sobre las 12 fotos, en otro hardware (Apple MPS, bf16 y fp16) | E | Marca y modelo iguales a sus trazas en 12/12 (bf16); válvula igual en 11/12; img_10 e img_05 idénticas |
| Enrutador y generador | Qwen2.5-1.5B real (bf16, en MPS) en 8 casos, con sus prompts y las fichas que registraron | E | Enrutador igual 8/8; texto idéntico 6/7 |
| Reranker, Chroma y corrida completa en Colab | — | — | No re-ejecutados: con la misma consulta, la recuperación recibe la misma entrada |
| Eval set e imágenes | Huella de píxeles, EXIF, columna `estado`, procedencia | R | 0 EXIF; 11 imágenes distintas en 12 casos (M4-06) |
| Guardia de lectura propuesta (C2) | Proyección sobre sus `ver_json` | D | Ver M4-02 |

Las diferencias de hardware (MPS frente a su GPU) no se consideran defectos de la entrega. Las latencias que medimos sirven como orden de magnitud y no reemplazan las suyas. El video y los materiales de Teams no se revisaron por este canal.

## 2. Fortalezas comprobadas

1. **La foto decide de verdad.**
   - `ver()` devuelve un JSON validado, y con sus campos se construye la consulta que recibe `verificar_existencia` de M3 (`correr_foto`, celda 41).
   - M4 cambia 8 de 12 respuestas frente a la pregunta sola.
   - Todo queda trazado en `salidas_m4.json` (`ver_json`, `consulta_desde_foto`, `pregunta_aumentada`).
   - Al reproducirlo, sus lecturas de marca y modelo salen iguales en las 12 fotos.
2. **Regresión controlada, poco común.** Sin foto, `sistema_multimodal` delega en `sistema_D` de M3: las 49 respuestas y las 49 pantallas coinciden con M3.
3. **Contrato de estados maduro.** `sin_producto`, `abstencion_dominio`, `sin_resultados`, `error_formato` y `error_operativo` están separados, con cobertura, y los errores quedan fuera de las métricas de acierto. La válvula no se confunde con un JSON inválido.
4. **Evaluación honesta y completa.**
   - Usan la misma D3 de M3, dos complementos declarados, la línea base «pregunta sola» y el techo con pregunta escrita.
   - Miden la latencia por etapa (`ver()` 1,72 s) y el pico de VRAM.
   - La ablación «describir antes» concluye en negativo y lo dicen.
   - M4.1 está rotulada como post hoc y optimista.
   - Explican el peor caso (img_10) con su causa y una propuesta concreta.
5. **Patrón bien justificado y procedencia cuidada.**
   - Eligieron visión como input por la pregunta del usuario («lo tengo en la mano y no sé el nombre») y descartaron CLIP por razones de datos.
   - Cada foto tiene licencia y URL, ninguna tiene EXIF, y etiquetaron 425 fichas del catálogo.

## 3. Observaciones

### M4-01 · El notebook se detiene fuera de Windows (celda 9)
- **Dónde:** [`ENTREGABLE.ipynb`, celda 9, L292](https://github.com/AlejandroSPosada/Topicos_IA_Proyecto_Digitdeck/blob/6afab2140abcf712dea14339f5e98f8e448b6828/Entregables/M4/pipeline/ENTREGABLE.ipynb?plain=1#L292). Compárese con [`INFORME_M4.md` §9.2, L316–325](https://github.com/AlejandroSPosada/Topicos_IA_Proyecto_Digitdeck/blob/6afab2140abcf712dea14339f5e98f8e448b6828/Entregables/M4/INFORME_M4.md?plain=1#L316-L325).
- **Qué se observa:**
  - El hash usa `to_csv(index=False)`, cuyo fin de línea depende del sistema operativo.
  - Con los parquet públicos de ESCI y el código exacto de la celda, en macOS/Linux sale `331ee032…` en vez de `4d31950e…`, y el `assert` detiene el notebook antes de construir el catálogo.
  - El §9.2 de su informe dice «Hash con `\r\n` explícito», pero esa corrección no está en el notebook entregado.
- **Por qué importa:** S13 pide que el pipeline corra desde cero en Colab, y Colab es Linux. Lo mismo ocurrirá en el servidor donde desplieguen en M5.
- **Sugerencia:** `to_csv(index=False, lineterminator="\r\n")`. Es una línea (C1 en CODE_PR) y en Windows no cambia nada.
- **Criterio de cierre:** en Colab la celda imprime `coincide con M1: True` y el notebook llega a la celda 60.

### M4-02 · La válvula de `ver()` no basta para no buscar
- **Dónde:** [`producto_identificado`, celda 40, L1421](https://github.com/AlejandroSPosada/Topicos_IA_Proyecto_Digitdeck/blob/6afab2140abcf712dea14339f5e98f8e448b6828/Entregables/M4/pipeline/ENTREGABLE.ipynb?plain=1#L1421) y [`correr_foto`, celda 41, L1509](https://github.com/AlejandroSPosada/Topicos_IA_Proyecto_Digitdeck/blob/6afab2140abcf712dea14339f5e98f8e448b6828/Entregables/M4/pipeline/ENTREGABLE.ipynb?plain=1#L1509); filas img_05, img_10 e img_11 de `salidas_m4.json`.
- **Qué se observa:**
  - `producto_identificado` solo exige `es_producto` y `tipo_producto`.
  - En img_10 (una playa), `ver()` devuelve `es_producto: true` con tipo «rocas»; la búsqueda trae fichas de la marca Roca y la respuesta es «Sí, lo tenemos».
  - Lo mismo ocurre en img_05 e img_11, siempre sin marca ni modelo.
  - Con sus modelos reales en otro hardware, las lecturas de img_10 e img_05 salen idénticas y el generador repite el «Sí, lo tenemos» con el mismo texto en img_10, img_05 e img_11.
  - En img_11 el VLM, además, escribe un texto visible «AirPods» que no se lee en la foto borrosa.
- **Ustedes ya lo identificaron** en el peor caso y propusieron la regla: «no buscar si el JSON no trae al menos marca o modelo».
- **Por qué importa:** ante una foto ambigua, el comprador recibe una afirmación sobre productos que no son el suyo.
- **Sugerencia:**
  - Implementar su regla: si no hay marca ni modelo, pedir el dato antes de buscar. C2 en CODE_PR es un ejemplo opt-in.
  - Proyectada sobre sus artefactos, sin volver a correr modelos, M4 pasaría de 5 a 2 afirmaciones falsas y de 1/4 a 3/4 adversariales, sin cambiar los positivos. Es post hoc, así que hay que medirla con fotos nuevas.
- **Criterio de cierre:** img_10, img_11 y al menos 3 fotos nuevas sin producto o ilegibles no reciben «Sí, lo tenemos»; img_07 sigue respondiendo con fichas citadas.

### M4-03 · Exacto, parecido y disponible
- **Dónde:** `correr_foto` (celda 41), que con foto usa siempre `verificar_existencia`; filas M4 img_03 y M4.1 img_06 de `salidas_m4.json`.
- **Qué se observa:**
  - En img_03 (AirPods), M4 responde «Sí, lo tenemos» con unos EarPods. Al reproducir el generador, afirma otra ficha (AirPods Pro). Su propio etiquetado marca ambas como «no es el producto».
  - En img_06 (Switch 2), M4.1 afirma unos mandos.
  - «¿Venden estufas como esta?» también se trata como existencia.
  - El aviso de catálogo histórico sí separa bien existencia en catálogo de disponibilidad.
- **Por qué importa:** un sustituto presentado como el producto exacto es la confusión que más dañaría la confianza de un comprador.
- **Sugerencia:** si la ficha principal no coincide con la marca y el modelo leídos, abrir con «No lo tenemos exacto, pero hay productos parecidos». Así pueden mantener el alcance de existencia que declararon.
- **Criterio de cierre:** img_03 e img_06 no abren con «Sí, lo tenemos» para un producto distinto.

### M4-04 · Hay dos `scorecard_m4.csv`
- **Dónde:** `Entregables/M4/scorecard_m4.csv` (el que escribe la celda 60, [L3037](https://github.com/AlejandroSPosada/Topicos_IA_Proyecto_Digitdeck/blob/6afab2140abcf712dea14339f5e98f8e448b6828/Entregables/M4/pipeline/ENTREGABLE.ipynb?plain=1#L3037)) y `Entregables/M4/Resultados/scorecard_m4.csv`.
- **Qué se observa:**
  - El segundo es de una corrida anterior: tiene 26 columnas en vez de 45, otras latencias y `nota_m4`/`nota_m4.1` distintas en img_01 e img_07.
  - El notebook actual ya no lo produce.
  - Solo el de la raíz reproduce `delta_m4.csv`.
- **Por qué importa:** quien abra `Resultados/` (por ejemplo, para preparar la demo) puede citar cifras que no son las del informe.
- **Sugerencia:** retirarlo o renombrarlo a `scorecard_m4_corrida_previa.csv` (C3 en CODE_PR; contenido intacto).
- **Criterio de cierre:** un único `scorecard_m4.csv` por versión.

### M4-05 · El aporte de la foto está en no afirmar de más, y conviene darle su intervalo
- **Dónde:** [`INFORME_M4.md` §6.2, L181–196](https://github.com/AlejandroSPosada/Topicos_IA_Proyecto_Digitdeck/blob/6afab2140abcf712dea14339f5e98f8e448b6828/Entregables/M4/INFORME_M4.md?plain=1#L181-L196); filas `tipo=positivo` de `scorecard_m4.csv`.
- **Qué se observa:**
  - Con D3, M4 acierta 1 de 6 positivos, igual que M3 con la pregunta sola. El +1 global viene de no afirmar en img_06 e img_08, y ustedes ya reconocen que img_06 acertó por accidente.
  - Lo que la foto sí mejora es bajar las afirmaciones falsas de 8 a 5 en 12 fotos.
  - Ustedes declaran que no calcularon intervalos para las filas con foto. Calculados desde su scorecard:
    - M4 menos M3 sola: +0,08, con IC 95 % pareado de −0,17 a +0,33;
    - M4.1: +0,33, con IC de 0,00 a +0,67.
  - En otro hardware, M4.1 descartó un iPhone nítido (img_02) como «no se aprecia en la imagen». Esto no ocurrió en su corrida, pero muestra que sus ganancias dependen de lecturas frágiles.
- **Por qué importa:** con 12 casos, «la foto mejora el acierto» no se sostiene; «la foto reduce las afirmaciones falsas en estos 12 casos» sí.
- **Sugerencia:** presentar el delta con denominadores y con su intervalo (C4 en CODE_PR lo calcula desde su CSV), y confirmar la versión elegida con 5–6 fotos nuevas.
- **Criterio de cierre:** la tabla de delta muestra n e IC para las filas con foto, y hay una tabla aparte con las fotos nuevas.

### M4-06 · El eval set tiene menos fotos distintas de lo que parece y sigue en «borrador»
- **Dónde:** [`eval_set/eval_set_m4.csv`](https://github.com/AlejandroSPosada/Topicos_IA_Proyecto_Digitdeck/blob/6afab2140abcf712dea14339f5e98f8e448b6828/Entregables/M4/eval_set/eval_set_m4.csv) (columna `estado`); [`INFORME_M4.md` L123](https://github.com/AlejandroSPosada/Topicos_IA_Proyecto_Digitdeck/blob/6afab2140abcf712dea14339f5e98f8e448b6828/Entregables/M4/INFORME_M4.md?plain=1#L123) y [§11, L342–345](https://github.com/AlejandroSPosada/Topicos_IA_Proyecto_Digitdeck/blob/6afab2140abcf712dea14339f5e98f8e448b6828/Entregables/M4/INFORME_M4.md?plain=1#L342-L345).
- **Qué se observa:**
  - img_12 es idéntica en píxeles a img_01, e img_11 es un desenfoque de img_03. Ambas están declaradas y son válidas como adversariales de atributo y de legibilidad, pero dejan 10 escenas distintas.
  - Las 12 filas tienen `estado = borrador`, aunque el informe dice que los criterios se fijaron antes de correr.
  - El etiquetado y los casos los propuso el asistente, sin una segunda persona que revisara ni medida de acuerdo (lo declaran).
- **Por qué importa:**
  - Cada caso pesa 8 puntos porcentuales.
  - Con escenas repetidas, una misma lectura cuenta dos veces.
  - Un estado «borrador» deja en duda qué criterio se usó al correr.
- **Sugerencia:**
  - Marcar `estado` como final en la versión con la que se corrió.
  - Al ampliar el set, añadir fotos de escenas nuevas (idealmente tomadas por ustedes) y que una segunda persona revise criterios y etiquetas.
  - C5 en CODE_PR detecta duplicados y revisa `estado`.
- **Criterio de cierre:** `estado` final en el CSV, y las fotos nuevas están en escenas distintas a las 10 actuales.

**Menores, sin acción obligatoria:**
- La celda 6 pide un token de GitHub con `getpass`, aunque el repositorio es público; esto añade fricción en Colab.
- La firma del índice Chroma sigue pendiente (lo declaran).
- La abstención en Rx (img_09) viene del umbral y no del enrutador (lo declaran).

## 4. Seguimiento de M3 (PR #1 y #2 del fork)

- **Incorporado, de otra forma:**
  - validación de la consulta y de la herramienta, separando `error_formato` de `error_operativo`, con cobertura y los errores fuera de las métricas de acierto (M3-01; [#2](https://github.com/manularrea/Topicos_IA_Proyecto_Digitdeck/pull/2)). No usaron `revision_tools.py`: lo reimplementaron en `correr_foto`;
  - auditoría de citas junto a D3 sin cambiar su definición (M3-02, celda 55);
  - consulta original conservada junto a la reformulación, y atributos de la foto separados de los de la ficha, sin inferir stock.
- **Decisión razonable:** la ruta sin foto conserva `sistema_D` tal cual, para garantizar las 49/49 idénticas.
- **Sigue abierto:** la firma del índice en lugar del conteo (lo declaran como pendiente).
- [#1](https://github.com/manularrea/Topicos_IA_Proyecto_Digitdeck/pull/1) y #2 pueden quedar como referencia histórica.

## 5. Prioridades para Demo Day

La Demo presenta el sistema completo como producto. Ya tienen un único punto de entrada, `sistema_multimodal(pregunta, foto)` ([celda 41, L1552](https://github.com/AlejandroSPosada/Topicos_IA_Proyecto_Digitdeck/blob/6afab2140abcf712dea14339f5e98f8e448b6828/Entregables/M4/pipeline/ENTREGABLE.ipynb?plain=1#L1552)). Esa función encadena:

- la lectura de la foto (M4);
- el enrutador, la búsqueda híbrida y la respuesta citada (M3);
- el reranker propio entrenado en ESCI (M1).

[`PLAN_DEMO.md`](PLAN_DEMO.md) propone tres prioridades sobre ese camino:

1. **[P0] Que el recorrido completo arranque donde vayan a desplegar** (M4-01). Al desplegar en M5 conviene además cargar los modelos una sola vez y preparar el índice fuera del arranque.
2. **[P1] La confianza como característica:** «si no estoy seguro, te pregunto» (M4-02, M4-03), con un panel «Lo que vi en la foto» junto a las fichas citadas.
3. **[P1] Una demo estable con números de valor** (M4-04, M4-05, M4-06):
   - tag de demo, un solo scorecard y casos ensayados con fotos nuevas;
   - plan B rotulado;
   - 1–3 números con su denominador.

`PLAN_DEMO.md` incluye además un guion sugerido y un backlog breve.

## 6. Cómo reproducir lo verificado

Desde la raíz del repositorio, con la rama de CODE_PR:

```bash
python review/m4/tests/verificar_scorecard.py        # recalcula delta_m4.csv desde scorecard_m4.csv (solo stdlib)
python review/m4/propuesta/ic_con_foto.py            # intervalos de las filas con foto (solo stdlib)
python review/m4/tests/verificar_eval_set.py         # duplicados en píxeles y columna estado (Pillow, numpy)
python -m unittest review/m4/tests/test_guardia_lectura.py review/m4/tests/test_ic_con_foto.py
python review/m4/tests/run_cell9.py Entregables/M4/pipeline/ENTREGABLE.ipynb <dir_parquets_esci>   # pandas, pyarrow
```

- **Celda 9:** los parquet son los de `amazon-science/esci-data` (`shopping_queries_dataset_{examples,products}.parquet`).
- **`ver()` y generador:** se reprodujeron leyendo las celdas 7, 9, 22, 23, 30, 40 y 43 del notebook y ejecutándolas sin cambios. Solo se cambió el dispositivo (cuda → mps).
  - `ver()` corrió con Qwen2-VL-2B sobre las 12 fotos de `eval_set/imagenes/`.
  - El enrutador y el generador corrieron con Qwen2.5-1.5B, usando las `pregunta_aumentada` y las fichas registradas en `salidas_m4.json`.
- **No se re-ejecutaron:** Chroma ni el reranker.
