# INFORME M4 — Digitdeck: el sistema ve

**SI4006 - Universidad EAFIT - 2026-2** — Maximiliano Bustamante, Valeria Frances Hornung, Sebastián Castaño, Alejandro Posada

---

## 1. Resumen ejecutivo

**Digitdeck M4** le agrega un componente visual al sistema de M3. El comprador manda una foto con su pregunta (*"¿Tienen este celular?"*), un VLM traduce la foto a un JSON con lo que se ve, y con esos campos el sistema de M3 busca en el catálogo y responde. Sin foto, el sistema es el de M3 sin cambios.

**Resultado:** con la vara oficial (la D3 de M3, sin cambios), M4 acierta **4 de 12** casos con foto, contra **3 de 12** de M3 con la pregunta sola y **8 de 10** del techo (M3 con la pregunta que escribiría quien sabe qué es el producto). Las afirmaciones falsas bajan de **8 a 5**. Los 49 casos de M3 sin foto quedan **idénticos** (17/49, 49/49 respuestas iguales). Ver cuesta **+1,44 s por caso** (3,77 s contra 2,33 s). Una variante diseñada después de ver la primera corrida (**M4.1**, post hoc) llega a 7 de 12, con 2 afirmaciones falsas y 4 de 4 adversariales, pero su mejora es optimista porque se ajustó mirando estos mismos 12 casos.

---

## 2. La pregunta, el patrón y el modelo

### 2.1 La pregunta que necesita ojos

Hasta M3, el comprador tenía que escribir el nombre del producto. Si tiene el producto en la mano y no sabe cómo se llama, M3 no puede ayudarle: con la pregunta sola (*"¿Tienen este celular?"*), M3 ofreció un teléfono Alcatel para la foto de un iPhone, una bebida isotónica para la de una Pony Malta y harina de maíz para la de una playa. Esa es la pregunta de nuestro usuario que no se puede responder sin ver.

### 2.2 Por qué visión como INPUT

| Patrón | ¿Sirve para "¿lo tienen?"? | Decisión |
|---|---|---|
| **Visión como input** (un VLM convierte la foto en texto antes del RAG) | Sí: la foto se vuelve una consulta y entra por la puerta que M3 ya sabe usar. El RAG, las herramientas y el harness de M3 siguen igual | **Elegido** |
| Visión como tool con CLIP | No con nuestros datos. Clasificar contra clases cerradas no dice si el producto está en el catálogo, y comparar la foto con las fotos del catálogo es imposible: el catálogo de ESCI no tiene imágenes, y SQID (la extensión de ESCI con imágenes, arXiv 2405.15190) solo cubre el locale `us` | Descartado |
| Visión como output (difusión) | No. Generar la foto de un producto es el mal uso que señala S12 (lámina 29): "la foto de un producto con detalles que el producto real no tiene" | Descartado |

### 2.3 Por qué Qwen2-VL-2B-Instruct

- Es el VLM del lab de S11 y del esqueleto de S13. S11 lo eligió porque cabe en la T4 de Colab; junto con el resto del sistema cabe en una GPU de 16 GB.
- Sigue una instrucción de salida JSON como la del lab B3 de S11: en la corrida final, los 12 JSON fueron válidos.
- No se probó un VLM más grande. Es la primera palanca si `ver()` resulta ser el cuello de botella.

### 2.4 Alcance: solo existencia

M4 responde "¿lo tienen?" con `verificar_existencia`. "¿Qué hay parecido?" queda fuera: en M3, `buscar_similares` acertó 1 de 21 preguntas, y agregarle una foto no arregla eso.

---

## 3. Arquitectura: dónde se enchufó

### 3.1 El recorrido de una pregunta con foto

| Paso | Qué hace | Por qué así |
|---|---|---|
| 1. `ver(foto)` | Qwen2-VL-2B con la válvula de S11 como instrucción de sistema y una instrucción de dominio que pide un JSON con `es_producto`, `tipo_producto`, `marca`, `modelo`, `color` y `texto_visible`. Resolución acotada (`min_pixels` 256·28·28, `max_pixels` 1024·28·28) y salida greedy | Las tres reglas de S13: válvula, salida estructurada y validada, y describir antes de preguntar |
| 2. Validación | Parser de S10/S11. Si no hay JSON válido, es un **error de formato** | Un error no es una abstención |
| 3. Válvula | Si `es_producto` es falso o no hay tipo de producto, el sistema se abstiene: "No tengo esa información en mis fuentes. No se aprecia en la imagen un producto que pueda buscar." | Lo que no se ve no se busca |
| 4. Consulta | Tipo + marca + modelo + color del JSON, con la normalización de M1 | En M3 la reescritura del enrutador dañó consultas ("merienda" por "Mérida"); aquí la consulta sale de la foto, de forma determinista |
| 5. Enrutador de M3 | Recibe la pregunta con lo que se ve ("¿Me venden esto? (En la foto se ve: ...)") y decide si se busca o no | Que un producto con receta, por ejemplo, no se busque. Solo decide; no escribe la consulta |
| 6. `verificar_existencia` | La herramienta de M3: búsqueda híbrida BM25 + densa (RRF, k = 60), reranker de M1 sobre 30 candidatos y umbral de exacto 0,5993 | Sin cambios respecto a M3 |
| 7. Generador | Qwen2.5-1.5B-Instruct con el prompt y las tres aperturas de M3 ("Sí, lo tenemos", "No lo tenemos exacto, pero hay productos parecidos", "No tengo esa información en mis fuentes") | Sin cambios respecto a M3 |
| 8. Presentación | Al final de la respuesta: "En la foto se ve: ... Las fichas son del catálogo histórico de Amazon España (ESCI), no del inventario actual de la tienda." | Orientación de la revisión de M3: foto y ficha por separado, sin inferir stock |

Sin foto, `sistema_multimodal(pregunta)` llama a `sistema_D` de M3 tal cual.

### 3.2 Las celdas de M3, copiadas

El sistema de M3 no se reescribe: sus celdas están copiadas en el notebook de M4 sin cambios de lógica. Lo único distinto son las rutas, que el reranker de M1 puede venir del Hub, y que el eval set de M3 y los umbrales se leen de `M3/Resultados/` en vez de recalcularse.

### 3.3 Dos fases para caber en la GPU

- **Fase A (solo texto):** con el verificador de M3 (Qwen2.5-3B) cargado, se corren los 49 casos de M3 sin foto y las dos líneas base.
- **Fase B (con foto):** se libera el verificador y se carga el VLM. `buscar_similares`, que es la única que usa el verificador, no se llama con foto.

### 3.4 Contrato de salida

| Estado | Qué significa | ¿Se califica? |
|---|---|---|
| `respuesta_generada` | Hubo fichas sobre el umbral y el generador respondió | Sí |
| `sin_resultados` | Ninguna ficha pasó el umbral de exacto: abstención | Sí |
| `abstencion_dominio` | El enrutador respondió NINGUNA, sin texto adicional | Sí |
| `sin_producto` | La válvula de `ver()`: no hay producto identificable | Sí |
| `error_formato` | JSON de `ver()` inválido, enrutador sin herramienta válida ni NINGUNA, consulta vacía, observación mal formada o generador sin texto | No: fuera de la nota, contado en la cobertura |
| `error_operativo` | Una excepción en cualquier etapa | No: fuera de la nota, contado en la cobertura |

En la corrida de referencia no hubo errores: cobertura 12 de 12 en M4 y en M4.1.

---

## 4. El eval set con imagen

### 4.1 Los 12 casos

Cada caso tiene **un criterio declarado antes de correr** en [`eval_set/eval_set_m4.csv`](eval_set/eval_set_m4.csv), junto con lo que cuenta como el producto, los campos que debería leer el VLM (*gold*) y la pregunta del techo.

| Caso | Foto | Pregunta | Tipo | Criterio |
|---|---|---|---|---|
| img_01 | iPhone 11 Pro Max oro | ¿Tienen este celular? | positivo | `acierto_respuesta` |
| img_02 | iPhone 11 Pro Max gris espacial | ¿Tienen este celular? | positivo | `segun_catalogo` |
| img_03 | AirPods con estuche | ¿Venden estos audífonos? | positivo | `acierto_respuesta` |
| img_04 | Dron DJI Air 2S | ¿Tienen este dron? | positivo | `acierto_respuesta` |
| img_05 | Estufa de gas de exterior (tipo seta) | ¿Venden estufas como esta? | positivo | `acierto_respuesta` |
| img_06 | Nintendo Switch 2 | ¿Tienen esta consola? | no existe | `no_afirma` |
| img_07 | Nintendo Switch original | ¿Tienen esta consola? | positivo | `acierto_respuesta` |
| img_08 | Pony Malta | ¿Venden esta bebida? | no existe | `no_afirma` |
| img_09 | Augmentin 875 mg (antibiótico con receta) | ¿Me venden esto? | adversarial | `valvula` |
| img_10 | Una playa, sin producto | ¿Tienen este producto? | adversarial | `valvula` |
| img_11 | Los AirPods de img_03, desenfocados | ¿Tienen este producto? | adversarial | `no_afirma` |
| img_12 | La foto de img_01 | ¿Lo tienen de 512 GB? | adversarial | `segun_catalogo` |

| Criterio | Nota 1 si... |
|---|---|
| `acierto_respuesta` | D3 de M3: el sistema afirma y al menos 2 de las 3 primeras fichas de la pantalla son el producto (todas, si el catálogo tiene menos de 2) |
| `no_afirma` | el sistema no dice "Sí, lo tenemos" |
| `valvula` | el sistema se abstiene |
| `segun_catalogo` | si el etiquetado encuentra el producto, se califica como `acierto_respuesta`; si no, como `no_afirma` |

**Por qué estos casos:**

- **Espejos de M3:** img_03, img_04 e img_05 son productos que ya estaban en el eval set de M3 (g09-E, n12-E y n01-E), para comparar la misma necesidad con y sin foto.
- **Dos productos que no están en el catálogo:** la Switch 2 (img_06) y la Pony Malta (img_08). Miden si el sistema afirma lo que no tiene. La Pony Malta es además el caso de sesgo de contexto: un producto latinoamericano en un catálogo de Amazon España.
- **Cuatro adversariales:** un producto que no se debe vender sin receta (img_09), una foto sin producto (img_10), una foto en la que no se puede confirmar marca ni modelo (img_11) y un atributo que la foto no muestra (img_12, la capacidad).
- `segun_catalogo` existe porque no sabíamos de antemano si el catálogo tenía el producto exacto (img_02) o la variante pedida (img_12). Lo decide el etiquetado; en img_12 resultó que no hay iPhone 11 Pro ni Pro Max oro de 512 GB, y el caso se califica como `no_afirma`.

### 4.2 Las fotos: procedencia y anonimización

| Fuente | Fotos | Licencia |
|---|---|---|
| Wikimedia Commons | img_02 a img_10 | CC BY-SA 4.0, CC BY 2.0, CC BY-SA 3.0, CC BY-SA 3.0 AU, CC0 y dominio público, según la foto |
| Unsplash (Daniel Romero) | img_01 | Unsplash License |
| Derivadas | img_11 (desenfoque gaussiano de img_03, radio 16) e img_12 (copia de img_01) | las de su original |

- Autor, licencia, URL y transformación de cada foto en [`eval_set/fuentes_imagenes.csv`](eval_set/fuentes_imagenes.csv). [`eval_set/descargar_imagenes.py`](eval_set/descargar_imagenes.py) las vuelve a bajar desde su fuente.
- **Sin caras ni documentos personales.** La única parte de una persona es una mano sosteniendo el iPhone (img_01). La caja de Augmentin no tiene datos de paciente.
- **Sin metadatos EXIF:** todas se re-guardaron como JPG con PIL, que no copia los metadatos de cámara ni de ubicación.
- Las fotos con licencia CC BY-SA se redistribuyen con la misma licencia.

### 4.3 El etiquetado del catálogo

ESCI no tiene etiquetas para estas fotos. Para calificar con D3 hay que saber qué fichas del catálogo son el producto de cada foto. Se armó [`Validacion/etiquetado_catalogo_m4.xlsx`](Validacion/etiquetado_catalogo_m4.xlsx) con **425 fichas candidatas** para los 9 casos que dependen del catálogo:

- los relevantes del caso espejo de M3,
- los títulos que coinciden con una búsqueda por palabras clave (276),
- lo que devuelven la búsqueda híbrida y el reranker con la pregunta del techo (79),
- y toda ficha que algún sistema mostró en su primera pantalla (el notebook las agrega solo).

### 4.4 Las líneas base

- **M3 con la pregunta sola:** lo que hace M3 cuando el comprador manda "¿Tienen este celular?" sin poder mostrar la foto. Es la línea base honesta.
- **Techo:** M3 con la pregunta que escribiría alguien que sabe qué es el producto ("¿Tienen el iPhone 11 Pro Max en color oro?"). La distancia entre M4 y el techo es lo que pierde `ver()`. img_10 e img_11 no tienen techo: no hay producto que nombrar.

---

## 5. El harness

**La misma función de M3 califica los casos nuevos.** La rúbrica lo pide ("la misma función de M2 califica los casos nuevos") y la revisión de M3 pide complementar D3 sin alterar su definición. Por eso la nota oficial de `acierto_respuesta` es `dimension_3` de M3, sin cambios.

Al lado se reportan dos **complementos**, que solo cambian `acierto_respuesta`:

- **Regla del CSV:** lo escrito en la columna `esperado` ("afirma y muestra un iPhone 11 Pro o Pro Max oro"): basta una ficha correcta entre las 3 primeras.
- **Primera cita:** la primera ficha citada en el texto es el producto. Atrapa respuestas que aprueban por la pantalla pero cuyo texto nombra primero otra cosa.

Y como diagnóstico, sin entrar a la nota:

- **Campos:** qué parte de la identidad del producto (tipo, marca, modelo, color) recuperó `ver()` frente al *gold*. En las fotos sin producto, 1 si `ver()` no inventó uno. Separa "leyó mal la foto" de "buscó mal".
- **nDCG@10** contra las fichas etiquetadas (la D1 de M3).
- **Afirmación falsa:** dijo "Sí, lo tenemos" sin mostrar el producto en las 3 primeras fichas.
- **Auditoría sintáctica de citas** (revisión de M3, M3-02): citas emitidas, citas que están en el contexto, citas desconocidas, respuestas que muestran fichas sin citar ninguna y abstenciones con un texto distinto al del contrato. No certifica que la respuesta sea correcta.
- **Cobertura:** cuántas salidas son válidas.

---

## 6. Resultados

Todos los números son de la corrida local de referencia: notebook desde cero, kernel reiniciado, RTX 5060 Ti 16 GB, Python 3.11.9, torch 2.11.0+cu128, transformers 4.57.1. Generación greedy.

### 6.1 Sin foto: ¿empeoró lo viejo?

| | M3 | M4 sin foto |
|---|---|---|
| Aciertos de respuesta (D3) | 17/49 | 17/49 |
| nDCG@10 existencia (ESCI) | 0,453 | 0,453 |
| Afirmaciones falsas | 6 | 6 |
| Respuestas idénticas a M3 | | 49/49 (y 49/49 primeras pantallas) |
| Latencia media | 2,08 s | 2,20 s |

No empeoró: sin foto el sistema es el mismo. Los números de M3 coinciden con el `scorecard_m3.csv` que se entregó.

### 6.2 Con foto: la tabla de delta

| Grupo | M3 pregunta sola | M4 | M4.1 (post hoc) | Techo |
|---|---|---|---|---|
| Aciertos, D3 (oficial) | 3/12 | **4/12** | 7/12 | 8/10 |
| Aciertos, regla del CSV | 3/12 | 5/12 | 9/12 | 10/10 |
| Aciertos, primera cita | 3/12 | 5/12 | 8/12 | 10/10 |
| Deberían responderse (8), D3 | 1/8 | 3/8 | 3/8 | 6/8 |
| Adversariales (4) | 2/4 | 1/4 | 4/4 | |
| Afirmaciones falsas | 8 | 5 | 2 | 0 |
| Campos recuperados por `ver()` | no ve | 0,72 | 0,71 | |
| Cobertura (salidas válidas) | 12/12 | 12/12 | 12/12 | 10/10 |
| Latencia media | 2,33 s | 3,77 s | 4,59 s | |
| Latencia p95 | 5,15 s | 5,95 s | 6,48 s | |

Con 12 casos, cada caso son 8 puntos porcentuales. No se calcularon intervalos de confianza para las filas con foto.

### 6.3 Caso por caso (D3; F = afirmación falsa)

| Caso | M3 sola | Techo | M4 | M4.1 | Qué pasó |
|---|---|---|---|---|---|
| img_01 iPhone oro | 0 F | 0 | 0 | 0 | M4 muestra el 11 Pro Max oro de 256 GB, que es correcto, pero D3 pide 2 de las 3 primeras; la regla del CSV y la primera cita lo aprueban. M4.1 muestra el 11 Pro Max en todos los colores y cita primero uno verde noche |
| img_02 iPhone gris espacial | 0 F | 1 | 0 | 0 F | El VLM leyó "negro". M4 ofrece un iPhone 11 negro como parecido; M4.1, sin color en la consulta, afirma el 11 Pro Max de todos los colores y el gris espacial queda 5.º |
| img_03 AirPods | 0 | 1 | 0 F | 1 | M4 buscó "auriculares inalámbricos apple airpods blanco" y afirmó unos EarPods (con cable). M4.1 buscó "apple airpods" y encontró los AirPods de 2.ª generación |
| img_04 DJI Air 2S | 0 F | 1 | 0 | 1 | El VLM leyó todo bien, pero con "gris" en la consulta ninguna ficha pasó el umbral. M4.1, sin el color, encuentra los dos Air 2S |
| img_05 estufa de gas | 0 F | 0 | 0 F | 0 | El VLM no ve que es de gas: M4 afirma un calefactor eléctrico; M4.1 lee "termómetro de exterior" y ofrece termómetros como parecidos |
| img_06 Switch 2 | 0 F | 1 | 1 | 0 F | M4 leyó "controlador de videojuegos" y ofreció un mando como parecido: acertó por accidente. M4.1 afirma mandos Pro Controller |
| img_07 Switch original | 1 | 1 | 1 | 0 | M4 muestra tres Switch originales. M4.1 muestra primero la correcta, pero después una OLED y una Lite (D3 pide 2 de 3) |
| img_08 Pony Malta | 0 F | 1 | 1 | 1 | El VLM leyó la marca; ninguna ficha pasó el umbral. M3 con la pregunta sola afirmaba una bebida isotónica |
| img_09 Augmentin | 1 | 1 | 1 | 1 | Acierto, pero no por la razón correcta: el enrutador no se negó, buscó, y la abstención vino del umbral |
| img_10 playa | 0 F | | 0 F | 1 | M4: "rocas", y el sistema ofreció productos de la marca Roca. M4.1: el VLM sigue viendo un producto ("pequeños objetos dispersos por el suelo"); se abstuvo porque el enrutador respondió NINGUNA |
| img_11 AirPods borrosos | 0 F | | 0 F | 1 | M4 afirmó unos auriculares cualquiera. En M4.1 el VLM respondió "no se aprecia" y actuó la válvula |
| img_12 ¿de 512 GB? | 1 | 1 | 0 F | 1 | M4 ignoró "512 GB" (la consulta sale solo de la foto) y afirmó el de 256 GB. M4.1 suma "512 gb" a la consulta y se abstiene: en el catálogo no hay oro de 512 GB |

### 6.4 Lo que leyó `ver()`

| | img_01 | img_02 | img_03 | img_04 | img_05 | img_06 | img_07 | img_08 | img_09 | img_10 | img_11 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Campos M4 | 1,00 | 0,75 | 1,00 | 1,00 | 0,50 | 0,75 | 0,75 | 1,00 | 0,33 | 0,00 | 0,50 |
| Campos M4.1 | 1,00 | 0,75 | 1,00 | 1,00 | 0,50 | 0,50 | 0,75 | 1,00 | 1,00 | 0,00 | 0,00 |

- **Lee bien** marca y modelo cuando están escritos o son icónicos: Apple iPhone 11 Pro Max, DJI Air 2S, Pony Malta, Augmentin, Nintendo Switch.
- **Falla en:** colores (gris espacial leído como negro), el tipo de producto (la consola leída como "controlador" o "videojuego"; la estufa como "calentador" o "termómetro"), generaciones de un mismo producto (Switch 2 contra Switch) y fotos sin producto (la playa).
- **Inventa texto:** en img_06 devolvió `texto_visible: "Nintendo Switch"`, y la foto no tiene ningún texto.

### 6.5 ¿Cuánto cuesta ver?

| Etapa (media por caso con foto) | M3 pregunta sola | M4 |
|---|---|---|
| `ver()` | | 1,72 s |
| Enrutamiento | 0,63 s | 0,68 s |
| Recuperación + reranking | 0,06 s | 0,11 s |
| Generación (cuando hubo fichas) | 2,21 s | 1,68 s |
| **Total** | **2,33 s** | **3,77 s** |

Ver cuesta **+1,44 s por caso** (+62 %), casi todo en el VLM. M4.1 cuesta 4,59 s porque `ver()` hace dos llamadas (3,05 s).

### 6.6 ¿Vale la pena describir antes de preguntar?

Se midió solo `ver()`, en las 11 fotos distintas:

| | Una llamada (M4) | Dos llamadas (M4.1) |
|---|---|---|
| Campos recuperados (media) | 0,689 | 0,682 |
| Segundos de `ver()` | 1,71 s | 3,03 s |

**No vale:** no mejora la lectura de la foto y cuesta 1,3 s más. Mejora img_09 (lee la dosis) y empeora img_06 e img_11. La mejora de M4.1 no viene de describir primero sino de cómo arma la consulta.

### 6.7 Auditoría de citas

| | M3 (sin foto) | M4 (sin foto) | M3 sola | M4 | M4.1 | Techo |
|---|---|---|---|---|---|---|
| Citas desconocidas | 0 | 0 | 0 | 0 | 0 | 0 |
| Respuestas con fichas y sin ninguna cita | 2 | 2 | 0 | 0 | 0 | 0 |
| Abstenciones fuera del contrato | 0 | 0 | 0 | 0 | 0 | 0 |

Las dos respuestas sin cita son de M3 (n04-S y n10-S, ambas de "parecidos"): el generador escribió el nombre del producto entre corchetes en lugar de su identificador. Con foto, todas las respuestas citan fichas del contexto.

---

## 7. El peor caso

### M4: img_10, una playa sin producto

- **Qué pasó:** `ver()` respondió `{"es_producto": true, "tipo_producto": "rocas"}`. La consulta fue "rocas", la búsqueda devolvió fichas de la marca Roca por encima del umbral y el generador respondió "Sí, lo tenemos" con un kit de bisagras y asientos de inodoro.
- **Por qué:** **leyó mal la foto** (la válvula escrita en el prompt no bastó: el VLM convirtió el paisaje en un producto) y **buscó con una sola palabra genérica**, que coincidió con una marca. Campos: 0.
- **Qué haríamos:** no buscar si el JSON no trae al menos marca o modelo, o si el tipo de producto es una sola palabra genérica; y medir la válvula con más fotos sin producto. M4.1 se abstuvo en este caso, pero por el enrutador, no porque el VLM viera que no había producto.

### M4.1: img_06, la Nintendo Switch 2

- **Qué pasó:** el VLM leyó "control de videojuegos Nintendo Switch", la consulta fue esa y el sistema afirmó tener mandos Pro Controller. Es una **afirmación falsa**: la Switch 2 no está en el catálogo.
- **Por qué:** **leyó mal la foto.** La consola se ve de frente, sin texto, y el VLM no distingue generaciones ni separa la consola de sus controles. En M4 el mismo caso salió bien por accidente: leyó "controlador de videojuegos" y el generador ofreció un mando solo como parecido.
- **Qué haríamos:** cuando el modelo no se lee en la foto, preguntarle al comprador cuál es antes de afirmar, y no tratar `texto_visible` como evidencia sin verificarlo.
- La regla automática del notebook señala img_05 (la estufa leída como termómetro). Ahí el sistema se equivocó de producto pero solo ofreció parecidos; img_06 es el fallo más grave porque dice "Sí, lo tenemos".

---

## 8. Lectura honesta

**¿Mejoró lo nuevo?** Poco con la vara oficial: M4 acierta 4 de 12 contra 3 de 12 de M3 con la pregunta sola, y el techo está en 8 de 10. Lo que más cambia es la calidad de los errores: con la pregunta sola, M3 afirma productos al azar (8 afirmaciones falsas); M4 baja a 5. En los adversariales M4 empeora (1 de 4 contra 2 de 4): afirma en la playa, en los AirPods borrosos y en el iPhone de 512 GB, donde M3 con la pregunta sola se abstenía.

**¿No empeoró lo viejo?** No: los 49 casos de M3 salen idénticos.

**¿Cuánto cuesta ver?** 1,44 s por caso con foto, casi todo en el VLM.

**¿Dónde se pierde?** Entre M4 y el techo hay 4 casos. Los fallos se reparten así:

| Tipo de fallo | Casos | Qué lo causa |
|---|---|---|
| **Leyó mal la foto** | img_02 (color), img_05 (tipo), img_10 (vio un producto donde no hay), e img_06 (consola leída como control; acertó por accidente) | Un VLM de 2B no distingue colores cercanos, generaciones ni la ausencia de producto, e inventa texto |
| **Buscó mal o afirmó con una lectura incompleta** | img_03 (el tipo genérico llevó a EarPods), img_04 (el color bajó el puntaje bajo el umbral), img_11 (sin marca ni modelo buscó "auriculares inalámbricos" y afirmó cualquiera), img_12 (la capacidad no está en la foto) | La consulta mezcla atributos que el catálogo escribe distinto, le falta lo que solo está en la pregunta, o se busca aunque la lectura no identifique el producto |
| **Mostró bien, pero la vara pide más** | img_01 (D3 pide 2 de las 3 primeras y M4 mostró una sola ficha correcta) | La definición de D3; los complementos lo aprueban |

**M4.1 ataca la segunda fila,** y por eso mejora: consulta con marca + modelo sin color, y con los atributos que solo están en la pregunta (img_03, img_04, img_12); en img_11 su VLM respondió "no se aprecia". Pero al quitar el color y el tipo empeora img_02 e img_07, pierde el acierto accidental de img_06, y la primera fila sigue igual. Con D3, M4.1 no responde mejor que M4 (3 de 8 los dos); toda su ventaja está en los adversariales.

**Lo que haríamos con un mes más:** (1) probar un VLM más grande o "VLM + herramienta" (S11 dice que un VLM pequeño no lee bien números ni detalles finos); (2) que el comprador confirme lo que se vio antes de afirmar, cuando la lectura no trae modelo; (3) confirmar M4.1 con fotos nuevas, que no se hayan mirado al diseñarla; (4) un juez VLM de faithfulness visual (S13) para medir si lo que dice el sistema se sostiene en la foto.

---

## 9. Cambios hechos después de ver resultados

Todo lo de esta sección se decidió **después de ver resultados sobre el mismo eval set**, y por eso se declara.

### 9.1 M4.1, la variante post hoc

M4 es la corrida declarada antes de mirar resultados. La primera corrida mostró fallos que no estaban en `ver()` sino en cómo su salida se vuelve consulta. M4.1 cambia tres cosas, cada una atada a un fallo observado:

| Cambio | Fallo que lo motivó |
|---|---|
| Describir antes del JSON (dos llamadas) | img_10: la válvula falló con una llamada |
| Consulta = marca + modelo; si no hay modelo, tipo + marca. Sin color | img_04: la palabra "gris" bastó para que ninguna ficha pasara el umbral; img_03: "auriculares inalámbricos ... blanco" llevó a unos EarPods |
| Los números con unidad ("512 GB") y los "sin ..." de la pregunta se suman a la consulta | img_12: la capacidad no se ve en la foto |

El color y todo lo visto siguen llegando al generador en la pregunta aumentada. M4.1 usa el mismo enchufe y el mismo contrato de salida que M4. **Su mejora es optimista:** habría que confirmarla con fotos nuevas.

### 9.2 Fallas corregidas en el camino

| Qué falló | Por qué | Qué se cambió |
|---|---|---|
| En la primera versión de M4.1, el paso de "describir" no describía: 10 de 12 respuestas fueron solo `{"es_producto": ...}` | Se le pasó la válvula de `ver()`, que menciona JSON | Válvula de S11 sin JSON para ese paso, y un conteo de descripciones que salen como JSON (0 de 12 en la corrida final) |
| Un JSON inválido de `ver()` habría contado como abstención correcta | Se trataba igual que "no hay producto" | Contrato de salida (§4.4) |
| La regla oficial cambió de D3 a la del CSV y volvió a D3 | §6 | D3 oficial, con los dos complementos |
| El hash del split de test de M1 no coincidía en Colab | Fin de línea de `to_csv` distinto en Windows y Linux (§7.8) | Hash con `\r\n` explícito |

---

## 10. Límites y ética

- **Ver no es decidir.** El VLM describe; quien decide si es el producto es el catálogo y, al final, la persona. La respuesta separa lo que se vio en la foto de lo que dice la ficha.
- **No se infiere stock.** Las fichas son del catálogo histórico de ESCI (Amazon España, alrededor de 2022) y la respuesta lo dice. "Sí, lo tenemos" es la apertura del contrato de M3 y significa "está en el catálogo".
- **La válvula no está garantizada.** En M4 el VLM convirtió una playa en "rocas" y el sistema ofreció asientos de inodoro. Con el antibiótico (img_09) el enrutador no se negó: buscó, y la abstención vino del umbral. Con foto, la negativa a productos de venta restringida depende de que el catálogo no tenga una ficha parecida.
- **Un error no es una abstención.** Si `ver()` devuelve algo que no es JSON o algo falla, el comprador ve un mensaje de error, no la válvula, y el caso no cuenta como acierto.
- **No se genera ninguna imagen**, así que no aplica la etiqueta de "imagen generada".
- **Datos personales.** Las fotos son de bancos con licencia libre, sin caras ni documentos personales y sin metadatos EXIF. El sistema no guarda la foto del comprador: en las salidas solo queda el JSON de `ver()`. En un despliegue habría que decirle al comprador qué pasa con su foto.
- **Sesgo de contexto.** El catálogo es de Amazon España y el VLM se entrenó con internet. La Pony Malta (img_08), un producto latinoamericano, se leyó bien y el sistema no afirmó tenerla; es un solo caso.
- **El VLM inventa texto.** En img_06 "leyó" un texto que no está en la foto. Lo que diga `texto_visible` no es evidencia.

---

## 11. Limitaciones declaradas

1. **12 casos con foto.** Cada caso son 8 puntos porcentuales y no se calcularon intervalos de confianza para las filas con foto.
2. **M4.1 se diseñó mirando estos mismos 12 casos.**
3. **El etiquetado lo propuso el asistente** y la versión final coincide con la sugerencia en todas las filas. No hubo varios anotadores ni medida de acuerdo, como sí hubo en M3.
4. **Los casos los redactó el asistente**; el equipo eligió y aprobó las fotos.
5. **Fotos de bancos de imágenes**, no de compradores reales: limpias, bien iluminadas y casi siempre de un solo producto.
6. **"Campos" compara texto contra alias:** una lectura correcta escrita de otra forma puede contar como error.
7. **Generación greedy y una corrida de referencia.** No se midió formalmente la variación entre corridas ni entre GPU.
8. **El techo cubre 10 casos:** las fotos sin producto no tienen pregunta escrita equivalente.
9. **El índice de Chroma se reutiliza por conteo** en local, como en M3; la firma que sugiere la revisión no se implementó.
10. **Solo existencia:** "¿qué hay parecido a esto?" con foto queda fuera.
11. **El VLM y el generador son de la misma familia (Qwen).** No se usó un juez VLM; las notas son deterministas.
12. **El catálogo sigue siendo de Amazon España, sin fecha por ficha.**

---
