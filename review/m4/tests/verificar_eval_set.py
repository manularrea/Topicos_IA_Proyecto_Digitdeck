"""Comprobación docente del eval set M4: imágenes idénticas en píxeles, derivadas declaradas y columna `estado`.

Requiere Pillow y numpy. Uso (desde la raíz): python review/m4/tests/verificar_eval_set.py
Sale con código 1 si encuentra imágenes idénticas no declaradas como copia o filas con estado distinto de los aceptados.
"""
import csv
import hashlib
import sys
from pathlib import Path

import numpy as np
from PIL import Image

RAIZ = Path(__file__).resolve().parents[3]
EVAL = RAIZ / "Entregables/M4/eval_set"
ESTADOS_FINALES = {"final", "aprobado", "congelado"}


def huella_pixeles(p):
    a = np.asarray(Image.open(p).convert("RGB"))
    return hashlib.sha256(a.tobytes() + str(a.shape).encode()).hexdigest()


def main():
    filas = list(csv.DictReader(open(EVAL / "eval_set_m4.csv", encoding="utf-8-sig")))
    grupos = {}
    for r in filas:
        grupos.setdefault(huella_pixeles(EVAL / "imagenes" / Path(r["imagen"]).name), []).append(r["id"])
    duplicadas = [g for g in grupos.values() if len(g) > 1]
    estados = sorted({r.get("estado", "") for r in filas})
    print(f"casos: {len(filas)} | imágenes distintas en píxeles: {len(grupos)}")
    print(f"grupos idénticos en píxeles: {duplicadas or 'ninguno'}")
    print(f"valores de `estado`: {estados}")
    ok = all(e in ESTADOS_FINALES for e in estados)
    print("estado final:", "OK" if ok else "PENDIENTE (marcar como final si los criterios se fijaron antes de correr)")
    return 0 if ok and not duplicadas else 1


if __name__ == "__main__":
    sys.exit(main())
