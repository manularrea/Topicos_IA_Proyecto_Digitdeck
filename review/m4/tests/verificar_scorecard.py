"""Comprobación docente: reconstruye los agregados del scorecard M4 entregado y compara con delta_m4.csv.

Solo stdlib. Uso: python review/m4/tests/verificar_scorecard.py  (desde la raíz del repositorio)."""
import csv
import json
import statistics
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
M4 = RAIZ / "Entregables/M4"


def p95(v):
    v = sorted(v); k = (len(v) - 1) * 0.95; i = int(k)
    return v[i] + (v[min(i + 1, len(v) - 1)] - v[i]) * (k - i)


def main():
    sc = list(csv.DictReader(open(M4 / "scorecard_m4.csv", encoding="utf-8")))
    delta = {r["grupo"]: r for r in csv.DictReader(open(M4 / "Resultados/delta_m4.csv", encoding="utf-8"))}
    chk = []

    def suma(col):
        v = [float(r[col]) for r in sc if r[col] != ""]
        return f"{int(sum(v))}/{len(v)}"

    d3 = delta["Con imagen (12 casos): aciertos, D3 (oficial)"]
    chk.append(("D3 M3 sola", suma("nota_m3_pregunta_sola"), d3["M3"].split()[0]))
    chk.append(("D3 M4", suma("nota_m4"), d3["M4"]))
    chk.append(("D3 M4.1", suma("nota_m4.1"), d3["M4.1 (post hoc)"]))
    chk.append(("D3 techo", suma("nota_m3_techo"), d3["techo"]))
    falsas = delta["Con imagen: afirmaciones falsas"]
    chk.append(("falsas M4", str(sum(r["afirmacion_falsa_m4"] == "True" for r in sc)), falsas["M4"]))
    chk.append(("falsas M4.1", str(sum(r["afirmacion_falsa_m4_1"] == "True" for r in sc)), falsas["M4.1 (post hoc)"]))
    lat = delta["Latencia media con imagen (s)"]
    for col, clave in (("seg_total_m4", "M4"), ("seg_total_m4_1", "M4.1 (post hoc)")):
        chk.append((f"lat media {col}", f"{statistics.mean(float(r[col]) for r in sc):.2f}", lat[clave].split()[0]))
    l95 = delta["Latencia p95 con imagen (s)"]
    for col, clave in (("seg_total_m3_sola", "M3"), ("seg_total_m4", "M4"), ("seg_total_m4_1", "M4.1 (post hoc)")):
        chk.append((f"lat p95 {col}", f"{p95([float(r[col]) for r in sc]):.2f}", l95[clave]))
    ok = all(a == b for _, a, b in chk)
    for n, a, b in chk:
        print(f"{'OK ' if a == b else 'DIF'} {n}: recalculado={a} delta={b}")
    old = list(csv.DictReader(open(M4 / "Resultados/scorecard_m4.csv", encoding="utf-8")))
    difs = [r["id"] for r, o in zip(sc, old) if r["nota_m4"] != o["nota_m4"] or r["nota_m4.1"] != o["nota_m4.1"]]
    print("Resultados/scorecard_m4.csv difiere del oficial en nota_m4/nota_m4.1 para:", difs)
    print(json.dumps({"todas_coinciden": ok, "scorecard_obsoleto_difiere": bool(difs)}))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
