"""Exemplo 2: somar um dicionário próprio ao do projeto.

O dicionario.tsv da raiz traz os termos do projeto (Claude Code, prompt,
token...). Para os seus, escreva outro .tsv no mesmo formato e junte os
dois. Roda sem modelo e sem dependência:

  python exemplos/02_dicionario_proprio.py
"""
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))  # a raiz
from normalizar import carregar_dicionario, normalizar

FRASE = "Subi o Python num Docker e depois no Kubernetes, sem estourar o cache."

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    padrao = carregar_dicionario(fonemas=False)
    meu = carregar_dicionario(AQUI / "meu_dicionario.tsv", fonemas=False)
    # o termo mais longo primeiro; num empate, o seu vem antes e vence
    dicionario = sorted(meu + padrao, key=lambda par: -len(par[0]))
    print("só o do projeto:", normalizar(FRASE, padrao))
    print("com o seu:      ", normalizar(FRASE, dicionario))
