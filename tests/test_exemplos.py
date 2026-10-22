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


def carregar(script):
    """Importa um exemplo pelo caminho (o nome começa com dígito)."""
    caminho = RAIZ / "exemplos" / script
    spec = importlib.util.spec_from_file_location(caminho.stem, caminho)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


class TestExemplo5Vozes(unittest.TestCase):
    """A medida de 19/10 (vozes_medidas.tsv) se refaz sem modelo: calibrada,
    duração e WER de cada linha saem da transcrição pelo linha_tsv()."""

    def setUp(self):
        self.vozes = carregar("05_vozes.py")
        texto = (RAIZ / "exemplos" / "vozes_medidas.tsv").read_text(
            encoding="utf-8")
        self.linhas = texto.splitlines()

    def test_cabecalho_e_ordem(self):
        self.assertEqual(self.linhas[0], self.vozes.CABECALHO)
        self.assertEqual([l.split("\t")[0] for l in self.linhas[1:]],
                         self.vozes.ORDEM)

    def test_wer_confere_com_a_transcricao(self):
        for linha in self.linhas[1:]:
            voz, _, duracao, _, transcricao = linha.split("\t")
            with self.subTest(voz=voz):
                self.assertEqual(self.vozes.linha_tsv(voz, float(duracao),
                                                      transcricao), linha)

    def test_sem_etapa_mostra_o_uso(self):
        r = subprocess.run([sys.executable, "exemplos/05_vozes.py"], cwd=RAIZ,
                           capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(r.returncode, 1)
        self.assertIn("python exemplos/05_vozes.py medir", r.stderr)


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
