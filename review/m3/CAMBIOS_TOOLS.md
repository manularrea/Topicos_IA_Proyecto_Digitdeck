# C1 — Variante explícita para validar herramientas y separar errores

## Qué cambia

`Entregables/M3/revision_tools.py` construye `D_revision` a partir de los componentes originales cargados. No redefine `sistema_D` ni modifica `SALIDAS` o el notebook. Es un adaptador docente para discutir/incorporar, no una nueva corrida certificada.

- Exige `tool` permitido, `args` objeto y `consulta` texto no vacío; no convierte otros tipos ni sustituye silenciosamente la pregunta.
- `NINGUNA` es una decisión explícita. JSON roto es `error_formato`, no una abstención correcta.
- Diferencia `abstencion_dominio`, `sin_resultados`, `respuesta_generada`, `error_formato` y `error_operativo`. El estado de generación no implica acierto del modelo.
- Comprueba el contrato de las observaciones. Una excepción queda registrada por etapa/tipo, sin exponer `str(exc)` al comprador. No captura interrupciones del usuario ni promete reintentos automáticos.
- Los errores llevan `evaluacion_valida=False`, no reciben D1/D3 y siempre figuran en el total/cobertura. No pueden incrementar abstención adversarial. Un promedio sobre válidos no se presenta como desempeño sobre todo el lote.
- Guardado exclusivo: no sobrescribe una corrida anterior.

No cambia prompts, recuperación, reranker, umbrales ni reformulación válida. No modifica las fórmulas D1/D3, el juez ni RAGAS. Requiere las mismas dependencias/modelos/insumos declarados por el equipo.

## Activación en una copia de trabajo

Desde `Entregables/M3/`, usar una **copia del notebook y de Resultados**. Las celdas originales guardan archivos con nombres fijos: no ejecutarlas contra el directorio histórico que se quiere conservar.

Añadir esta celda después de definir las funciones de `c043` y antes de `c047`, que libera los modelos. Para evitar volver a generar D histórico innecesariamente, en la copia se puede separar `c043` antes de `SALIDAS["D"] = correr(sistema_D)` y ejecutar solo sus definiciones. `CATALOGO`, prompts, generador, reranker y verificador deben seguir cargados.

```python
from pathlib import Path
from datetime import datetime, timezone
from revision_tools import crear_sistema_D, evaluar_lote, guardar_revision

D_revision = crear_sistema_D(globals())
# Primero un lote pequeño autorizado; después EVAL_M3 completo.
informe_revision = evaluar_lote(D_revision, EVAL_M3[:3], dimension_1, dimension_3)
print(informe_revision["cobertura"])
print(informe_revision["aciertos_D3_en_validos"])
sello = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
ruta = Path("Resultados_revision") / f"D_revision_{sello}.json"
guardar_revision(informe_revision, ruta)
```

No inyectar salidas fallidas en las celdas históricas de evaluación: no conocen el nuevo estado. Para RAGAS/jueces, emparejar por `id` únicamente los casos con `evaluacion_valida is True`, declarar cobertura, conservar los excluidos y usar archivos nuevos. Comparar versiones sobre los mismos casos/protocolo, sin sustituir cifras de la entrega.

## Pruebas y alcance

Desde la raíz del repositorio:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest review/m3/tests/test_revision_tools.py -v
```

48 pruebas aprobadas. Prueban esquema, éxito, falta de resultados, excepciones, interrupción, contrato de observación, continuidad del lote, cobertura y no sobrescritura. La comparación con D usa transcripciones identificadas de c033/c035/c037/c043 y callbacks; NO ejecuta el LLM o Chroma. Validar integración real antes de fusionar. `sources/funciones_seleccionadas.py` solo sirve de fixture docente y no se importa desde la aplicación. Entorno y hashes en `evidence/validacion_tools.json`.

La recomendación de auditoría complementaria de citas está documentada en la revisión general. Su extensión ejecutable C2 no forma parte de este commit.
