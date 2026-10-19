"""Medida sem depender só do ouvido: o Whisper transcreve cada amostra.

Para cada WAV de amostras/<rodada>/:
  - WER: palavras erradas / palavras do roteiro, com os dois lados passados
    pelo normalizar.py (o Whisper escreve "2.1.299" e "R$"; o roteiro, por
    extenso). Se o Whisper não entende um termo, o ouvinte também tropeça;
  - vãos entre palavras acima de VAO s, com as duas palavras em volta (acha
    pausa onde o texto não pede);
  - duração.
Grava amostras/<rodada>/medidas.tsv. Regra das rodadas: uma mudança só
entra se ganhar o A/B às cegas, de ouvido, sem piorar o WER.

faster-whisper (MIT) e o modelo Systran/faster-whisper-small (MIT), em CPU
int8, baixado sozinho na 1ª vez para modelos/whisper/ (fora do git). O
texto de referência é rodadas/roteiro.txt.

Uso:
  python medir.py <rodada> [arquivo.wav ...]

palavras() e wer() não precisam do Whisper nem do numpy (os testes os
usam sem modelo). Para medir um WAV qualquer: exemplos/04_medir_wav.py.
"""
import re
import subprocess
import sys
import unicodedata
import wave
from pathlib import Path

from normalizar import normalizar

AQUI = Path(__file__).parent
VAO = 0.15  # s; a pausa de vírgula do Kokoro é 0,15


def palavras(texto):
    """Normaliza, tira acento e pontuação: só as palavras, em minúsculas."""
    # sem o dicionário de pronúncia: ele reescreve o termo pelo contexto
    # ("Claude Code" vira "Clôude Côude", mas "Cloud Code" fica), e a palavra
    # que o Whisper acertou contava como erro (achado em 19/10)
    texto = normalizar(texto, dicionario=[], fonemas=False).lower()
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return re.findall(r"[a-z]+", texto)


def ler(wav):
    """WAV -> float32 mono a 16 kHz pelo ffmpeg. O av que o faster-whisper
    1.2.1 puxou não aceita o metadata_errors que ele passa (18/10)."""
    import numpy as np

    bruto = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error",
                            "-i", str(wav), "-f", "f32le", "-ac", "1", "-ar",
                            "16000", "-"], capture_output=True, check=True)
    return np.frombuffer(bruto.stdout, dtype=np.float32)


def wer(ref, hip):
    """Distância de edição entre listas de palavras, dividida por len(ref)."""
    linha = list(range(len(hip) + 1))
    for i, r in enumerate(ref, 1):
        anterior, linha[0] = linha[0], i
        for j, h in enumerate(hip, 1):
            anterior, linha[j] = linha[j], min(linha[j] + 1, linha[j - 1] + 1,
                                               anterior + (r != h))
    return linha[-1] / len(ref)


def main():
    from faster_whisper import WhisperModel

    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    pasta = AQUI / "amostras" / sys.argv[1]
    wavs = [Path(a) for a in sys.argv[2:]] or sorted(pasta.glob("*.wav"))
    ref = palavras((AQUI / "rodadas" / "roteiro.txt").read_text(encoding="utf-8"))
    modelo = WhisperModel("small", device="cpu", compute_type="int8",
                          download_root=str(AQUI / "modelos" / "whisper"))
    linhas = ["amostra\tduracao_s\twer\tvaos\ttranscricao"]
    for wav in wavs:
        with wave.open(str(wav)) as w:
            duracao = w.getnframes() / w.getframerate()
        trechos, _ = modelo.transcribe(ler(wav), language="pt",
                                       word_timestamps=True, beam_size=5)
        ditas = [p for t in trechos for p in t.words]
        texto = "".join(p.word for p in ditas).strip()
        vaos = [f"{a.word.strip()}|{b.word.strip()} {b.start - a.end:.2f}"
                for a, b in zip(ditas, ditas[1:]) if b.start - a.end > VAO]
        erro = wer(ref, palavras(texto))
        linhas.append(f"{wav.stem}\t{duracao:.2f}\t{erro:.3f}\t"
                      f"{'; '.join(vaos)}\t{texto}")
        print(f"{wav.stem}\t{duracao:.2f} s\tWER {erro:.3f}\t"
              f"{len(vaos)} vãos > {VAO} s")
    (pasta / "medidas.tsv").write_text("\n".join(linhas) + "\n",
                                       encoding="utf-8")


if __name__ == "__main__":
    main()
