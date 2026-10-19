"""Acabamento de áudio comum ao Piper e ao Kokoro.

gravar(): float de -1 a 1 -> WAV 16 bits, depois ffmpeg com passa-alta de
70 Hz e loudnorm a -16 LUFS, pico -1,5 dBTP (o alvo de áudio dos Reels
do projeto), em duas passadas: a 1ª mede, a 2ª aplica em modo
linear. Numa passada só media de -16,8 a -17,4 LUFS (18/10).
"""
import json
import re
import subprocess
import wave

import numpy as np

ALVO = "I=-16:TP=-1.5:LRA=11"
# Acabamento opcional (rodada 9, 18/10, a partir de guias de mixagem de
# voz): de-esser leve nos "s" chiados e equalização de voz, com corte leve
# em 300 e 700 Hz (embolado, nasal) e realce em 2 kHz (clareza).
ACABAMENTO = ("deesser=i=0.3:m=0.4:f=0.5,"
              "equalizer=f=300:t=q:w=1:g=-2,equalizer=f=700:t=q:w=1.4:g=-1.5,"
              "equalizer=f=2000:t=q:w=1:g=2,")


def gravar(audio, taxa, destino, acabamento=False):
    """Grava audio (numpy, float de -1 a 1) em destino (Path .wav).

    acabamento=True soma o de-esser e a equalização de ACABAMENTO.
    Precisa do ffmpeg no PATH."""
    filtros = ACABAMENTO if acabamento else ""
    bruto = destino.with_suffix(".bruto.wav")
    with wave.open(str(bruto), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(taxa)
        wav.writeframes((np.clip(audio, -1, 1) * 32767).astype("<i2").tobytes())
    medida = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", str(bruto), "-af",
         f"{filtros}highpass=f=70,loudnorm={ALVO}:print_format=json", "-f", "null",
         "-"], capture_output=True, text=True, check=True).stderr
    # o ffmpeg escreve mais linhas depois do JSON: pegar só o bloco {...}
    m = json.loads(re.findall(r"\{[^{}]*\}", medida)[-1])
    filtro = (f"{filtros}highpass=f=70,loudnorm={ALVO}:linear=true"
              f":measured_I={m['input_i']}:measured_TP={m['input_tp']}"
              f":measured_LRA={m['input_lra']}"
              f":measured_thresh={m['input_thresh']}"
              f":offset={m['target_offset']}")
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                    "-i", str(bruto), "-af", filtro, "-ar", str(taxa),
                    str(destino)], check=True)
    bruto.unlink()
