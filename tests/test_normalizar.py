"""O normalizador: os casos de normalizar.CASOS e o dicionário do projeto."""
import contextlib
import io
import unicodedata
import unittest

import normalizar
from normalizar import carregar_dicionario, extenso, normalizar as norm


class TestCasos(unittest.TestCase):

    def test_casos_do_normalizador(self):
        # os mesmos de "python normalizar.py --teste", sem dicionário
        self.assertGreaterEqual(len(normalizar.CASOS), 24)
        for entrada, esperado in normalizar.CASOS:
            with self.subTest(entrada=entrada):
                self.assertEqual(norm(entrada, []), esperado)

    def test_testar_devolve_zero(self):
        with contextlib.redirect_stdout(io.StringIO()) as saida:
            self.assertEqual(normalizar.testar(), 0)
        self.assertIn(f"{len(normalizar.CASOS)}/{len(normalizar.CASOS)} casos ok",
                      saida.getvalue())


class TestExtenso(unittest.TestCase):

    def test_valores(self):
        casos = {
            0: "zero", 21: "vinte e um", 101: "cento e um", 1001: "mil e um",
            2026: "dois mil e vinte e seis", 1_000_000: "um milhão",
            999_999_999: "novecentos e noventa e nove milhões novecentos e "
                         "noventa e nove mil novecentos e noventa e nove",
        }
        for n, esperado in casos.items():
            with self.subTest(n=n):
                self.assertEqual(extenso(n), esperado)


class TestBordas(unittest.TestCase):

    def test_data_invalida_fica_como_esta(self):
        self.assertEqual(norm("32/13", []), "trinta e dois/treze")

    def test_sigla_de_seis_letras_nao_se_soletra(self):
        self.assertEqual(norm("ABCDEF", []), "ABCDEF")

    def test_sigla_curta_se_soletra(self):
        self.assertEqual(norm("o MCP", []), "o ême cê pê")


class TestDicionario(unittest.TestCase):

    def test_mais_longo_primeiro(self):
        tamanhos = [len(t) for t, _ in carregar_dicionario(fonemas=False)]
        self.assertEqual(tamanhos, sorted(tamanhos, reverse=True))

    def test_grafia_para_o_kokoro(self):
        self.assertEqual(norm("o Claude Code e os tokens", fonemas=False),
                         "o Cláude Côude e os tôquens")

    def test_prefixo_sub_separado(self):
        # 21/10, Peter: sem a entrada, o Kokoro lia "su-ba-gente"
        self.assertEqual(norm("o subagente e os Subagentes", fonemas=False),
                         "o súbi agente e os súbi agentes")

    def test_fonemas_para_o_piper(self):
        # a 3ª coluna, com o til separado (NFD), como o Piper aceita
        self.assertEqual(norm("tokens", fonemas=True),
                         unicodedata.normalize("NFD", "[[tˈokẽjs]]"))

    def test_sem_diferenca_de_maiusculas(self):
        self.assertEqual(norm("o CACHE", fonemas=False), "o quéche")


if __name__ == "__main__":
    unittest.main()
