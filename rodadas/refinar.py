"""Rodada 2: ajustes de síntese, pausas e volume nas vozes do Piper.

Para cada voz × ajuste grava amostras/<rodada>/<voz>-<ajuste>.wav:
  1. síntese frase a frase sem esticar o volume (normalize_audio=False);
  2. pausa entre frases (PAUSA, maior depois de "?");
  3. ffmpeg: passa-alta de 70 Hz e loudnorm a -16 LUFS, pico -1,5 dBTP
     (o alvo de áudio dos Reels do projeto).
Grava também amostras/<rodada>/fonemas.txt (o que o espeak entregou ao modelo),
para achar a palavra lida errado e corrigi-la no dicionario.tsv.

Uso:
  python rodadas/refinar.py [rodada, padrão r3] [voz ...]
"""
import sys
from pathlib import Path

import numpy as np
from piper import PiperVoice, SynthesisConfig

AQUI = Path(__file__).resolve().parent.parent  # a raiz
sys.path.insert(0, str(AQUI))
from audio import gravar
from normalizar import normalizar
# Rodada 3 (18/10): só a faber. Cadu e jeff saíram (pedido do Peter); a
# faber soou robótica na rodada 1, então os ajustes sobem a variação.
VOZES = ["faber-medium"]
# length_scale (> 1 mais lento), noise_scale (variação da voz),
# noise_w_scale (variação do ritmo). Padrão das vozes: 1.0 / 0.667 / 0.8.
# "firme" (1.05/0.55/0.7, menos variação) saiu: ia contra o robótico.
AJUSTES = {
    "padrao": (1.0, 0.667, 0.8),
    "calma": (1.08, 0.70, 0.9),
    # sugestão da pesquisa no GitHub (18/10); noise_w > 1 gagueja (relato)
    "lenta": (1.1, 0.7, 0.8),
    "viva": (1.04, 0.80, 0.95),
}
PAUSA = {"padrao": 0.30, "?": 0.45}


def sintetizar(voz, texto, ajuste):
    length, noise, noise_w = ajuste
    config = SynthesisConfig(length_scale=length, noise_scale=noise,
                             noise_w_scale=noise_w, normalize_audio=False)
    partes, fonemas, taxa = [], [], 22050
    for trecho in voz.synthesize(texto, syn_config=config):
        taxa = trecho.sample_rate
        partes.append(trecho.audio_float_array)
        fonemas.append("".join(trecho.phonemes))
        final = trecho.phonemes[-1] if trecho.phonemes else "."
        pausa = PAUSA["?"] if final == "?" else PAUSA["padrao"]
        partes.append(np.zeros(int(taxa * pausa), dtype=np.float32))
    audio = np.concatenate(partes[:-1])  # sem pausa depois da última frase
    return audio, taxa, fonemas


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    args = sys.argv[1:]
    # r7 (18/10): a faber com a calibração das rodadas 4 a 6
    rodada = args.pop(0) if args and args[0][:1] == "r" and \
        args[0][1:].isdigit() else "r3"
    saida = AQUI / "amostras" / rodada
    saida.mkdir(parents=True, exist_ok=True)
    texto = normalizar((AQUI / "rodadas" / "roteiro.txt").read_text(encoding="utf-8"))
    relatorio = []
    for nome in args or VOZES:
        voz = PiperVoice.load(str(AQUI / "modelos" / f"pt_BR-{nome}.onnx"))
        for rotulo, ajuste in AJUSTES.items():
            audio, taxa, fonemas = sintetizar(voz, texto, ajuste)
            gravar(audio, taxa, saida / f"{nome}-{rotulo}.wav")
            print(f"{nome}\t{rotulo}\t{len(audio) / taxa:.2f} s")
            if rotulo == "padrao":
                relatorio += [f"# {nome}"] + fonemas
    (saida / "fonemas.txt").write_text("\n".join(relatorio) + "\n",
                                       encoding="utf-8")


if __name__ == "__main__":
    main()
