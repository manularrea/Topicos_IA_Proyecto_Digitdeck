# Plan sugerido para Demo Day — Digitdeck

Orientación docente, no formato oficial. Ustedes deciden qué adoptar y quién lo asume.

## Punto de partida: lo que ya tienen conectado

El recorrido completo ya existe en una sola función: `sistema_multimodal(pregunta, foto)` (celda 41 de `Entregables/M4/pipeline/ENTREGABLE.ipynb`).

- **Con foto:** `ver()` lee la foto (Qwen2-VL-2B) y construye la consulta. Después, el enrutador de M3 decide si buscar o abstenerse, y la búsqueda híbrida de M3 (Chroma + BM25) devuelve candidatas. El reranker de M1 (publicado en el Hub) las ordena y aplica el umbral de exacto. Al final, el generador de M3 responde con fichas citadas, más un aviso de qué se vio y de que el catálogo es histórico.
- **Sin foto:** es el sistema D de M3 tal cual, con 49/49 respuestas idénticas.
- **Contrato de estados:** errores de formato, sin producto, abstención y sin resultados quedan separados de las respuestas.

En la revisión se re-ejecutó `ver()` y el generador con los modelos reales en otro hardware, y el comportamiento coincidió con sus trazas. Esa función es la base natural del despliegue de M5: al desplegar, basta con envolverla en una interfaz.

## P0 — Que el recorrido completo arranque en el entorno de despliegue

- **Prioridad:** P0
- **Qué podría ocurrir durante la demo:** en el entorno donde desplieguen, que normalmente es Linux, el arranque se detiene en el control del split de test y la app nunca llega a `sistema_multimodal`.
- **Evidencia exacta:** celda 9 de `ENTREGABLE.ipynb` @ `6afab21`. Con los parquet públicos de ESCI y el código tal cual, fuera de Windows el hash da `331ee032…` en vez de `4d31950e…` y salta el `AssertionError`. Con `to_csv(..., lineterminator="\r\n")` coincide con M1.
- **Cambio mínimo recomendado:** esa línea (propuesta C1 de esta revisión) y una corrida de punta a punta en el mismo entorno donde vivirá la app. Al desplegar conviene además cargar los modelos una sola vez y separar la preparación del índice del arranque del servicio.
- **Qué NO hace falta rehacer:** el split, el hash de M1, el catálogo ni las cifras de M4.
- **Cómo verificar el cierre:** en el entorno de despliegue la celda (o el arranque de la app) imprime `coincide con M1: True` y una foto ensayada recorre todo el sistema hasta la respuesta.
- **Quién lo asume:** lo decide el equipo.

## P1 — Mostrar la confianza como característica: «si no estoy seguro, te pregunto»

- **Prioridad:** P1
- **Qué podría ocurrir durante la demo:** alguien del público muestra una foto ambigua (un paisaje, algo borroso) y el sistema contesta «Sí, lo tenemos» con productos ajenos. Esto se reproduce hoy con generación real.
- **Evidencia exacta:**
  - img_10, la playa, recibe fichas de asientos Roca; img_11, borrosa, y img_05 también afirman. Las tres lecturas tienen marca y modelo vacíos.
  - img_03 presenta un sustituto (EarPods o AirPods Pro, ambos marcados por ustedes como «no es el producto») como si fuera el exacto.
  - Fuentes: `Resultados/salidas_m4.json` y su `scorecard_m4.csv`, confirmados en la revisión re-ejecutando el VLM y el generador.
- **Cambio mínimo recomendado:** la regla que ustedes mismos proponen en el peor caso. Si la foto no da marca ni modelo, pedir el dato antes de buscar; hay un ejemplo opt-in en la propuesta C2. Y cuando la ficha no coincide con lo leído, abrir con «No lo tenemos exacto, pero hay productos parecidos». En la interfaz, mostrar un panel «Lo que vi en la foto» junto a las fichas citadas: hace visible el guardrail.
- **Qué NO hace falta rehacer:** el VLM, el reranker, el enrutador ni el eval set.
- **Cómo verificar el cierre:** con img_10, img_11 y al menos tres fotos nuevas sin producto o ilegibles, el sistema pide aclaración o se abstiene. Con img_07 y una foto nueva nítida sigue respondiendo con fichas citadas.
- **Quién lo asume:** lo decide el equipo.

## P1 — Una demo estable y con números que la respalden

- **Prioridad:** P1
- **Qué podría ocurrir durante la demo:** una lectura cambia entre hardware y el caso estrella falla en vivo; o se cita un número que no corresponde a la versión mostrada.
- **Evidencia exacta:**
  - En otro hardware, la variante M4.1 en bf16 descartó un iPhone nítido (img_02) como «no se aprecia en la imagen»; no ocurrió en fp16 ni en su corrida.
  - Hay dos `scorecard_m4.csv` con valores distintos (la raíz de M4 y `Resultados/`).
  - En positivos, M3 sola y M4 aciertan 1/6 cada uno; el valor medido de la foto está en no afirmar de más: de 8 a 5 afirmaciones falsas en 12 fotos.
- **Cambio mínimo recomendado:**
  - Congelar una versión con tag y dejar un único scorecard.
  - Ensayar en el hardware de la demo un set fijo: un éxito con foto (img_07 u otra foto nueva que funcione allí), el guardrail (img_10), la abstención por Rx (img_09) y una pregunta sin foto.
  - Preparar un plan B rotulado como «salida grabada».
  - Elegir 1–3 números con su denominador: afirmaciones falsas en 12 fotos frente a la pregunta sola; 49/49 sin regresiones sin foto; segundos por consulta con foto en el hardware de la demo.
  - Al desplegar, el health check, los logs y W&B (ya lo usaron en M1) pueden presentarse como «así lo operamos».
- **Qué NO hace falta rehacer:** el harness, la vara D3 ni la tabla de delta.
- **Cómo verificar el cierre:** el set ensayado corre tres veces seguidas igual en el entorno de la demo, y cada número dicho en voz alta está en un único archivo con su denominador.
- **Quién lo asume:** lo decide el equipo.

## Backlog breve (después de la demo)

- Token de GitHub opcional en Colab (el repo es público).
- Firma del índice Chroma (ya declarado).
- Atender «¿venden algo como esto?» con búsqueda de parecidos.
- VLM más grande si el presupuesto lo permite.

## Guion sugerido (bloques, sin minutos obligatorios)

1. **La persona y su problema:** un comprador tiene el producto en la mano —el mando de su consola, un dron— y no sabe cómo se llama ni cómo buscarlo. La tienda pierde la venta porque la búsqueda por texto falla.
2. **Momento wow, en vivo:** sube la foto y pregunta «¿lo tienen?». En segundos la interfaz muestra qué vio el sistema, las fichas del catálogo con su identificador y la respuesta. Todo es trazable.
3. **Cómo funciona, en una frase por pieza:** ve (M4) → entiende y decide (enrutador M3) → busca (híbrida M3) → ordena con el modelo propio entrenado en ESCI (M1) → responde citando las fichas (M3).
4. **Confianza como producto:** una foto ambigua → «No veo marca ni modelo, ¿me lo confirmas?». Un medicamento con receta → abstención. Eso es lo que hace al sistema seguro para la tienda.
5. **Prueba de valor:** 1–3 números con su denominador, y la latencia.
6. **Así lo operamos:** URL, health check, W&B, versión con tag.
7. **Límites honestos y siguiente paso:**
   - Límites: catálogo histórico sin stock; VLM de 2B; 12 fotos de evaluación.
   - Siguiente paso: búsqueda de parecidos y más fotos reales de usuarios.
