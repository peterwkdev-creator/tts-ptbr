"""Amostras com a base Kokoro-82M (kokoro-onnx, sem torch).

Vozes PT-BR do Kokoro: pf_dora, pm_alex, pm_santa. Uma mistura é a média
ponderada dos estilos (examples/with_blending.py do kokoro-onnx): é por ela
que se dosa o sotaque.

O espeak do kokoro-onnx (espeakng-loader) não é o do Piper. Por isso o texto
é fonemizado aqui, corrigido por CORRECOES e só então sintetizado
(is_phonemes=True). O que saiu de cada amostra fica em <saída>/fonemas.txt.

Modelo e vozes: release model-files-v1.0 de thewh1teagle/kokoro-onnx, em
modelos/kokoro/ (fora do git; baixar_modelos.py). Código MIT, modelo Apache 2.0.

Uso:
  python kokoro.py [pasta de saída, padrão r3]
"""
import re
import sys
import time
from pathlib import Path

from kokoro_onnx import Kokoro

from audio import gravar
from normalizar import normalizar

AQUI = Path(__file__).parent
# Medido nos fonemas do roteiro em 18/10.
CORRECOES = [
    # vogal de apoio depois do "r" antes de consoante: veɾəsˈɐ̃ʊ̃ ("ver-e-são"),
    # sˌeɾəvidˈoɾ, vˈiɾəɡulæ
    (r"ɾə(?=[bdfɡgklmnpstvzʃʒxŋ])", "ɾ"),
]
# "r" é o "r" do inglês no Kokoro; o espeak o usa em "três", "prompt",
# "outubro" e "por". A variante -rr troca pelo "r" batido do português.
BATIDO = [(r"r", "ɾ")]
# nome -> (pesos das vozes, somam 1; troca o "r"?)
VARIANTES = {
    "alex": ({"pm_alex": 1.0}, False),
    "alex-rr": ({"pm_alex": 1.0}, True),
    "dora": ({"pf_dora": 1.0}, False),
    "dora-rr": ({"pf_dora": 1.0}, True),
    "alex-santa": ({"pm_alex": 0.5, "pm_santa": 0.5}, False),
}
VELOCIDADE = 1.0  # ritmo de conversa (pedido do Peter, 18/10)
PAUSA_FRASE = 0.30
PAUSA_VIRGULA = 0.15


def fonemizar(kokoro, texto, batido):
    fonemas = kokoro.tokenizer.phonemize(texto, "pt-br")
    for padrao, troca in CORRECOES + (BATIDO if batido else []):
        fonemas = re.sub(padrao, troca, fonemas)
    return fonemas


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    saida = AQUI / "amostras" / (sys.argv[1] if len(sys.argv) > 1 else "r3")
    saida.mkdir(parents=True, exist_ok=True)
    modelo = AQUI / "modelos" / "kokoro"
    kokoro = Kokoro(str(modelo / "kokoro-v1.0.onnx"),
                    str(modelo / "voices-v1.0.bin"))
    texto = normalizar((AQUI / "rodadas" / "roteiro.txt").read_text(encoding="utf-8"),
                       fonemas=False)
    relatorio = [texto]
    for nome, (pesos, batido) in VARIANTES.items():
        estilo = sum(kokoro.get_voice_style(v) * p for v, p in pesos.items())
        fonemas = fonemizar(kokoro, texto, batido)
        relatorio.append(f"# kokoro-{nome}\n{fonemas}")
        inicio = time.perf_counter()
        audio, taxa = kokoro.create(fonemas, voice=estilo, speed=VELOCIDADE,
                                    lang="pt-br", is_phonemes=True,
                                    sentence_pause=PAUSA_FRASE,
                                    clause_pause=PAUSA_VIRGULA)
        sintese = time.perf_counter() - inicio
        gravar(audio, taxa, saida / f"kokoro-{nome}.wav")
        print(f"kokoro-{nome}\t{sintese:.2f} s de síntese\t"
              f"{len(audio) / taxa:.2f} s de áudio")
    (saida / "fonemas-kokoro.txt").write_text("\n".join(relatorio) + "\n",
                                              encoding="utf-8")


if __name__ == "__main__":
    main()
