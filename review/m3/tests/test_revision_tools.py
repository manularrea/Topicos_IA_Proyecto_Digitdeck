"""Regresiones docentes: callbacks controlados, sin GPU/modelos/API."""
import copy
import importlib.util
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "Entregables/M3"))
import revision_tools as rt


@pytest.fixture
def original():
    path = ROOT / "review/m3/sources/funciones_seleccionadas.py"
    spec = importlib.util.spec_from_file_location("original_digitdeck", path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    m.CATALOGO = {"ids": ["B000000001", "B000000002", "B000000003"],
                  "titulo": ["Cuaderno azul pequeño", "Cuaderno azul grande", "Lápiz rojo"],
                  "contexto": ["[B000000001] Cuaderno azul pequeño", "[B000000002] Cuaderno azul grande", "[B000000003] Lápiz rojo"]}
    m.SYSTEM_ENRUTADOR = "DOBLE_ENRUTADOR"
    m.SYSTEM_RAG = "DOBLE_GENERADOR"
    m.armar_prompt = lambda idx, pregunta, encabezado: encabezado + "\n" + pregunta
    return m


@pytest.fixture
def caso():
    return {"id": "control", "pregunta": "¿Tienen cuadernos?", "tipo": "gold", "intencion": "existencia",
            "relevantes_esci": ["B000000001", "B000000002"], "relevantes_equipo": ["B000000001", "B000000002"]}


def configurar(m, nombre="verificar_existencia", obs=None, texto=None):
    if obs is None:
        obs = {"ranking": [0, 1, 2], "resultado": [0, 1], "t_rec": 0.1, "t_rr": 0.02}
    if texto is None:
        texto = "Sí, lo tenemos: [B000000001] [B000000002]"
    m.generar = lambda system, user, *args: (json.dumps({"tool": nombre, "args": {"consulta": "cuadernos"}})
                                          if system == m.SYSTEM_ENRUTADOR else texto)
    m.HERRAMIENTAS = {n: lambda q: copy.deepcopy(obs) for n in rt.NOMBRES}
    return rt.crear_sistema_D(vars(m))


@pytest.mark.parametrize("nombre", sorted(rt.NOMBRES))
def test_consulta_valida_conserva_texto_y_tildes(nombre):
    crudo = json.dumps({"tool": nombre, "args": {"consulta": " Mérida "}})
    assert rt.parsear_pedido("```json\n" + crudo + "\n```") == (nombre, "Mérida")


@pytest.mark.parametrize("valor", [None, 1, True, [], {}, "", "  "])
def test_rechaza_consulta_no_textual_o_vacia(valor):
    with pytest.raises(rt.ErrorEsquema):
        rt.parsear_pedido(json.dumps({"tool": "verificar_existencia", "args": {"consulta": valor}}))


@pytest.mark.parametrize("pedido", [
    {}, {"tool": "otra", "args": {"consulta": "x"}},
    {"tool": "verificar_existencia", "args": []}, {"tool": "verificar_existencia", "args": {}},
    {"tool": "verificar_existencia"}, {"tool": ["verificar_existencia"], "args": {}},
    {"tool": "verificar_existencia", "args": {"consulta": "x", "otro": 1}},
    {"tool": "verificar_existencia", "args": {"consulta": "x"}, "otro": 1}])
def test_rechaza_esquema(pedido):
    with pytest.raises(rt.ErrorEsquema):
        rt.parsear_pedido(json.dumps(pedido))


@pytest.mark.parametrize("crudo", [None, "", "{", "No digas NINGUNA", "NINGUNA y sí existe"])
def test_texto_invalido_no_es_decision_de_no_buscar(crudo):
    with pytest.raises(rt.ErrorEsquema):
        rt.parsear_pedido(crudo)


def test_ninguna_explicita():
    assert rt.parsear_pedido("  ninguna\n") == ("ninguna", None)


@pytest.mark.parametrize("nombre", sorted(rt.NOMBRES))
def test_ruta_valida_conserva_salida_original(original, caso, nombre):
    fn = configurar(original, nombre)
    antes = original.sistema_D(caso)
    despues = fn(caso)
    for key in ("consulta_busqueda", "ranking", "contexto_ids", "contexto", "pantalla", "respuesta",
                "respuesta_generada", "apertura", "abstiene", "citados", "herramienta"):
        assert despues[key] == antes[key], key
    assert despues["sistema"] == "D_revision" and despues["evaluacion_valida"] is True


def test_sin_resultados_conserva_abstencion_y_no_genera(original, caso):
    fn = configurar(original, obs={"ranking": [0], "resultado": [], "t_rec": 0.1, "t_rr": 0.1})
    def gen(system, user, *args):
        assert system == original.SYSTEM_ENRUTADOR
        return '{"tool":"verificar_existencia","args":{"consulta":"cuaderno"}}'
    original.generar = gen
    s = fn(caso)
    assert s["estado"] == "sin_resultados" and s["abstiene"] and s["evaluacion_valida"]
    assert s["ranking"] == ["B000000001"]


def test_ninguna_no_ejecuta_herramienta(original, caso):
    fn = configurar(original)
    original.generar = lambda *args: "NINGUNA"
    original.HERRAMIENTAS = {n: lambda q: pytest.fail("No debe ejecutar herramientas") for n in rt.NOMBRES}
    s = fn(caso)
    assert s["estado"] == "abstencion_dominio" and s["abstiene"] and s["evaluacion_valida"]


def test_error_formato_no_es_abstencion(original, caso):
    fn = configurar(original)
    original.generar = lambda *args: '{"tool":"verificar_existencia","args":{"consulta":42}}'
    s = fn(caso)
    assert s["estado"] == "error_formato" and not s["abstiene"] and not s["evaluacion_valida"]
    assert s["error_etapa"] == "esquema_llamada"


def test_fallo_backend_diferente_de_sin_resultados(original, caso):
    fn = configurar(original)
    def cae(q):
        raise TimeoutError("detalle que podría contener información privada")
    original.HERRAMIENTAS["verificar_existencia"] = cae
    s = fn(caso)
    assert s["estado"] == "error_operativo" and s["error_tipo"] == "TimeoutError"
    assert s["error_etapa"] == "herramienta" and not s["evaluacion_valida"] and not s["abstiene"]
    assert "privada" not in json.dumps(s)


@pytest.mark.parametrize("etapa", ["enrutamiento", "generacion"])
def test_modelo_caido_se_registra(original, caso, etapa):
    fn = configurar(original)
    buena = original.generar
    def gen(system, user, *args):
        if (system == original.SYSTEM_ENRUTADOR) == (etapa == "enrutamiento"):
            raise RuntimeError("modelo no disponible")
        return buena(system, user, *args)
    original.generar = gen
    s = fn(caso)
    assert s["error_etapa"] == etapa and not s["evaluacion_valida"]


def test_interrupcion_del_usuario_no_se_oculta(original, caso):
    fn = configurar(original)
    def stop(*args):
        raise KeyboardInterrupt()
    original.generar = stop
    with pytest.raises(KeyboardInterrupt):
        fn(caso)


@pytest.mark.parametrize("cambio", [
    {"ranking": [True]}, {"ranking": [-1]}, {"ranking": [3]}, {"ranking": [0, 0]},
    {"resultado": [2], "ranking": [0]}, {"resultado": "0"}, {"t_rec": -1},
    {"t_rr": float("nan")}, {"t_rec": True}, {"t_verif": 1},
    {"t_verif": 1, "candidatas": 1, "revisadas": 1, "exactas": -1}])
def test_observacion_invalida_no_llega_al_generador(original, caso, cambio):
    obs = {"ranking": [0, 1, 2], "resultado": [0, 1], "t_rec": 0.1, "t_rr": 0.1, **cambio}
    fn = configurar(original, obs=obs)
    s = fn(caso)
    assert s["estado"] == "error_formato" and s["error_etapa"] == "esquema_observacion"
    assert not s["evaluacion_valida"]


def test_conserva_metadatos_verificador(original, caso):
    fn = configurar(original, nombre="buscar_similares", obs={"ranking": [0, 1], "resultado": [0],
                    "t_rec": 0.1, "t_rr": 0.1, "t_verif": 0.2, "candidatas": 2, "revisadas": 2, "exactas": 1})
    s = fn(caso)
    assert s["verif_candidatas"] == 2 and s["verif_alternativas"] == 1
    assert s["latencia"]["verificacion"] == 0.2


def test_lote_continua_y_excluye_fallo_de_D3(original, caso):
    fn = configurar(original)
    llamadas = []
    def tool(q):
        llamadas.append(q)
        if len(llamadas) == 1:
            raise RuntimeError("fallo controlado")
        return {"ranking": [0, 1], "resultado": [0, 1], "t_rec": 0.1, "t_rr": 0.1}
    original.HERRAMIENTAS["verificar_existencia"] = tool
    adv = {**caso, "tipo": "adversarial", "id": "adv"}
    casos = [adv, caso]
    original_casos = copy.deepcopy(casos)
    informe = rt.evaluar_lote(fn, casos, original.dimension_1, original.dimension_3)
    assert informe["cobertura"]["validos"] == 1 and informe["cobertura"]["errores"] == 1
    assert informe["detalle"][0]["d3"] is None
    assert informe["aciertos_D3_en_validos"] == {"numerador": 1, "denominador": 1, "valor": 1.0}
    assert casos == original_casos


def test_lote_todo_error_no_da_cero_de_modelo(original, caso):
    fn = configurar(original)
    original.generar = lambda *args: "formato inválido"
    r = rt.evaluar_lote(fn, [caso], original.dimension_1, original.dimension_3)
    assert r["aciertos_D3_en_validos"]["valor"] is None
    assert r["cobertura"]["fraccion_valida"] == 0.0


def test_validacion_global_y_lote_vacio(original, caso):
    fn = configurar(original)
    with pytest.raises(ValueError):
        rt.evaluar_lote(fn, [caso, caso], original.dimension_1, original.dimension_3)
    with pytest.raises(ValueError):
        rt.evaluar_lote(fn, [{**caso, "pregunta": []}], original.dimension_1, original.dimension_3)
    assert rt.evaluar_lote(fn, [], original.dimension_1, original.dimension_3)["cobertura"]["total"] == 0
    with pytest.raises(ValueError):
        rt.crear_sistema_D({})


def test_no_sobrescribe_y_serializa_none(tmp_path):
    p = tmp_path / "nueva" / "corrida.json"
    rt.guardar_revision({"medida": None}, p)
    assert json.loads(p.read_text()) == {"medida": None}
    with pytest.raises(FileExistsError):
        rt.guardar_revision({"otra": 1}, p)
    assert json.loads(p.read_text()) == {"medida": None}
    with pytest.raises(ValueError):
        rt.guardar_revision({"medida": float("nan")}, tmp_path / "nan.json")
    assert not (tmp_path / "nan.json").exists()
