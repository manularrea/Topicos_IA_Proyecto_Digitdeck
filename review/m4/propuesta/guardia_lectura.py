"""Propuesta docente (opt-in) para M4 de Digitdeck: no buscar con una lectura que no identifica el producto.

No modifica el notebook ni las cifras entregadas. Replica la idea que el equipo propone en INFORME_M4 §7
("no buscar si el JSON no trae al menos marca o modelo") como un estado nuevo, `pide_confirmacion`,
que no afirma ni se presenta como abstención por inexistencia: le pide al comprador el dato que falta.
"""
import json
import unicodedata
from pathlib import Path

# Mismos vacíos que la celda 40 del notebook M4 (VACIOS).
VACIOS = {"", "null", "none", "no se aprecia", "no se aprecia en la imagen", "desconocido", "n/a", "ninguno"}
MENSAJE_CONFIRMACION = ("No puedo confirmar qué producto es con la foto. "
                        "¿Me dices la marca o el modelo para buscarlo en el catálogo?")


def _normal(t):
    t = unicodedata.normalize("NFKD", str(t)).encode("ascii", "ignore").decode()
    return " ".join(t.lower().split())


def valor(js, campo):
    """Equivalente a `_valor` del notebook: None si el VLM dejó el campo vacío o escribió 'null'."""
    v = js.get(campo) if isinstance(js, dict) else None
    if v is None or isinstance(v, bool):
        return v
    v = str(v).strip()
    return None if _normal(v) in VACIOS else v


def requiere_confirmacion(ver_json):
    """True si la lectura dice que hay producto pero no trae ni marca ni modelo."""
    if not isinstance(ver_json, dict):
        return False
    return valor(ver_json, "marca") is None and valor(ver_json, "modelo") is None


def con_guardia(consulta_fn):
    """Envuelve `consulta_fn(js, pregunta)` del notebook: si falta identidad, lanza PideConfirmacion.

    Uso en una COPIA del notebook (después de la celda 43):
        from guardia_lectura import con_guardia, PideConfirmacion
    y en `correr_foto`, antes de `validar_consulta`, capturar PideConfirmacion y cerrar con
    estado "pide_confirmacion" (ver README de la propuesta)."""
    def _fn(js, pregunta):
        if requiere_confirmacion(js):
            raise PideConfirmacion(MENSAJE_CONFIRMACION)
        return consulta_fn(js, pregunta)
    return _fn


class PideConfirmacion(Exception):
    """No es error ni abstención por inexistencia: falta un dato del comprador."""


def nota_contrafactual(criterio_efectivo):
    """Nota si el sistema no afirma (pide confirmación) con los criterios del eval set M4."""
    return {"acierto_respuesta": 0.0, "no_afirma": 1.0, "valvula": 1.0}[criterio_efectivo]


def reproyectar(scorecard_csv, salidas_json):
    """Recalcula agregados de M4 y M4.1 si la guardia hubiera actuado sobre los ver_json entregados.

    Es una proyección: supone que pedir confirmación corta el flujo antes de buscar (como la válvula),
    de modo que no hace falta volver a correr modelos. No sustituye una corrida real."""
    import csv
    sal = json.loads(Path(salidas_json).read_text(encoding="utf-8"))["con_imagen"]
    with open(scorecard_csv, encoding="utf-8") as fh:
        filas = list(csv.DictReader(fh))
    res = {}
    for sistema, suf_nota, suf_falsa in (("M4", "m4", "m4"), ("M4.1", "m4.1", "m4_1")):
        notas, falsas, adv, activada = [], 0, 0, []
        for f in filas:
            s = sal[sistema][f["id"]]
            nota = float(f[f"nota_{suf_nota}"])
            falsa = f[f"afirmacion_falsa_{suf_falsa}"] == "True"
            if s.get("estado") in ("respuesta_generada", "sin_resultados") and requiere_confirmacion(s.get("ver_json")):
                activada.append(f["id"])
                nota, falsa = nota_contrafactual(f["criterio_efectivo_m4"]), False
            notas.append(nota)
            falsas += falsa
            adv += nota if f["tipo"] == "adversarial" else 0
        n_adv = sum(f["tipo"] == "adversarial" for f in filas)
        res[sistema] = {"guardia_activada": activada, "d3": f"{int(sum(notas))}/{len(notas)}",
                        "adversariales": f"{int(adv)}/{n_adv}", "afirmaciones_falsas": falsas}
    return res


if __name__ == "__main__":
    import sys
    raiz = Path(sys.argv[1] if len(sys.argv) > 1 else ".") / "Entregables/M4"
    print(json.dumps(reproyectar(raiz / "scorecard_m4.csv", raiz / "Resultados/salidas_m4.json"),
                     ensure_ascii=False, indent=2))
