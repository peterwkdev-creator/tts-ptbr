"""Exemplo 1: o normalizador escreve por extenso o que o TTS leria mal.

Número, porcentagem, data, versão, dinheiro, sigla e termo em inglês, numa
frase só. Roda sem modelo e sem dependência:

  python exemplos/01_normalizar.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # a raiz
from normalizar import normalizar

FRASE = ("Testei a API do Claude Code v2.1.299 em 18/10/2026: 96% dos tokens "
         "foram releitura, e o plano custaria R$ 1.299,90.")

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    print("antes: ", FRASE)
    # fonemas=False: a grafia para o Kokoro (o Piper aceita fonemas [[...]])
    print("depois:", normalizar(FRASE, fonemas=False))
