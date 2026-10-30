import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "propuesta"))
import ic_con_foto as ic  # noqa: E402


class TestIC(unittest.TestCase):
    def test_wilson_valores_conocidos(self):
        lo, hi = ic.wilson(4, 12)
        self.assertAlmostEqual(lo, 0.138, places=3)
        self.assertAlmostEqual(hi, 0.609, places=3)
        self.assertEqual(ic.wilson(0, 10)[0], 0.0)

    def test_bootstrap_diferencia_nula(self):
        self.assertEqual(ic.bootstrap_dif([1, 0, 1], [1, 0, 1], reps=200), (0.0, 0.0))

    def test_scorecard_entregado_coincide_con_delta(self):
        r = ic.calcular()
        self.assertEqual(r["n"], 12)
        self.assertEqual(r["d3"]["M3 sola"]["aciertos"], "3/12")
        self.assertEqual(r["d3"]["M4"]["aciertos"], "4/12")
        self.assertEqual(r["d3"]["M4.1"]["aciertos"], "7/12")
        self.assertEqual(r["afirmaciones_falsas"]["M4"]["casos"], "5/12")


if __name__ == "__main__":
    unittest.main()
