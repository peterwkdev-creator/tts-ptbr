"""A medida: WER e palavras rodam sem o Whisper e sem o numpy."""
import unittest

from medir import palavras, wer


class TestWer(unittest.TestCase):

    def test_igual_e_zero(self):
        self.assertEqual(wer(["a", "b", "c"], ["a", "b", "c"]), 0)

    def test_troca(self):
        self.assertEqual(wer(["a", "b"], ["a", "c"]), 0.5)

    def test_falta_e_sobra(self):
        self.assertEqual(wer(["a", "b", "c", "d"], ["a", "c", "d", "e"]), 0.5)


class TestPalavras(unittest.TestCase):

    def test_normaliza_e_tira_acento(self):
        self.assertEqual(palavras("Só 96%!"),
                         ["so", "noventa", "e", "seis", "por", "cento"])

    def test_os_dois_lados_batem(self):
        # o Whisper escreve "R$" e números; o roteiro pode vir por extenso
        self.assertEqual(palavras("v2.1 custa R$ 2,00"),
                         palavras("versão dois ponto um custa dois reais"))

    def test_dicionario_nao_entra(self):
        # o dicionário troca "Claude Code" inteiro; a mesma palavra escrita
        # tem de dar a mesma palavra dos dois lados
        self.assertEqual(palavras("Claude Code e tokens"), ["claude", "code", "e", "tokens"])
        self.assertEqual(palavras("Cloud Code")[1], palavras("Claude Code")[1])

    def test_versao_sem_v_perde_o_ponto(self):
        # limite conhecido: sem o "v", "2.1" não é versão e o ponto some
        # (o Whisper escreve "versão 2.1.299"), o que soma erro ao WER
        self.assertEqual(palavras("versão 2.1"), ["versao", "dois", "um"])


if __name__ == "__main__":
    unittest.main()
