"""A/B da leitura dos números (21/10): as falas do 7 com número, pelo caminho do narrar.py.

A atual; B só a última palavra do número tônica (as outras com ˌ); C as outras sem acento; D como B, com as palavras antes da última coladas.
"""
import re
import sys
from pathlib import Path

import numpy as np

TTS = Path("D:/Arquivos/ClaudeProjects/Projetos/PeterWKDev/sys-tts")
sys.path.insert(0, str(TTS))
from kokoro_onnx import Kokoro  # noqa: E402
from audio import gravar  # noqa: E402
from kokoro import PAUSA_VIRGULA, VARIANTES, fonemizar  # noqa: E402
from normalizar import CENTENAS, DEZENAS, UNIDADES, normalizar  # noqa: E402
from prosodia import RITMO, RODADAS  # noqa: E402

NUM = set(UNIDADES + DEZENAS + CENTENAS + ["cem", "mil", "milhão", "milhões", "meio"]) - {""}
SEP = re.compile(r"[,.?!:;]")


def grupo(texto, fonemas, troca, colar=False):
    """Nas sequências de número ("cento e dez mil"), a tônica fica só na última palavra."""
    palavras = texto.split()
    tokens = fonemas.split(" ")
    if len(palavras) != len(tokens):
        return fonemas, False
    limpa = [SEP.sub("", p).lower() for p in palavras]
    eh = [w in NUM for w in limpa]
    i = 0
    while i < len(limpa):
        if not eh[i]:
            i += 1
            continue
        j, fim = i, i
        while j + 1 < len(limpa) and not SEP.search(palavras[j]) and (
                eh[j + 1] or (limpa[j + 1] == "e" and j + 2 < len(limpa) and eh[j + 2])):
            j += 1
            if eh[j]:
                fim = j
        for k in range(i, fim):
            if eh[k]:
                tokens[k] = tokens[k].replace("ˈ", troca)
        if colar and fim > i:
            tokens[i:fim] = ["".join(tokens[i:fim])] + [None] * (fim - i - 1)
        i = j + 1
    return " ".join(t for t in tokens if t is not None), True


def vaos(audio, taxa):
    """Silêncios internos de 40 ms ou mais (janela de 10 ms abaixo de -40 dB do pico)."""
    jan = int(taxa * 0.01)
    n = len(audio) // jan
    rms = np.sqrt((audio[:n * jan].reshape(n, jan) ** 2).mean(1))
    baixo = rms < np.abs(audio).max() * 0.01
    voz = np.where(~baixo)[0]
    baixo = baixo[voz[0]:voz[-1]]
    corridas, c = [], 0
    for b in baixo:
        if b:
            c += 1
        else:
            if c >= 4:
                corridas.append(c * 10)
            c = 0
    return corridas


sys.stdout.reconfigure(encoding="utf-8")
saida = Path(sys.argv[1])
saida.mkdir(parents=True, exist_ok=True)
k = Kokoro(str(TTS / "modelos/kokoro/kokoro-v1.0.onnx"), str(TTS / "modelos/kokoro/voices-v1.0.bin"))
pesos, batido = VARIANTES["dora"]
estilo = sum(k.get_voice_style(v) * p for v, p in pesos.items())
ajustes = next(a for nome, _, a, *_ in RODADAS["r10"] if nome == "5-final")
falas = ["Nossa regra dizia: súbi agente relê 110 mil tokens por passo. Medimos no nosso projeto: 48 mil.",
         "Em 34 súbi agentes, a mediana do passo foi 48 mil. Na sessão principal, 96 mil. Metade.",
         "Na mediana, nove e meio por cento da sessão; no pior caso, 37."]
for nome, troca in {"A-atual": None, "B-secundaria": "ˌ", "C-sem-acento": "", "D-colado": "ˌ+"}.items():
    pedacos = []
    for fala in falas:
        texto = normalizar(fala, dicionario=[], fonemas=False)
        f = fonemizar(k, texto, batido)
        for a in ajustes:
            f = a(f)
        if troca is not None:
            f, ok = grupo(texto, f, troca.rstrip("+"), troca.endswith("+"))
            assert ok, (texto, f)
        audio, taxa = k.create(f, voice=estilo, speed=RITMO[0], lang="pt-br", is_phonemes=True,
                               sentence_pause=0, clause_pause=PAUSA_VIRGULA)
        print(nome, "|", f, "| vãos ms:", vaos(audio, taxa))
        pedacos += [audio, np.zeros(int(taxa * 0.6), audio.dtype)]
    gravar(np.concatenate(pedacos), taxa, saida / f"{nome}.wav", acabamento=True)
