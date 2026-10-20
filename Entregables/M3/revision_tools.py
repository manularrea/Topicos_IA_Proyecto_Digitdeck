"""Propuesta docente opt-in. No reemplaza D ni sus resultados históricos.

Crea D_revision con las herramientas, prompts y presentación del notebook.
Solo endurece el contrato de entrada y separa fallos de decisiones del dominio.
"""
from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Mapping
import json
import math
from numbers import Integral, Real
from pathlib import Path
from time import perf_counter
from typing import Any

PROTOCOLO = "digitdeck-tools-revision-v1"
NOMBRES = frozenset({"verificar_existencia", "buscar_similares"})
MENSAJE_ERROR = "No pude completar la consulta por un error del sistema. No se verificó la disponibilidad del producto."


class ErrorEsquema(ValueError):
    """Una llamada o una observación no cumple el contrato declarado."""


def parsear_pedido(crudo: str) -> tuple[str, str | None]:
    """Exige consulta textual no vacía; no coerciona listas/números a texto.

    Conserva el JSON rodeado de texto del parser original. Solo la respuesta
    NINGUNA (sin texto adicional) expresa explícitamente no usar herramienta.
    """
    if not isinstance(crudo, str):
        raise ErrorEsquema("La salida del enrutador debe ser texto.")
    if crudo.strip().upper() == "NINGUNA":
        return "ninguna", None
    inicio, fin = crudo.find("{"), crudo.rfind("}")
    try:
        pedido = json.loads(crudo[inicio:fin + 1]) if inicio >= 0 and fin > inicio else None
    except (json.JSONDecodeError, ValueError) as exc:
        raise ErrorEsquema("JSON de herramienta inválido.") from exc
    if not isinstance(pedido, dict) or set(pedido) != {"tool", "args"}:
        raise ErrorEsquema("Se esperan únicamente tool y args.")
    nombre, args = pedido["tool"], pedido["args"]
    if not isinstance(nombre, str) or nombre not in NOMBRES:
        raise ErrorEsquema("Herramienta no permitida.")
    if not isinstance(args, dict) or set(args) != {"consulta"}:
        raise ErrorEsquema("args debe ser un objeto con consulta.")
    consulta = args["consulta"]
    if not isinstance(consulta, str) or not consulta.strip():
        raise ErrorEsquema("consulta debe ser un texto no vacío.")
    return nombre, consulta.strip()


def validar_observacion(obs: Any, n_catalogo: int) -> None:
    """Comprueba estructura, posiciones y tiempos, no relevancia comercial."""
    if not isinstance(obs, dict):
        raise ErrorEsquema("La herramienta debe devolver un objeto.")
    for campo in ("ranking", "resultado"):
        valores = obs.get(campo)
        if not isinstance(valores, list) or any(
            isinstance(i, bool) or not isinstance(i, Integral) or not 0 <= i < n_catalogo
            for i in valores
        ):
            raise ErrorEsquema(f"{campo}: posiciones de catálogo inválidas.")
        if len(valores) != len(set(valores)):
            raise ErrorEsquema(f"{campo}: posiciones repetidas.")
    if not set(obs["resultado"]).issubset(obs["ranking"]):
        raise ErrorEsquema("El resultado debe pertenecer al ranking.")
    tiempos = ("t_rec", "t_rr", "t_verif") if "t_verif" in obs else ("t_rec", "t_rr")
    for campo in tiempos:
        valor = obs.get(campo)
        if isinstance(valor, bool) or not isinstance(valor, Real) or not math.isfinite(valor) or valor < 0:
            raise ErrorEsquema(f"{campo}: tiempo inválido.")
    if "t_verif" in obs:
        for campo in ("candidatas", "revisadas", "exactas"):
            valor = obs.get(campo)
            if isinstance(valor, bool) or not isinstance(valor, Integral) or valor < 0:
                raise ErrorEsquema(f"{campo}: conteo inválido.")


def crear_sistema_D(ns: Mapping[str, Any]) -> Callable[[dict], dict]:
    """Construye una variante sin modificar globals, SALIDAS ni sistema_D.

    Invocar cuando los colaboradores del notebook estén definidos/cargados,
    antes de liberar los modelos. Fallos por caso quedan fuera de D1/D3.
    """
    requeridos = ("generar", "SYSTEM_ENRUTADOR", "SYSTEM_RAG", "armar_prompt",
                  "_salida", "APERTURAS", "HERRAMIENTAS", "CATALOGO")
    faltan = [k for k in requeridos if k not in ns]
    if faltan:
        raise ValueError(f"Faltan componentes del notebook: {', '.join(faltan)}")
    for nombre in NOMBRES:
        if not callable(ns["HERRAMIENTAS"].get(nombre)):
            raise ValueError(f"Falta herramienta ejecutable: {nombre}")

    def sistema(p: dict) -> dict:
        if not isinstance(p, dict) or not isinstance(p.get("id"), str) or not p["id"].strip():
            raise ValueError("Cada caso debe tener id textual no vacío.")
        if not isinstance(p.get("pregunta"), str) or not p["pregunta"].strip():
            raise ValueError("Cada caso debe tener pregunta textual no vacía.")
        t_total = perf_counter()
        lat: dict[str, float] = {}
        crudo, herramienta, consulta = None, None, None
        etapa = "enrutamiento"
        try:
            t = perf_counter()
            crudo = ns["generar"](ns["SYSTEM_ENRUTADOR"], f"Pregunta: {p['pregunta']}", 80)
            lat["enrutamiento"] = perf_counter() - t
            etapa = "esquema_llamada"
            herramienta, consulta = parsear_pedido(crudo)
            extra = {"herramienta": herramienta, "salida_enrutador": crudo,
                     "consulta_original": p["pregunta"], "enrutador_formato_ok": True,
                     "evaluacion_valida": True, "protocolo_revision": PROTOCOLO}
            ranking, ctx = [], []
            respuesta = ns["APERTURAS"]["abstiene"]
            estado = "abstencion_dominio"
            if herramienta != "ninguna":
                etapa = "herramienta"
                obs = ns["HERRAMIENTAS"][herramienta](consulta)
                etapa = "esquema_observacion"
                validar_observacion(obs, len(ns["CATALOGO"]["ids"]))
                ranking, ctx = obs["ranking"], obs["resultado"]
                lat.update(recuperacion=float(obs["t_rec"]), reranking=float(obs["t_rr"]))
                if "t_verif" in obs:
                    lat["verificacion"] = float(obs["t_verif"])
                    extra.update(verif_candidatas=int(obs["candidatas"]), verif_revisadas=int(obs["revisadas"]),
                                 verif_exactas=int(obs["exactas"]), verif_alternativas=len(ctx))
                estado = "sin_resultados"
                if ctx:
                    etapa = "generacion"
                    encabezado = f"Usaste la herramienta {herramienta} y obtuviste estas fichas del catálogo:"
                    t = perf_counter()
                    respuesta = ns["generar"](ns["SYSTEM_RAG"], ns["armar_prompt"](ctx, p["pregunta"], encabezado))
                    lat["generacion"] = perf_counter() - t
                    if not isinstance(respuesta, str) or not respuesta.strip():
                        raise ErrorEsquema("El generador no devolvió una respuesta textual.")
                    estado = "respuesta_generada"
            etapa = "presentacion"
            extra["estado"] = estado
            lat["total"] = perf_counter() - t_total
            return ns["_salida"]("D_revision", p, consulta, ranking, ctx, respuesta, lat, extra)
        except Exception as exc:
            # No convierte una excepción en 'no existe', ni en abstención correcta.
            # No captura KeyboardInterrupt/SystemExit; no expone secretos en str(exc).
            lat["total"] = perf_counter() - t_total
            return {"sistema": "D_revision", "id": p["id"], "consulta_original": p["pregunta"],
                    "consulta_busqueda": consulta, "herramienta": herramienta,
                    "salida_enrutador": crudo if isinstance(crudo, str) else None,
                    "enrutador_formato_ok": herramienta is not None,
                    "ranking": [], "contexto_ids": [], "contexto": [], "pantalla": [], "citados": [],
                    "respuesta": MENSAJE_ERROR, "respuesta_generada": None, "apertura": "error",
                    "abstiene": False, "evaluacion_valida": False, "protocolo_revision": PROTOCOLO,
                    "estado": "error_formato" if isinstance(exc, ErrorEsquema) else "error_operativo",
                    "error_etapa": etapa, "error_tipo": type(exc).__name__,
                    "latencia": {k: round(v, 3) for k, v in lat.items()}}

    sistema.nombre = "D_revision"
    return sistema


def evaluar_lote(sistema: Callable, casos: list[dict], dimension_1: Callable, dimension_3: Callable) -> dict:
    """Continúa después de errores operativos y conserva todos los casos.

    Métricas del dominio: solo sobre ejecuciones válidas; cobertura y fallos
    siempre al lado. No alimenta los errores al harness ni al juez.
    """
    ids = [p.get("id") for p in casos]
    if any(not isinstance(i, str) or not i.strip() for i in ids) or len(ids) != len(set(ids)):
        raise ValueError("Los ids del lote deben ser textos únicos no vacíos.")
    if any(not isinstance(p.get("pregunta"), str) or not p["pregunta"].strip() for p in casos):
        raise ValueError("Todas las preguntas deben ser textos no vacíos.")
    salidas, detalle = [], []
    for p in casos:
        s = sistema(p)
        salidas.append(s)
        fila = {"id": p["id"], "estado": s["estado"], "evaluacion_valida": s["evaluacion_valida"],
                "d1": None, "d3": None}
        if s["evaluacion_valida"] is True:
            fila.update(d1=dimension_1(p, s), d3=dimension_3(p, s))
        detalle.append(fila)
    validos = sum(s["evaluacion_valida"] is True for s in salidas)
    aciertos = sum(bool(f["d3"]["acierto_respuesta"]) for f in detalle if f["d3"] is not None)
    return {"protocolo_revision": PROTOCOLO, "sistema": "D_revision", "salidas": salidas, "detalle": detalle,
            "cobertura": {"total": len(casos), "validos": validos, "errores": len(casos) - validos,
                          "fraccion_valida": validos / len(casos) if casos else None,
                          "estados": dict(Counter(s["estado"] for s in salidas))},
            "aciertos_D3_en_validos": {"numerador": aciertos, "denominador": validos,
                                      "valor": aciertos / validos if validos else None}}


def guardar_revision(informe: dict, ruta: str | Path) -> None:
    """Escritura exclusiva: se rehúsa a sobrescribir una corrida previa."""
    texto = json.dumps(informe, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with ruta.open("x", encoding="utf-8") as f:
        f.write(texto)
