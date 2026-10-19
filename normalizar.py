"""Normalizador PT-BR: escreve por extenso o que o TTS lê mal.

Ordem: dinheiro (R$), data (dd/mm/aaaa), versão (v2.1.299), porcentagem,
números, dicionário de pronúncia (dicionario.tsv) e siglas em maiúsculas.
A camada é nossa e vale para qualquer modelo; o modelo só recebe o texto já
escrito do jeito que se fala.

Uso:
  python normalizar.py texto.txt      imprime o texto normalizado
  python normalizar.py --teste        roda os casos do fim do arquivo
"""
import re
import sys
import unicodedata
from pathlib import Path

UNIDADES = ["zero", "um", "dois", "três", "quatro", "cinco", "seis", "sete",
            "oito", "nove", "dez", "onze", "doze", "treze", "catorze",
            "quinze", "dezesseis", "dezessete", "dezoito", "dezenove"]
DEZENAS = ["", "", "vinte", "trinta", "quarenta", "cinquenta", "sessenta",
           "setenta", "oitenta", "noventa"]
CENTENAS = ["", "cento", "duzentos", "trezentos", "quatrocentos",
            "quinhentos", "seiscentos", "setecentos", "oitocentos",
            "novecentos"]
MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
         "agosto", "setembro", "outubro", "novembro", "dezembro"]
LETRAS = {"A": "á", "B": "bê", "C": "cê", "D": "dê", "E": "é", "F": "éfe",
          "G": "gê", "H": "agá", "I": "i", "J": "jota", "K": "cá", "L": "éle",
          "M": "ême", "N": "êne", "O": "ó", "P": "pê", "Q": "quê", "R": "érre",
          "S": "ésse", "T": "tê", "U": "u", "V": "vê", "W": "dáblio",
          "X": "xis", "Y": "ípsilon", "Z": "zê"}

DICIONARIO = Path(__file__).with_name("dicionario.tsv")


def _ate999(n):
    if n == 100:
        return "cem"
    c, r = divmod(n, 100)
    partes = [CENTENAS[c]] if c else []
    if r:
        if r < 20:
            partes.append(UNIDADES[r])
        else:
            d, u = divmod(r, 10)
            partes.append(DEZENAS[d])
            if u:
                partes.append(UNIDADES[u])
    return " e ".join(partes)


def extenso(n):
    """Inteiro de 0 a 999.999.999 por extenso, no masculino."""
    if n == 0:
        return "zero"
    milhoes, resto = divmod(n, 10**6)
    milhares, resto = divmod(resto, 1000)
    grupos = []
    if milhoes:
        grupos.append((milhoes, "um milhão" if milhoes == 1
                       else _ate999(milhoes) + " milhões"))
    if milhares:
        grupos.append((milhares, "mil" if milhares == 1
                       else _ate999(milhares) + " mil"))
    if resto:
        grupos.append((resto, _ate999(resto)))
    texto = grupos[0][1]
    for i, (valor, palavras) in enumerate(grupos[1:], 1):
        ultimo = i == len(grupos) - 1
        liga = " e " if ultimo and (valor < 100 or valor % 100 == 0) else " "
        texto += liga + palavras
    return texto


def _decimal(inteiro, fracao):
    texto = extenso(int(inteiro.replace(".", "")))
    if fracao is None:
        return texto
    if fracao.startswith("0"):
        lida = " ".join(UNIDADES[int(d)] for d in fracao)
    else:
        lida = extenso(int(fracao))
    return f"{texto} vírgula {lida}"


def _dinheiro(m):
    reais = int(m.group(1).replace(".", ""))
    centavos = int(m.group(2)) if m.group(2) else 0
    partes = []
    if reais:
        unidade = "real" if reais == 1 else "reais"
        if reais % 10**6 == 0:
            unidade = "de reais"
        partes.append(f"{extenso(reais)} {unidade}")
    if centavos:
        partes.append(extenso(centavos) + (" centavo" if centavos == 1
                                           else " centavos"))
    return " e ".join(partes) or "zero real"


def _data(m):
    dia, mes = int(m.group(1)), int(m.group(2))
    if not (1 <= dia <= 31 and 1 <= mes <= 12):
        return m.group(0)
    texto = ("primeiro" if dia == 1 else extenso(dia)) + " de " + MESES[mes - 1]
    if m.group(3):
        texto += " de " + extenso(int(m.group(3)))
    return texto


def _versao(m):
    """Vírgula depois da versão quando a frase segue: sem ela, o último
    número se ligava à palavra seguinte ("nove em" saía nˈɔvj ˈeɪŋ) e soava
    separado (rodada 4, aprovado pelo Peter em 18/10)."""
    texto = "versão " + " ponto ".join(extenso(int(p))
                                       for p in m.group(1).split("."))
    if re.match(r" \w", m.string[m.end():]):
        texto += ","
    return texto


ACENTOS = set("áéíóúâêôãõà")


def _tonica_ia(m):
    """Consoante + "ia(s)/iam" sem acento gráfico é tônica no "i" pela
    ortografia (valeria, seria, padaria; "Valéria" e "história" levam
    acento). O espeak do Kokoro lia "valeria" como o nome (18/10): o acento
    explícito resolve nos dois motores."""
    palavra = m.group(0)
    if palavra.isupper() or ACENTOS & set(palavra.lower()):
        return palavra
    return m.group(1) + "í" + m.group(2)


def carregar_dicionario(caminho=DICIONARIO, fonemas=True):
    """Lê o .tsv em caminho -> [(termo, pronúncia)], o termo mais longo antes.

    fonemas=True usa a 3ª coluna [[...]] quando houver (só o Piper lê)."""
    pares = []
    for linha in caminho.read_text(encoding="utf-8").splitlines():
        if not linha.strip() or linha.startswith("#"):
            continue
        colunas = [c.strip() for c in linha.split("\t")]
        pronuncia = colunas[1]
        if fonemas and len(colunas) > 2:
            # O Piper só conhece o til separado (e + U+0303), como o espeak
            # entrega; "ẽ" pronto dá "Missing phoneme from id map".
            pronuncia = unicodedata.normalize("NFD", colunas[2])
        pares.append((colunas[0], pronuncia))
    pares.sort(key=lambda p: -len(p[0]))  # o mais longo primeiro
    return pares


def normalizar(texto, dicionario=None, fonemas=True):
    """Devolve o texto escrito do jeito que se fala.

    dicionario: pares (termo, pronúncia), como os de carregar_dicionario();
    None carrega o dicionario.tsv; [] não usa nenhum.
    fonemas: True para o Piper (usa a 3ª coluna [[...]] do dicionário);
    False para o Kokoro, que só lê a 2ª coluna.
    """
    if dicionario is None:
        dicionario = carregar_dicionario(fonemas=fonemas)
    texto = re.sub(r"R\$\s?(\d{1,3}(?:\.\d{3})*|\d+)(?:,(\d{2}))?",
                   _dinheiro, texto)
    texto = re.sub(r"\b(\d{1,2})/(\d{1,2})(?:/(\d{4}))?\b", _data, texto)
    texto = re.sub(r"\bv(\d+(?:\.\d+)+)\b", _versao, texto)
    numero = r"(\d{1,3}(?:\.\d{3})+|\d+)(?:,(\d+))?"
    texto = re.sub(numero + r"\s?%",
                   lambda m: _decimal(m.group(1), m.group(2)) + " por cento",
                   texto)
    texto = re.sub(r"\b" + numero + r"\b",
                   lambda m: _decimal(m.group(1), m.group(2)), texto)
    for termo, pronuncia in dicionario:
        texto = re.sub(r"(?<!\w)" + re.escape(termo) + r"(?!\w)", pronuncia,
                       texto, flags=re.IGNORECASE)
    texto = re.sub(r"\b([^\W\d_]*[bcdfgjklmnpqrstvxzç])i(as?|am)\b",
                   _tonica_ia, texto, flags=re.IGNORECASE)
    texto = re.sub(r"\b[A-Z]{2,5}\b",
                   lambda m: " ".join(LETRAS[c] for c in m.group(0)), texto)
    return texto


CASOS = [
    ("R$ 1.299,90", "mil duzentos e noventa e nove reais e noventa centavos"),
    ("R$ 1,00", "um real"),
    ("R$ 0,50", "cinquenta centavos"),
    ("R$ 2.000.000", "dois milhões de reais"),
    ("18/10/2026", "dezoito de outubro de dois mil e vinte e seis"),
    ("1/3", "primeiro de março"),
    ("v2.1.299", "versão dois ponto um ponto duzentos e noventa e nove"),
    ("v2.1 em 18/10", "versão dois ponto um, em dezoito de outubro"),
    ("a v2.1.", "a versão dois ponto um."),
    ("a v2.1, e", "a versão dois ponto um, e"),
    ("96%", "noventa e seis por cento"),
    ("0,3%", "zero vírgula três por cento"),
    ("1.189", "mil cento e oitenta e nove"),
    ("19,1", "dezenove vírgula um"),
    ("100", "cem"),
    ("1050", "mil e cinquenta"),
    ("1200", "mil e duzentos"),
    ("1.200.000", "um milhão e duzentos mil"),
    ("414 mil", "quatrocentos e catorze mil"),
    ("a API", "a á pê i"),  # "í" sozinho o espeak lê "i agudo" (18/10)
    ("valeria a pena", "valería a pena"),
    ("seria e teriam", "sería e teríam"),
    ("Valéria e história", "Valéria e história"),
    ("ideia e meia", "ideia e meia"),
]


def testar():
    vazio = []
    falhas = 0
    for entrada, esperado in CASOS:
        obtido = normalizar(entrada, vazio)
        if obtido != esperado:
            falhas += 1
            print(f"FALHA: {entrada!r} -> {obtido!r} (esperado {esperado!r})")
    print(f"{len(CASOS) - falhas}/{len(CASOS)} casos ok")
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    if sys.argv[1:] == ["--teste"]:
        sys.exit(testar())
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    print(normalizar(Path(sys.argv[1]).read_text(encoding="utf-8")))
