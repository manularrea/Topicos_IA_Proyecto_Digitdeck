import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ / "review/m4/propuesta"))
import guardia_lectura as g  # noqa: E402

M4 = RAIZ / "Entregables/M4"


class TestGuardia(unittest.TestCase):
    def test_sin_marca_ni_modelo_pide_confirmacion(self):
        self.assertTrue(g.requiere_confirmacion({"es_producto": True, "tipo_producto": "rocas", "marca": None, "modelo": None}))

    def test_null_como_texto_cuenta_como_vacio(self):
        js = {"es_producto": True, "tipo_producto": "auriculares inalámbricos", "marca": "null", "modelo": "null"}
        self.assertTrue(g.requiere_confirmacion(js))

    def test_con_marca_o_modelo_sigue(self):
        self.assertFalse(g.requiere_confirmacion({"tipo_producto": "bebida", "marca": "Pony Malta", "modelo": "null"}))
        self.assertFalse(g.requiere_confirmacion({"tipo_producto": "dron", "marca": None, "modelo": "Air 2S"}))

    def test_json_invalido_no_se_convierte_en_confirmacion(self):
        self.assertFalse(g.requiere_confirmacion(None))

    def test_envoltorio_respeta_consulta_original(self):
        fn = g.con_guardia(lambda js, p: "apple airpods")
        self.assertEqual(fn({"marca": "Apple", "modelo": "AirPods"}, "¿Venden estos audífonos?"), "apple airpods")
        with self.assertRaises(g.PideConfirmacion):
            fn({"tipo_producto": "calentador de exterior", "marca": None, "modelo": None}, "¿Venden estufas como esta?")

    def test_reproyeccion_sobre_artefactos_entregados(self):
        r = g.reproyectar(M4 / "scorecard_m4.csv", M4 / "Resultados/salidas_m4.json")
        self.assertEqual(r["M4"]["guardia_activada"], ["img_05", "img_10", "img_11"])
        self.assertEqual(r["M4"]["d3"], "6/12")
        self.assertEqual(r["M4"]["adversariales"], "3/4")
        self.assertEqual(r["M4"]["afirmaciones_falsas"], 2)
        self.assertEqual(r["M4.1"]["guardia_activada"], ["img_05"])
        self.assertEqual(r["M4.1"]["d3"], "7/12")
        self.assertEqual(r["M4.1"]["afirmaciones_falsas"], 2)


if __name__ == "__main__":
    unittest.main()
