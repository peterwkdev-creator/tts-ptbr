"""Rodadas 4 a 6: calibram os dois defeitos que o Peter ouviu na rodada 3
(18/10).

Só a 1ª frase do roteiro, com o Kokoro. Cada variante muda uma coisa só
contra a "regua" da rodada, para a comparação ser justa:
  - "Claude Code": o espeak gera klˈɔwd kˈoud de "Clóud Côud", que é o
    "ou" de "cloud"; o inglês é klˈɔːd kˈoʊd (fonemizador en-us do Kokoro).
  - Versão: o "nove" se liga ao "em" seguinte (nˈɔvj ˈeɪŋ) e o último 9 sai
    separado.
Prefira trocar a grafia a escrever fonemas à mão: o Kokoro aprendeu o PT-BR
pelo espeak, que escreve o "e" final átono como `y` (o "de" sai `dʒy`).

O guia de escuta de cada rodada (ordem, o que muda e fonemas) fica em
<rodada>/fonemas.txt.

Uso:
  python rodadas/calibrar.py [rodada: r4, r5 ou r6; padrão r6]
"""
import sys
import time
from pathlib import Path

from kokoro_onnx import Kokoro

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # a raiz
from audio import gravar
from kokoro import AQUI, PAUSA_FRASE, PAUSA_VIRGULA, VELOCIDADE, fonemizar
from normalizar import carregar_dicionario, normalizar

CC_GRAFIA = "Clóud Côud"  # o que o dicionario.tsv dava na rodada 3
CC_ATUAL = "klˈɔwd kˈoud"  # o que o espeak faz dele
NOVE_ATUAL = "nˈɔvj ˈeɪŋ"
VERSAO = "dois ponto um ponto duzentos e noventa e nove"
VIRGULA = (VERSAO, VERSAO + ",")  # o v-virgula, aprovado na rodada 4


def cc(grafia):
    return (CC_GRAFIA, grafia)


# rodada -> nome -> (o que se ouve, trocas no texto, troca nos fonemas)
RODADAS = {
    "r4": {
        "atual": ("régua: a frase da rodada 3", [], None),
        "cc-ingles": ("Claude Code do inglês", [],
                      (CC_ATUAL, "klˈɔːd kˈoʊd")),
        "cc-sem-u": ("o mesmo, Code sem o u final", [],
                     (CC_ATUAL, "klˈɔːd kˈod")),
        "cc-clodi": ("Clódi Códi com i pleno, à mão", [],
                     (CC_ATUAL, "klˈɔdʒi kˈodʒi")),
        "v-virgula": ("vírgula depois da versão", [VIRGULA], None),
        "v-nove-i": ("nove sem ligar ao em", [],
                     (NOVE_ATUAL, "nˈɔvi ˈeɪŋ")),
        "v-digitos": ("dois ponto um ponto dois nove nove",
                      [(VERSAO, "dois ponto um ponto dois nove nove,")],
                      None),
    },
    # O Peter, 18/10: v-virgula e v-nove-i acertam a versão; "Claude Code"
    # soa norte-americano. Pedido: pronúncia brasileira.
    "r5": {
        "atual": ("régua: Clóud Côud", [VIRGULA], None),
        "clode-code": ("Clóde Códe", [VIRGULA, cc("Clóde Códe")], None),
        "clode-code-fechado": ("Clóde Côde",
                               [VIRGULA, cc("Clóde Côde")], None),
        "claude-code-pt": ("Cláudi Códi: a grafia lida em português",
                           [VIRGULA, cc("Claude Code")], None),
        "clode-tudo-fechado": ("Clôde Côde",
                               [VIRGULA, cc("Clôde Côde")], None),
    },
    # O Peter, 18/10: claude-code-pt chegou perto. O "Claude" em português
    # está certo; o "Code" fica em inglês, mas sem o sotaque norte-americano
    # (o oʊ e o d seco). Só o "Code" muda; o "Claude" fica o da régua.
    "r6": {
        "1-regua": ("régua: Cláudi Códi, o claude-code-pt da r5",
                    [VIRGULA, cc("Claude Code")], None),
        "2-coudi": ("Code como Côudi, semivogal w no ditongo",
                    [VIRGULA, cc("Claude Coude")], None),
        "3-coude": ("Code como Côude, u pleno no ditongo",
                    [VIRGULA, cc("Claude Côude")], None),
        "4-codi": ("Code como Côdi, sem ditongo",
                   [VIRGULA, cc("Claude Côde")], None),
        "5-coud": ("Code como Côud, sem vogal no fim",
                   [VIRGULA, cc("Claude Côud")], None),
    },
}
VOZES = {"alex": "pm_alex", "dora": "pf_dora"}


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    rodada = sys.argv[1] if len(sys.argv) > 1 else "r6"
    saida = AQUI / "amostras" / rodada
    saida.mkdir(parents=True, exist_ok=True)
    modelo = AQUI / "modelos" / "kokoro"
    kokoro = Kokoro(str(modelo / "kokoro-v1.0.onnx"),
                    str(modelo / "voices-v1.0.bin"))
    # A base das rodadas é a frase da rodada 3, de antes da calibração: o
    # dicionário com CC_GRAFIA e a versão sem a vírgula que o normalizador
    # passou a pôr. Assim as rodadas continuam reproduzíveis.
    dicionario = [(t, CC_GRAFIA if t == "Claude Code" else p)
                  for t, p in carregar_dicionario(fonemas=False)]
    roteiro = normalizar((AQUI / "rodadas" / "roteiro.txt").read_text(encoding="utf-8"),
                         dicionario, fonemas=False)
    frase = roteiro.split(". ")[0].replace(VERSAO + ",", VERSAO) + "."
    relatorio = [f"Rodada {rodada}, 1ª frase do roteiro, vozes "
                 f"{', '.join(VOZES)}. Ouvir na ordem abaixo.", frase]
    for nome, (descricao, no_texto, nos_fonemas) in RODADAS[rodada].items():
        texto = frase
        for antes, depois in no_texto:
            if antes not in texto:
                sys.exit(f"{nome}: {antes!r} não está em {texto!r}")
            texto = texto.replace(antes, depois)
        fonemas = fonemizar(kokoro, texto, batido=False)
        if nos_fonemas:
            if nos_fonemas[0] not in fonemas:
                sys.exit(f"{nome}: {nos_fonemas[0]!r} não está em {fonemas!r}")
            fonemas = fonemas.replace(*nos_fonemas)
        fora = sorted(set(fonemas) - set(kokoro.tokenizer.vocab))
        if fora:
            sys.exit(f"{nome}: fora do vocabulário do Kokoro: {fora}")
        relatorio.append(f"# {nome}: {descricao}\n{fonemas}")
        for voz, id_voz in VOZES.items():
            inicio = time.perf_counter()
            audio, taxa = kokoro.create(fonemas, voice=id_voz,
                                        speed=VELOCIDADE, lang="pt-br",
                                        is_phonemes=True,
                                        sentence_pause=PAUSA_FRASE,
                                        clause_pause=PAUSA_VIRGULA)
            gravar(audio, taxa, saida / f"{voz}-{nome}.wav")
            print(f"{voz}-{nome}\t{time.perf_counter() - inicio:.2f} s de "
                  f"síntese\t{len(audio) / taxa:.2f} s de áudio")
    (saida / "fonemas.txt").write_text("\n".join(relatorio) + "\n",
                                       encoding="utf-8")


if __name__ == "__main__":
    main()
