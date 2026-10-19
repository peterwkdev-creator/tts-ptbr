"""Rodadas 8 a 10: o roteiro inteiro gerado frase a frase no Kokoro.

Até a r7 o roteiro ia de uma vez ao kokoro.create(), que corta os fonemas em
lotes de até 510 e deixa o modelo cuidar das pausas dentro do lote. O card do
Kokoro (VOICES.md) diz que ele rende melhor com 100 a 200 tokens por lote:
abaixo de ~10 a 20 a fala sai fraca, acima de ~400 sai corrida. Aqui cada
frase é um lote e as pausas são nossas.

Régua em degraus: cada variante soma uma mudança à anterior (guia em
amostras/<rodada>/fonemas.txt; medida em medir.py).
r8 (lotes):
  1-regua     o método da r7 (roteiro de uma vez)
  2-frases    uma frase por lote, pausa nossa pela pontuação final
  3-juntas    frase curta (< CURTA caracteres) vai junto com a anterior
  4-oracoes   corta também em ":" e ";", com pausa de oração
  5-ritmo     velocidade varia por lote, 0,97 a 1,03 (hipótese, sem fonte)
r9 (sobre o 3-juntas, o que o Peter preferiu):
  1-regua     o 3-juntas da r8
  2-secundaria  tira o acento secundário de palavra que já tem o primário
                (dˌuzˈeɪŋtʊz): o valor do plano saía picotado (Peter, 18/10)
  3-esta      palavra só com secundário vira primário ("estˌa" -> "estˈa")
  4-vogal     "a" átono final: æ -> ɐ (kˈadæ -> kˈadɐ)
  5-acabamento  4 + de-esser e equalização (audio.py, ACABAMENTO)
r10 (sobre o 5-acabamento da r9, o que o Peter aprovou; todos com acabamento):
  1-regua     o 5-acabamento da r9
  2-siglas    sigla soletrada vira uma palavra só, tônica na última letra
              ("ˈa pˈe ˈi" -> "ˌa pˌe ˈi"): o Whisper ouvia "ap"
  3-atono     "a" átono que sobrou como æ vira a ("ʃæmˈeɪ" -> "ʃamˈeɪ")
  4-ritmo     velocidade por lote como no 5-ritmo da r8 (Peter gostou)
  5-final     último lote mais lento (FINAL): alongamento de fim de fala
  6-respiro   inspiração sintética antes de cada lote depois do 1º
              (respiro(); hipótese: ruído filtrado, não a mesma voz)

Uso:
  python prosodia.py [rodada, padrão r10] [voz ...]
"""
import re
import sys
from pathlib import Path

import numpy as np
from kokoro_onnx import Kokoro

from audio import gravar
from kokoro import PAUSA_FRASE, PAUSA_VIRGULA, VARIANTES, VELOCIDADE, fonemizar
from normalizar import normalizar

AQUI = Path(__file__).parent
# segundos de silêncio depois do lote, pela pontuação final
PAUSA = {".": 0.45, "?": 0.60, "!": 0.50, ":": 0.25, ";": 0.25}
# caracteres do texto; juntam "Liguei um servidor…" (58) e "A resposta…"
# (34), e os lotes ficam entre 157 e 225 fonemas (r8, 18/10)
CURTA = 60
RITMO = [1.0, 0.97, 1.03, 0.99, 1.02]
FINAL = 0.95  # velocidade do último lote (r10)
# respiro (r10): inspirações de 300 a 600 ms (Elmers et al. 2021);
# silêncio antes e vão até a fala, em segundos
RESPIRO, ANTES, VAO = 0.35, 0.15, 0.08
NIVEL = 0.08  # pico do respiro sobre o pico da fala (~-22 dB; hipótese)
SIGLAS = [("ˈemy sˈe pˈe", "ˌemy sˌe pˈe"), ("ˈa pˈe ˈi", "ˌa pˌe ˈi")]


def _secundaria(fonemas):
    return re.sub(r"\S+", lambda m: m[0].replace("ˌ", "") if "ˈ" in m[0]
                  else m[0], fonemas)


def _isolada(fonemas):
    return re.sub(r"\S+", lambda m: m[0].replace("ˌ", "ˈ") if "ˈ" not in m[0]
                  else m[0], fonemas)


def _vogal(fonemas):
    return re.sub(r"æ(?=[\s,.?!:;]|$)", "ɐ", fonemas)


def _siglas(fonemas):
    for antes, depois in SIGLAS:
        fonemas = fonemas.replace(antes, depois)
    return fonemas


def _atono(fonemas):
    return fonemas.replace("æ", "a")


def respiro(fala, taxa):
    """Inspiração sintética: ruído de 400 a 2.500 Hz que cresce e corta."""
    n = int(taxa * RESPIRO)
    espectro = np.fft.rfft(np.random.default_rng(10).standard_normal(n))
    freq = np.fft.rfftfreq(n, 1 / taxa)
    espectro[(freq < 400) | (freq > 2500)] = 0
    ruido = np.fft.irfft(espectro, n)
    t = np.linspace(0, 1, n)
    ruido *= np.minimum(t / 0.7, (1 - t) / 0.3) ** 2
    return (ruido / np.abs(ruido).max() * NIVEL
            * np.abs(fala).max()).astype(fala.dtype)


SEC, ISO, VOG, SIG, ATO = _secundaria, _isolada, _vogal, _siglas, _atono
R9 = [SEC, ISO, VOG]
# rodada -> [(nome, degrau dos lotes, ajustes de fonemas, acabamento, *extras)]
RODADAS = {
    "r8": [("1-regua", 1, [], False), ("2-frases", 2, [], False),
           ("3-juntas", 3, [], False), ("4-oracoes", 4, [], False),
           ("5-ritmo", 5, [], False)],
    "r9": [("1-regua", 3, [], False), ("2-secundaria", 3, [SEC], False),
           ("3-esta", 3, [SEC, ISO], False), ("4-vogal", 3, [SEC, ISO, VOG], False),
           ("5-acabamento", 3, [SEC, ISO, VOG], True)],
    "r10": [("1-regua", 3, R9, True), ("2-siglas", 3, R9 + [SIG], True),
            ("3-atono", 3, R9 + [SIG, ATO], True),
            ("4-ritmo", 3, R9 + [SIG, ATO], True, "ritmo"),
            ("5-final", 3, R9 + [SIG, ATO], True, "ritmo", "final"),
            ("6-respiro", 3, R9 + [SIG, ATO], True, "ritmo", "final",
             "respiro")],
}


def lotes(texto, degrau):
    """Corta o texto em lotes conforme o degrau da régua."""
    corte = r"(?<=[.!?])\s+" if degrau < 4 else r"(?<=[.!?:;])\s+"
    partes = [p for p in re.split(corte, texto.strip()) if p]
    if degrau < 3:
        return partes
    juntas = []
    for p in partes:
        # só frase inteira curta se junta; oração curta ("…o histórico:")
        # fica sozinha, senão o degrau 4 não corta nada
        if juntas and len(p) < CURTA and p[-1] in ".!?":
            juntas[-1] += " " + p
        else:
            juntas.append(p)
    return juntas


def sintetizar(kokoro, texto, estilo, batido, degrau, ajustes, extras=()):
    """Devolve (áudio, taxa, linhas do guia) para um degrau da régua."""
    def fonemas_de(t):
        f = fonemizar(kokoro, t, batido)
        for ajuste in ajustes:
            f = ajuste(f)
        return f
    if degrau == 1:
        fonemas = fonemas_de(texto)
        audio, taxa = kokoro.create(fonemas, voice=estilo, speed=VELOCIDADE,
                                    lang="pt-br", is_phonemes=True,
                                    sentence_pause=PAUSA_FRASE,
                                    clause_pause=PAUSA_VIRGULA)
        return audio, taxa, [f"[{len(fonemas)} fon.] {fonemas}"]
    partes, guia, taxa = [], [], 24000
    grupos = lotes(texto, degrau)
    for i, lote in enumerate(grupos):
        fonemas = fonemas_de(lote)
        ultimo = i == len(grupos) - 1
        velocidade = VELOCIDADE
        if degrau >= 5 or "ritmo" in extras:
            velocidade = RITMO[i % len(RITMO)]
        if "final" in extras and ultimo:
            velocidade = FINAL
        audio, taxa = kokoro.create(fonemas, voice=estilo, speed=velocidade,
                                    lang="pt-br", is_phonemes=True,
                                    sentence_pause=0, clause_pause=PAUSA_VIRGULA)
        pausa = PAUSA.get(lote.rstrip()[-1], PAUSA["."])
        if "respiro" in extras and not ultimo:
            # a pausa vira silêncio curto + inspiração + vão até a fala
            partes += [audio, np.zeros(int(taxa * ANTES), dtype=audio.dtype),
                       respiro(audio, taxa),
                       np.zeros(int(taxa * VAO), dtype=audio.dtype)]
            pausa = f"{ANTES} + respiro {RESPIRO} + {VAO}"
        else:
            partes += [audio, np.zeros(int(taxa * pausa), dtype=audio.dtype)]
        guia.append(f"[{len(fonemas)} fon., speed {velocidade}, "
                    f"pausa {pausa}] {fonemas}")
    return np.concatenate(partes[:-1]), taxa, guia


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    args = sys.argv[1:]
    rodada = args.pop(0) if args and re.fullmatch(r"r\d+", args[0]) else "r10"
    saida = AQUI / "amostras" / rodada
    saida.mkdir(parents=True, exist_ok=True)
    modelo = AQUI / "modelos" / "kokoro"
    kokoro = Kokoro(str(modelo / "kokoro-v1.0.onnx"),
                    str(modelo / "voices-v1.0.bin"))
    texto = normalizar((AQUI / "rodadas" / "roteiro.txt").read_text(encoding="utf-8"),
                       fonemas=False)
    guia = [__doc__.split("Uso")[0].strip(), "", texto]
    for nome in args or ["alex"]:
        pesos, batido = VARIANTES[nome]
        estilo = sum(kokoro.get_voice_style(v) * p for v, p in pesos.items())
        for rotulo, degrau, ajustes, acabamento, *extras in RODADAS[rodada]:
            audio, taxa, linhas = sintetizar(kokoro, texto, estilo, batido,
                                             degrau, ajustes, extras)
            gravar(audio, taxa, saida / f"{nome}-{rotulo}.wav", acabamento)
            print(f"{nome}-{rotulo}\t{len(linhas)} lotes\t"
                  f"{len(audio) / taxa:.2f} s")
            guia += ["", f"# {nome}-{rotulo} ({len(audio) / taxa:.2f} s)"] + linhas
    (saida / "fonemas.txt").write_text("\n".join(guia) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
