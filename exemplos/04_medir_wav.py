"""Exemplo 4: medir um WAV pelo Whisper contra o texto que devia ser dito.

Mostra o WER (palavras erradas / palavras do texto, os dois lados
normalizados) e os vãos entre palavras acima de medir.VAO segundos. Precisa
do requirements-medir.txt e do ffmpeg; o modelo do Whisper (small, ~480 MB)
baixa sozinho na primeira vez para modelos/whisper/.

  python exemplos/04_medir_wav.py [arquivo.wav] [texto.txt]

Sem argumentos, mede o saida/exemplo/voz.wav do exemplo 3 contra o
exemplos/narracao.txt.
"""
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
sys.path.insert(0, str(RAIZ))
from medir import VAO, ler, palavras, wer

if __name__ == "__main__":
    from faster_whisper import WhisperModel

    sys.stdout.reconfigure(encoding="utf-8")
    wav = Path(sys.argv[1]) if len(sys.argv) > 1 else RAIZ / "saida" / "exemplo" / "voz.wav"
    fonte = Path(sys.argv[2]) if len(sys.argv) > 2 else AQUI / "narracao.txt"
    linhas = [l for l in fonte.read_text(encoding="utf-8").splitlines()
              if l.strip() and not l.startswith("#")]
    texto = " ".join(l.split("|", 1)[-1].strip() for l in linhas)
    modelo = WhisperModel("small", device="cpu", compute_type="int8",
                          download_root=str(RAIZ / "modelos" / "whisper"))
    trechos, _ = modelo.transcribe(ler(wav), language="pt",
                                   word_timestamps=True, beam_size=5)
    ditas = [p for t in trechos for p in t.words]
    ouvido = "".join(p.word for p in ditas).strip()
    print("texto: ", texto)
    print("ouvido:", ouvido)
    print(f"WER {wer(palavras(texto), palavras(ouvido)):.3f}")
    for a, b in zip(ditas, ditas[1:]):
        if b.start - a.end > VAO:
            print(f"  vão de {b.start - a.end:.2f} s entre "
                  f"{a.word.strip()!r} e {b.word.strip()!r}")
