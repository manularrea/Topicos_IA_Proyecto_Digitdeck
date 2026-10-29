# Propuestas docentes M4 — Digitdeck (opt-in, no fusionar sin validar)

Referencia evaluada: `6afab21` (`main` del original, 25/10/2026 01:15 -05:00). No se modifican cifras, CSV ni salidas entregadas.

## C1 — Hash del split de test portable (celda 9 del notebook, conteo desde 0)

**Qué cambia:** una línea. `to_csv(index=False)` → `to_csv(index=False, lineterminator="\r\n")`.

**Por qué:** desde pandas 1.5, `to_csv` usa `os.linesep`. El hash registrado en M1 (`4d31950e…`) corresponde a finales de línea CRLF (Windows). En Linux/macOS (incluido Colab) la celda calcula `331ee032…` y el `assert` detiene el notebook antes de construir el catálogo. INFORME_M4 §9.2 describe esta corrección, pero el notebook entregado no la contiene.

**Prueba (datos reales, sin modelos):** con los parquet públicos de `amazon-science/esci-data` y el código exacto de la celda 9:

| Versión | Hash | Resultado |
|---|---|---|
| `6afab21` (macOS, `os.linesep="\n"`) | `331ee032d616c815e0dcacabacdeebb8` | `AssertionError` |
| con C1 | `4d31950e81340999c4cbda611b4256c9` | OK (92.739 pares, 3.844 consultas, 80.383 productos) |

En Windows el resultado no cambia (CRLF explícito = CRLF por defecto). No se ejecutaron las celdas posteriores (requieren GPU y modelos); C1 no certifica la corrida completa en Colab.

## C2 — Guardia de lectura antes de buscar (`propuesta/guardia_lectura.py`)

Implementa la idea del propio equipo (INFORME_M4 §7, peor caso img_10): si `ver()` dice que hay producto pero no trae **ni marca ni modelo**, no se busca; se cierra con un estado `pide_confirmacion` que solicita el dato al comprador. No es un error ni una abstención por inexistencia.

**Activación en una COPIA del notebook**, en `correr_foto` (celda 41), justo después de la válvula:

```python
from guardia_lectura import requiere_confirmacion, MENSAJE_CONFIRMACION
...
        if not producto_identificado(v):
            return _cerrar(...)                                   # válvula existente
        if requiere_confirmacion(v["json"]):                      # C2
            return _cerrar(nombre, p, "pide_confirmacion", None, [], [],
                           f"{APERTURAS['abstiene']} {MENSAJE_CONFIRMACION}", lat, t_total, extra)
```

Los consumidores (`nota_caso`, conteo de estados, cobertura) deben tratar `pide_confirmacion` como una no-afirmación válida; revisar esas celdas antes de usarlo.

**Proyección sobre los artefactos entregados** (`reproyectar`): supone que la guardia corta el flujo antes de buscar, como la válvula. No vuelve a correr modelos.

| | D3 | Adversariales | Afirmaciones falsas | Casos donde actúa |
|---|---|---|---|---|
| M4 entregado | 4/12 | 1/4 | 5 | — |
| M4 + C2 (proyección) | 6/12 | 3/4 | 2 | img_05, img_10, img_11 |
| M4.1 entregado | 7/12 | 4/4 | 2 | — |
| M4.1 + C2 (proyección) | 7/12 | 4/4 | 2 | img_05 |

**Límites:** se diseñó mirando estos 12 casos (post hoc, como M4.1); los positivos no mejoran (1/6); en preguntas genéricas ("¿Venden estufas como esta?") pide un dato que quizá el comprador no tiene. Validar con fotos nuevas antes de adoptarla.

## Pruebas

```bash
python -m unittest review/m4/tests/test_guardia_lectura.py -v   # 6 pruebas, solo stdlib
python review/m4/tests/verificar_scorecard.py                   # reconstruye delta_m4.csv desde scorecard_m4.csv
```

Entorno y salidas en `evidence/validacion_m4.json`.
