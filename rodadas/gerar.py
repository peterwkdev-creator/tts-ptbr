"""Gera as amostras do roteiro com o Piper, texto cru contra normalizado.

Para cada voz em modelos/*.onnx grava amostras/<voz>-<cru|norm>.wav e mede o
tempo de síntese em CPU, a duração do áudio e o fator de tempo real
(síntese / duração; abaixo de 1 é mais rápido que a fala).

Uso:
  python rodadas/gerar.py
"""
import sys
import time
import wave
from pathlib import Path

from piper import PiperVoice

AQUI = Path(__file__).resolve().parent.parent  # a raiz
sys.path.insert(0, str(AQUI))
from normalizar import normalizar
MODELOS = AQUI / "modelos"
SAIDA = AQUI / "amostras"


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    SAIDA.mkdir(exist_ok=True)
    cru = (AQUI / "rodadas" / "roteiro.txt").read_text(encoding="utf-8").strip()
    textos = {"cru": cru, "norm": normalizar(cru)}
    (SAIDA / "roteiro-normalizado.txt").write_text(textos["norm"] + "\n",
                                                   encoding="utf-8")
    linhas = ["voz\ttexto\tsintese_s\taudio_s\tfator_tempo_real"]
    for modelo in sorted(MODELOS.glob("*.onnx")):
        voz = PiperVoice.load(str(modelo))
        nome = modelo.stem.removeprefix("pt_BR-")
        for rotulo, texto in textos.items():
            arquivo = SAIDA / f"{nome}-{rotulo}.wav"
            inicio = time.perf_counter()
            with wave.open(str(arquivo), "wb") as wav:
                voz.synthesize_wav(texto, wav)
            sintese = time.perf_counter() - inicio
            with wave.open(str(arquivo), "rb") as wav:
                audio = wav.getnframes() / wav.getframerate()
            linhas.append(f"{nome}\t{rotulo}\t{sintese:.2f}\t{audio:.2f}\t"
                          f"{sintese / audio:.3f}")
            print(linhas[-1])
    (SAIDA / "medidas.tsv").write_text("\n".join(linhas) + "\n",
                                       encoding="utf-8")


if __name__ == "__main__":
    main()
