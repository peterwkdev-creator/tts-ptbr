"""Exemplo 5: 6 vozes abertas leem a mesma frase, e o Whisper mede cada uma.

Origem: a medida do post 4 ("6 vozes abertas"), feita em 19/10/2026 com a
versão r10 do normalizar.py e do dicionário; o resultado daquele dia está em
exemplos/vozes_medidas.tsv.

  alex, dora  Kokoro-82M pelo narrar.py, com a nossa calibração (dicionário,
              fonemas e ritmo)
  santa       Kokoro-82M puro (voz pm_santa)
  cadu, faber, jeff  Piper puro (pt_BR-<voz>-medium)

As 4 sem calibração recebem a frase pelo normalizar.py sem dicionário
(dicionario=[]): números e siglas por extenso, nenhuma pronúncia nossa.

Cada etapa roda no ambiente que tem a biblioteca dela (os três
requirements*.txt não se misturam) e precisa dos modelos
(python baixar_modelos.py) e do ffmpeg no PATH:

  python exemplos/05_vozes.py kokoro   requirements.txt
  python exemplos/05_vozes.py piper    requirements-piper.txt
  python exemplos/05_vozes.py medir    requirements-medir.txt (Whisper small)

Grava em saida/vozes/ (fora do git): <voz>.wav e medidas.tsv, com voz,
calibrada, duração em segundos, WER e a transcrição do Whisper.
"""
import subprocess
import sys
import wave
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
SAIDA = RAIZ / "saida" / "vozes"
sys.path.insert(0, str(RAIZ))

# Curta de propósito: 6 vozes cabem num vídeo de 30 a 45 s.
FRASE = "Medi no Claude Code: 96% dos tokens são releitura."
CALIBRADAS = ["alex", "dora"]
KOKORO_PURO = {"santa": "pm_santa"}
PIPER = ["cadu", "faber", "jeff"]
ORDEM = CALIBRADAS + list(KOKORO_PURO) + PIPER
CABECALHO = "voz\tcalibrada\tduracao_s\twer\ttranscricao"


def linha_tsv(voz, duracao, transcricao):
    """Uma linha do medidas.tsv; o WER é da transcrição contra a FRASE.

    Não precisa de modelo: palavras() e wer() são do medir.py, sem Whisper.
    """
    from medir import palavras, wer

    erro = wer(palavras(FRASE), palavras(transcricao))
    calibrada = "sim" if voz in CALIBRADAS else "não"
    return f"{voz}\t{calibrada}\t{duracao:.2f}\t{erro:.3f}\t{transcricao}"


def kokoro():
    from kokoro_onnx import Kokoro

    from audio import gravar
    from normalizar import normalizar

    for voz in CALIBRADAS:
        pasta = SAIDA / f"_{voz}"
        pasta.mkdir(parents=True, exist_ok=True)
        roteiro = pasta / "narracao.txt"
        roteiro.write_text(f"1 | {FRASE}\n", encoding="utf-8")
        subprocess.run([sys.executable, str(RAIZ / "narrar.py"), str(roteiro),
                        str(pasta), voz], check=True)
        (pasta / "voz.wav").replace(SAIDA / f"{voz}.wav")
    modelo = Kokoro(str(RAIZ / "modelos" / "kokoro" / "kokoro-v1.0.onnx"),
                    str(RAIZ / "modelos" / "kokoro" / "voices-v1.0.bin"))
    texto = normalizar(FRASE, dicionario=[], fonemas=False)
    for nome, voz in KOKORO_PURO.items():
        audio, taxa = modelo.create(texto, voice=voz, speed=1.0, lang="pt-br")
        gravar(audio, taxa, SAIDA / f"{nome}.wav")


def piper():
    import numpy as np
    from piper import PiperVoice

    from audio import gravar
    from normalizar import normalizar

    texto = normalizar(FRASE, dicionario=[], fonemas=True)
    for nome in PIPER:
        voz = PiperVoice.load(str(RAIZ / "modelos" / f"pt_BR-{nome}-medium.onnx"))
        bruto = SAIDA / f"_{nome}.wav"
        with wave.open(str(bruto), "wb") as wav:
            voz.synthesize_wav(texto, wav)
        with wave.open(str(bruto), "rb") as wav:
            taxa = wav.getframerate()
            amostras = np.frombuffer(wav.readframes(wav.getnframes()),
                                     dtype=np.int16)
        gravar(amostras.astype(np.float32) / 32768, taxa, SAIDA / f"{nome}.wav")
        bruto.unlink()


def medir():
    from faster_whisper import WhisperModel

    from medir import ler

    modelo = WhisperModel("small", device="cpu", compute_type="int8",
                          download_root=str(RAIZ / "modelos" / "whisper"))
    linhas = [CABECALHO]
    for voz in ORDEM:
        wav = SAIDA / f"{voz}.wav"
        with wave.open(str(wav)) as w:
            duracao = w.getnframes() / w.getframerate()
        trechos, _ = modelo.transcribe(ler(wav), language="pt", beam_size=5)
        texto = "".join(t.text for t in trechos).strip()
        linhas.append(linha_tsv(voz, duracao, texto))
        print(linhas[-1])
    (SAIDA / "medidas.tsv").write_text("\n".join(linhas) + "\n",
                                       encoding="utf-8")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")  # o uso sai por aqui
    etapas = {"kokoro": kokoro, "piper": piper, "medir": medir}
    if len(sys.argv) != 2 or sys.argv[1] not in etapas:
        sys.exit(__doc__)
    SAIDA.mkdir(parents=True, exist_ok=True)
    etapas[sys.argv[1]]()
