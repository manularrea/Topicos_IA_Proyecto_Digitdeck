"""Fixture docente: funciones transcritas, NO notebook completo.

Origen: Entregables/M3/ENTREGABLE.ipynb, c033/c035/c037/c043,
commit 1ead5646a01286e9e043557aba83afec5e9c639a,
blob d075b20c8818f604f666034797e261d41ab32c67.
Subconjunto de la transcripción usada en el preview aprobado. No se
modifican sus ramas de decisión. Los tests inyectan catálogo, herramientas,
prompts y generador. Este archivo NO se importa desde la aplicación.
"""
import json
import re
import time
import unicodedata
import numpy as np

PALABRAS_NOMBRE = 8
APERTURAS = {"afirma": "Sí, lo tenemos:",
             "similares": "No lo tenemos exacto, pero hay productos parecidos:",
             "abstiene": "No tengo esa información en mis fuentes."}
APERTURA_CORRECTA = {"existencia": "afirma", "similar": "similares"}

def _normal(t):
    t = unicodedata.normalize("NFD", (t or "").lower())
    return re.sub(r"\s+", " ", "".join(ch for ch in t if unicodedata.category(ch) != "Mn")).strip()

def leer_apertura(respuesta):
    r = _normal(respuesta)[:120]
    if r.startswith(_normal(APERTURAS["abstiene"])[:25]) or "no tengo esa informacion" in r[:60]:
        return "abstiene"
    if r.startswith("no lo tenemos exacto") or "hay productos parecidos" in r[:80]:
        return "similares"
    if r.startswith("si, lo tenemos") or r.startswith("si lo tenemos"):
        return "afirma"
    return "otro"

def ids_citados(respuesta, contexto_ids):
    texto = (respuesta or "").upper()
    return [pid for pid in contexto_ids if pid.upper() in texto]

def nombre_corto(i):
    palabras = CATALOGO["titulo"][i].split()
    return " ".join(palabras[:PALABRAS_NOMBRE]).rstrip(" ,;:-|/")

def completar_nombres(respuesta, ctx):
    texto = respuesta or ""
    for i in ctx:
        marca = f"[{CATALOGO['ids'][i]}]"
        pos = texto.upper().find(marca.upper())
        if pos == -1:
            continue
        clave = _normal(" ".join(CATALOGO["titulo"][i].split()[:3]))
        entorno = _normal(texto[max(0, pos - 120):pos + len(marca) + 120])
        if clave and clave in entorno:
            continue
        texto = texto[:pos] + nombre_corto(i) + " " + texto[pos:]
    return texto

def _salida(nombre, p, consulta, ranking, ctx, respuesta, lat, extra=None):
    respuesta_generada = respuesta
    respuesta = completar_nombres(respuesta, ctx)
    apertura = leer_apertura(respuesta)
    abstiene = apertura == "abstiene"
    ctx_ids = [CATALOGO["ids"][i] for i in ctx]
    s = {"sistema": nombre, "id": p["id"], "consulta_busqueda": consulta,
         "ranking": [CATALOGO["ids"][i] for i in ranking[:10]], "contexto_ids": ctx_ids,
         "contexto": [CATALOGO["contexto"][i] for i in ctx], "respuesta": respuesta,
         "respuesta_generada": respuesta_generada, "apertura": apertura,
         "abstiene": abstiene, "pantalla": [] if abstiene else ctx_ids, "citados": ids_citados(respuesta, ctx_ids),
         "latencia": {k: round(v, 3) for k, v in lat.items()}}
    s.update(extra or {})
    return s

def ndcg_con_ideal(rels_top, n_relevantes, k=10):
    descuentos = 1.0 / np.log2(np.arange(2, k + 2))
    rels = np.asarray(rels_top[:k], dtype=float)
    dcg = float(np.sum(rels * descuentos[:len(rels)]))
    idcg = float(np.sum(descuentos[:min(n_relevantes, k)]))
    return dcg / idcg if idcg > 0 else 0.0

def mrr(rels):
    for i, r in enumerate(rels):
        if r > 0:
            return 1.0 / (i + 1)
    return 0.0

def dimension_1(p, s):
    if p["tipo"] != "gold":
        return {"ndcg10_esci": None, "mrr_esci": None, "ndcg10_equipo": None}
    rel = set(p["relevantes_esci"])
    rels = [int(pid in rel) for pid in s["ranking"][:10]]
    d = {"ndcg10_esci": ndcg_con_ideal(rels, len(rel)), "mrr_esci": mrr(rels), "ndcg10_equipo": None}
    if p["intencion"] == "existencia":
        rel_eq = set(p["relevantes_equipo"])
        d["ndcg10_equipo"] = ndcg_con_ideal([int(pid in rel_eq) for pid in s["ranking"][:10]], len(rel_eq)) if rel_eq else None
    return d

def dimension_3(p, s):
    if p["tipo"] == "adversarial":
        pantalla_ok = bool(s["abstiene"])
        respuesta_ok = pantalla_ok
    elif s["abstiene"]:
        pantalla_ok = respuesta_ok = False
    else:
        rel = set(p["relevantes_esci"])
        pantalla_ok = sum(pid in rel for pid in s["pantalla"][:3]) >= min(2, len(rel))
        respuesta_ok = pantalla_ok and s["apertura"] == APERTURA_CORRECTA[p["intencion"]]
    rel_eq = set(p["relevantes_equipo"] or [])
    falsa = (p["intencion"] in ("existencia", "ninguna") and s["apertura"] == "afirma"
             and not any(pid in rel_eq for pid in s["pantalla"][:3]))
    return {"acierto_pantalla": pantalla_ok, "acierto_respuesta": respuesta_ok,
            "afirmacion_falsa": falsa, "formato_roto": s["apertura"] == "otro"}

def _extraer_json(t):
    i, j = t.find("{"), t.rfind("}")
    if i != -1 and j > i:
        try:
            return json.loads(t[i:j + 1])
        except Exception:
            return None
    return None

def enrutar(pregunta):
    crudo = generar(SYSTEM_ENRUTADOR, f"Pregunta: {pregunta}", 80)
    pedido = _extraer_json(crudo)
    if isinstance(pedido, dict) and pedido.get("tool") in ("verificar_existencia", "buscar_similares"):
        args = pedido.get("args") if isinstance(pedido.get("args"), dict) else {}
        consulta = str(args.get("consulta") or pregunta).strip() or pregunta
        return pedido["tool"], consulta, crudo, True
    return "ninguna", None, crudo, (pedido is None and "NINGUNA" in crudo.upper())

def sistema_D(p):
    lat, t_total = {}, time.perf_counter()
    t = time.perf_counter(); herramienta, consulta, crudo, json_ok = enrutar(p["pregunta"]); lat["enrutamiento"] = time.perf_counter() - t
    extra = {"herramienta": herramienta, "salida_enrutador": crudo, "enrutador_formato_ok": json_ok}
    if herramienta == "ninguna":
        lat["total"] = time.perf_counter() - t_total
        return _salida("D", p, None, [], [], APERTURAS["abstiene"], lat, extra)
    obs = HERRAMIENTAS[herramienta](consulta)
    lat["recuperacion"], lat["reranking"] = obs["t_rec"], obs["t_rr"]
    if "t_verif" in obs:
        lat["verificacion"] = obs["t_verif"]
        extra.update({"verif_candidatas": obs["candidatas"], "verif_revisadas": obs["revisadas"],
                      "verif_exactas": obs["exactas"], "verif_alternativas": len(obs["resultado"])})
    if not obs["resultado"]:
        lat["total"] = time.perf_counter() - t_total
        return _salida("D", p, consulta, obs["ranking"], [], APERTURAS["abstiene"], lat, extra)
    encabezado = f"Usaste la herramienta {herramienta} y obtuviste estas fichas del catálogo:"
    t = time.perf_counter(); respuesta = generar(SYSTEM_RAG, armar_prompt(obs["resultado"], p["pregunta"], encabezado)); lat["generacion"] = time.perf_counter() - t
    lat["total"] = time.perf_counter() - t_total
    return _salida("D", p, consulta, obs["ranking"], obs["resultado"], respuesta, lat, extra)
