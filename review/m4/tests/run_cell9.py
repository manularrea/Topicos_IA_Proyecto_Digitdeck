"""Ejecuta SOLO la celda 9 del notebook M4 (hash del split de test) sin GPU ni modelos.

Uso: python run_cell9.py RUTA_NOTEBOOK DIR_PARQUETS_ESCI"""
import json, sys, re, hashlib, pandas as pd
from pathlib import Path
nb = json.load(open(sys.argv[1], encoding="utf-8"))
src = "".join(nb["cells"][9]["source"])
g = {"re": re, "hashlib": hashlib, "pd": pd,
     "RUTA_EXAMPLES": Path(sys.argv[2]) / Path("shopping_queries_dataset_examples.parquet"),
     "RUTA_PRODUCTS": Path(sys.argv[2]) / Path("shopping_queries_dataset_products.parquet")}
try:
    exec(src, g); print("CELDA 9: OK")
except AssertionError as e:
    print("CELDA 9: AssertionError:", e)
