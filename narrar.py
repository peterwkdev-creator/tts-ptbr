"""Narração de um post: uma frase por linha, no método do 2-numeros da r11.

Entrada: arquivo com linhas "N | frase" (N = slide em que a frase é dita;
linha vazia ou começada por # se ignora). Cada frase é um lote do Kokoro,
com os ajustes de fonemas e o acabamento da r11 (prosodia.py), velocidade
pelo RITMO e o último lote mais lento (FINAL). Saída na pasta indicada:
  voz.wav      a narração inteira, -16 LUFS (audio.py)
  tempos.json  versão do TTS, voz e, por frase: slide, texto, início e fim (s)

Uso:
  python narrar.py <narracao.txt> <pasta de saída> [voz]

voz: uma das VARIANTES de kokoro.py (alex, alex-rr, dora, dora-rr,
alex-santa); padrão alex. Modelo em modelos/kokoro/ (baixar_modelos.py)
e ffmpeg no PATH. Exemplo: exemplos/03_narrar.py.
"""
import json
import sys
from pathlib import Path

import numpy as np
from kokoro_onnx import Kokoro

from audio import gravar
from kokoro import PAUSA_VIRGULA, VARIANTES, fonemizar
from normalizar import normalizar, tonica_dos_numeros
from prosodia import FINAL, PAUSA, RITMO, RODADAS

AQUI = Path(__file__).parent
VERSAO = "r11 2-numeros"
ENTRE_SLIDES = 0.25  # s a mais de pausa quando a frase seguinte muda de slide


def ler(arquivo):
    """Linhas "N | frase" de arquivo (Path) -> [(N, frase), ...]."""
    frases = []
    for linha in arquivo.read_text(encoding="utf-8").splitlines():
        if not linha.strip() or linha.startswith("#"):
            continue
        slide, texto = linha.split("|", 1)
        frases.append((int(slide), texto.strip()))
    return frases


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    entrada, saida = Path(sys.argv[1]), Path(sys.argv[2])
    voz = sys.argv[3] if len(sys.argv) > 3 else "alex"
    saida.mkdir(parents=True, exist_ok=True)
    modelo = AQUI / "modelos" / "kokoro"
    kokoro = Kokoro(str(modelo / "kokoro-v1.0.onnx"),
                    str(modelo / "voices-v1.0.bin"))
    pesos, batido = VARIANTES[voz]
    estilo = sum(kokoro.get_voice_style(v) * p for v, p in pesos.items())
    ajustes = next(a for nome, _, a, *_ in RODADAS["r11"] if nome == "2-numeros")
    frases = ler(entrada)
    partes, tempos, agora, taxa = [], [], 0.0, 24000
    for i, (slide, texto) in enumerate(frases):
        normal = normalizar(texto, fonemas=False)
        fonemas = fonemizar(kokoro, normal, batido)
        for ajuste in ajustes:
            fonemas = ajuste(fonemas)
        fonemas, ok = tonica_dos_numeros(normal, fonemas)
        if not ok:
            print(f"aviso: números sem ajuste (tokens não casam): {normal}")
        ultima = i == len(frases) - 1
        velocidade = FINAL if ultima else RITMO[i % len(RITMO)]
        audio, taxa = kokoro.create(fonemas, voice=estilo, speed=velocidade,
                                    lang="pt-br", is_phonemes=True,
                                    sentence_pause=0, clause_pause=PAUSA_VIRGULA)
        dur = len(audio) / taxa
        tempos.append({"slide": slide, "texto": texto, "fonemas": fonemas,
                       "inicio": round(agora, 3), "fim": round(agora + dur, 3)})
        pausa = PAUSA.get(texto[-1], PAUSA["."])
        if not ultima and frases[i + 1][0] != slide:
            pausa += ENTRE_SLIDES
        partes += [audio, np.zeros(int(taxa * pausa), dtype=audio.dtype)]
        agora += dur + int(taxa * pausa) / taxa
        print(f"{slide}\t{dur:.2f} s\t{texto}")
    audio = np.concatenate(partes[:-1])
    gravar(audio, taxa, saida / "voz.wav", acabamento=True)
    (saida / "tempos.json").write_text(json.dumps(
        {"versao": VERSAO, "voz": voz, "duracao": round(len(audio) / taxa, 3),
         "frases": tempos}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"total {len(audio) / taxa:.2f} s -> {saida / 'voz.wav'}")


if __name__ == "__main__":
    main()
