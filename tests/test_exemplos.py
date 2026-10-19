"""Os exemplos que rodam sem modelo, a narração lida e o baixar_modelos."""
import importlib.util
import re
import subprocess
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]


def rodar(script):
    r = subprocess.run([sys.executable, script], cwd=RAIZ, capture_output=True,
                       text=True, encoding="utf-8", check=True)
    return r.stdout


class TestExemplos(unittest.TestCase):

    def test_01_normalizar(self):
        saida = rodar("exemplos/01_normalizar.py")
        self.assertIn("á pê i do Cláude Côude versão dois ponto um ponto "
                      "duzentos e noventa e nove, em dezoito de outubro", saida)
        self.assertIn("mil duzentos e noventa e nove reais e noventa centavos",
                      saida)

    def test_02_dicionario_proprio(self):
        saida = rodar("exemplos/02_dicionario_proprio.py")
        self.assertIn("Subi o Páiton num Dóquer e depois no Cubernétis", saida)

    @unittest.skipUnless(importlib.util.find_spec("kokoro_onnx"),
                         "precisa do requirements.txt")
    def test_narracao_do_exemplo_3(self):
        from narrar import ler
        frases = ler(RAIZ / "exemplos" / "narracao.txt")
        self.assertEqual([s for s, _ in frases], [1, 1, 2])


class TestBaixarModelos(unittest.TestCase):

    def test_fonte_oficial_e_hash(self):
        from baixar_modelos import ARQUIVOS
        for nome, (url, sha) in ARQUIVOS.items():
            with self.subTest(nome=nome):
                self.assertRegex(url, r"^https://(github\.com/thewh1teagle/"
                                      r"kokoro-onnx|huggingface\.co/rhasspy/"
                                      r"piper-voices)/")
                self.assertTrue(re.fullmatch(r"[0-9a-f]{64}", sha))


if __name__ == "__main__":
    unittest.main()
