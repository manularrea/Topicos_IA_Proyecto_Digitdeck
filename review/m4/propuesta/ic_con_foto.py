"""Propuesta docente: intervalos de confianza para las filas con foto del scorecard M4.

Solo stdlib y solo lectura de Entregables/M4/scorecard_m4.csv; no modifica cifras.
- Wilson 95 % para la proporción de aciertos D3 de cada versión.
- Bootstrap pareado por caso (semilla fija) para la diferencia frente a «M3 pregunta sola»
  y para las afirmaciones falsas.
Uso (desde la raíz): python review/m4/propuesta/ic_con_foto.py [--json]
"""
import csv
import json
import math
import random
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
SCORECARD = RAIZ / "Entregables/M4/scorecard_m4.csv"
VERSIONES = {"M3 sola": "nota_m3_pregunta_sola", "M4": "nota_m4", "M4.1": "nota_m4.1", "Techo": "nota_m3_techo"}
FALSAS = {"M4": "afirmacion_falsa_m4", "M4.1": "afirmacion_falsa_m4_1"}
SEMILLA, B, Z = 20261025, 10000, 1.959964


def wilson(k, n, z=Z):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return (max(0.0, c - h), min(1.0, c + h))


def bootstrap_dif(a, b, semilla=SEMILLA, reps=B):
    """IC 95 % percentil de mean(a) - mean(b), remuestreando casos (pareado)."""
    rng = random.Random(semilla)
    n = len(a)
    difs = []
    for _ in range(reps):
        idx = [rng.randrange(n) for _ in range(n)]
        difs.append(sum(a[i] - b[i] for i in idx) / n)
    difs.sort()
    return (difs[int(0.025 * reps)], difs[int(0.975 * reps) - 1])


def _bool(x):
    return 1 if str(x).strip().lower() in ("1", "1.0", "true") else 0


def calcular(path=SCORECARD):
    filas = list(csv.DictReader(open(path, encoding="utf-8-sig")))
    out = {"n": len(filas), "d3": {}, "dif_vs_m3_sola": {}, "afirmaciones_falsas": {}}
    # Celdas vacías = caso excluido de la métrica (p. ej. error de formato), igual que en delta_m4.csv.
    valores = {v: [float(r[c]) if r[c] != "" else None for r in filas] for v, c in VERSIONES.items()}
    for v, col in valores.items():
        xs = [x for x in col if x is not None]
        k = int(sum(xs))
        lo, hi = wilson(k, len(xs))
        out["d3"][v] = {"aciertos": f"{k}/{len(xs)}", "ic95": [round(lo, 3), round(hi, 3)]}
    for v in ("M4", "M4.1"):
        pares = [(a, b) for a, b in zip(valores[v], valores["M3 sola"]) if a is not None and b is not None]
        a, b = [x for x, _ in pares], [y for _, y in pares]
        lo, hi = bootstrap_dif(a, b)
        d = (sum(a) - sum(b)) / len(pares)
        out["dif_vs_m3_sola"][v] = {"n_pares": len(pares), "dif": round(d, 3), "ic95": [round(lo, 3), round(hi, 3)]}
    for v, c in FALSAS.items():
        k = sum(_bool(r[c]) for r in filas)
        lo, hi = wilson(k, len(filas))
        out["afirmaciones_falsas"][v] = {"casos": f"{k}/{len(filas)}", "ic95": [round(lo, 3), round(hi, 3)]}
    return out


if __name__ == "__main__":
    res = calcular()
    if "--json" in sys.argv:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        print(f"Filas con foto: n={res['n']}")
        for v, d in res["d3"].items():
            print(f"  D3 {v:8s} {d['aciertos']:>6s}  IC95 Wilson {d['ic95']}")
        for v, d in res["dif_vs_m3_sola"].items():
            print(f"  {v} - M3 sola (n={d['n_pares']}): {d['dif']:+.3f}  IC95 bootstrap pareado {d['ic95']}")
        for v, d in res["afirmaciones_falsas"].items():
            print(f"  Afirmaciones falsas {v}: {d['casos']}  IC95 Wilson {d['ic95']}")
