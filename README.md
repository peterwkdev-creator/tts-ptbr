# tts-ptbr

Voz em português do Brasil feita de modelos abertos e de uma camada própria:
o texto é escrito do jeito que se fala, narrado frase a frase pelo
Kokoro-82M, acabado a -16 LUFS e medido pelo Whisper. É o TTS que narra os
vídeos do perfil peterwk.dev ("IA testada de verdade, com prova na tela e
data").

> **Versão inicial, aberta a melhorias.** Roda em CPU, no Windows e no
> Linux, e foi calibrada de ouvido e pela medida em textos curtos de
> tecnologia. Medido em 18/10/2026: o `exemplos/narracao.txt` (3 linhas)
> virou 15,7 s de áudio, e o Whisper o transcreveu com WER de 0,133; o erro
> que sobra está à vista, como "Claude Code" ouvido como "Cloud Code". A voz
> é sintética: rotule como IA o que publicar com ela.

## Instalar

Precisa do Python 3.12 (o normalizador e os testes rodam do 3.11 ao 3.14) e
do [ffmpeg](https://ffmpeg.org/download.html) no PATH. Num ambiente virtual,
um comando instala as dependências e baixa o modelo (cerca de 354 MB, com o
SHA-256 conferido):

```bash
python -m pip install -r requirements.txt && python baixar_modelos.py
```

## Uso

Normalizar um texto não precisa de modelo nem de dependência:

```python
from normalizar import normalizar

print(normalizar("A API v2.1 custou R$ 1.299,90 em 18/10/2026.", fonemas=False))
# A á pê i versão dois ponto um, custou mil duzentos e noventa e nove reais
# e noventa centavos em dezoito de outubro de dois mil e vinte e seis.
```

Narrar um arquivo com uma frase por linha (`slide | frase`) grava `voz.wav`
e `tempos.json`, com o início e o fim de cada frase:

```bash
python narrar.py exemplos/narracao.txt saida/meu-post alex
```

## Por quê

Os modelos abertos de voz em português tropeçam no que mais aparece em
texto de tecnologia: "v2.1.299", "R$ 1.299,90", "18/10", "96%", "API",
"prompt". Trocar de modelo não resolve, porque o erro está antes dele, no
texto. Por isso a camada de texto é própria e vale para qualquer motor
(aqui, o Kokoro e o Piper), e cada ajuste se mede: o Whisper transcreve o
áudio e o WER diz se a mudança ajudou ou piorou, além do ouvido.

## O que cobre

| Arquivo | O que faz |
|---|---|
| `normalizar.py` | Escreve por extenso dinheiro (`R$ 1.299,90`), data (`18/10/2026`, `1/3`), versão (`v2.1.299`), porcentagem, números até 999.999.999 com decimais e siglas de 2 a 5 maiúsculas (soletradas); acentua a tônica do "-ia" sem acento ("valeria" → "valería"); aplica o dicionário. |
| `dicionario.tsv` | Pronúncia dos termos em inglês (Claude Code, prompt, token, deploy, cache...): grafia para o Kokoro e, opcional, fonemas para o Piper. |
| `kokoro.py` | Vozes (`alex`, `alex-rr`, `dora`, `dora-rr`, `alex-santa`), fonemização pelo espeak e as correções de fonemas. |
| `prosodia.py` | Uma frase por lote, pausas pela pontuação, ritmo que varia por frase, fim mais lento e os ajustes de tônica e de vogal. |
| `narrar.py` | Narração de um texto com o método aprovado; grava `voz.wav` e `tempos.json`. |
| `audio.py` | Passa-alta de 70 Hz, de-esser, equalização de voz e loudnorm a -16 LUFS, pico -1,5 dBTP, em duas passadas. |
| `medir.py` | WER e vãos entre palavras pelo Whisper. |
| `baixar_modelos.py` | Baixa o modelo e as vozes da fonte oficial, com o SHA-256. |
| `rodadas/` | Os scripts das rodadas de calibração (Piper e Kokoro) e o roteiro fixo delas. |

Não cobre: horas (`10h30`), ordinais, telefone, número no feminino ("2
pessoas" sai "dois pessoas"), números acima de 999.999.999, versão sem o "v" ("2.1" sai "dois um"; por
isso a transcrição "versão 2.1.299" do Whisper soma erro ao WER) e inglês
fora do dicionário.

## Como é testado

```bash
python -m unittest
```

São 21 testes, que rodam do checkout sem modelo baixado e sem instalar
nada: os casos do normalizador (`normalizar.CASOS`, também em
`python normalizar.py --teste`), o dicionário, o WER, os exemplos 1 e 2 e os
blocos Python deste README. O GitHub Actions os roda a cada push, do Python
3.11 ao 3.14 e no Windows. A síntese e a transcrição precisam dos modelos e
se conferem pela medida: `medir.py` e o exemplo 4. Uma mudança de pronúncia
só entra se ganhar a escuta às cegas sem piorar o WER.

## Mais exemplos

| Exemplo | Precisa de |
|---|---|
| `python exemplos/01_normalizar.py`: número, sigla, versão, data e dinheiro numa frase | nada |
| `python exemplos/02_dicionario_proprio.py`: somar o seu `.tsv` ao do projeto | nada |
| `python exemplos/03_narrar.py [voz]`: narra o `exemplos/narracao.txt` em `saida/exemplo/` | `requirements.txt`, modelo, ffmpeg |
| `python exemplos/04_medir_wav.py [wav] [texto]`: WER e vãos do áudio do exemplo 3 | `requirements-medir.txt`, ffmpeg |

Dicionário próprio, no mesmo formato do `dicionario.tsv`
(`termo<TAB>grafia`):

```python
from pathlib import Path
from normalizar import carregar_dicionario, normalizar

meu = carregar_dicionario(Path("exemplos/meu_dicionario.tsv"), fonemas=False)
padrao = carregar_dicionario(fonemas=False)
dicionario = sorted(meu + padrao, key=lambda par: -len(par[0]))
print(normalizar("Subi o Python num Docker.", dicionario))
# Subi o Páiton num Dóquer.
```

O WER sem o Whisper, de duas listas de palavras:

```python
from medir import palavras, wer

print(wer(palavras("Custou R$ 2,00."), palavras("custou dois reais")))
# 0.0
```

## Fontes, licenças dos modelos e limites

| Componente | Fonte | Licença |
|---|---|---|
| Kokoro-82M (modelo) | [hexgrad/Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M) | Apache 2.0 |
| kokoro-onnx (código); o `kokoro-v1.0.onnx` e o `voices-v1.0.bin` da release `model-files-v1.0` são conversões do Kokoro-82M | [thewh1teagle/kokoro-onnx](https://github.com/thewh1teagle/kokoro-onnx) | MIT (código), Apache 2.0 (modelo e vozes) |
| Vozes pt_BR do Piper (faber, cadu, jeff), só nas rodadas | [rhasspy/piper-voices](https://huggingface.co/rhasspy/piper-voices), tag `v1.0.0` | CC0 |
| faster-whisper e o modelo `Systran/faster-whisper-small` | [SYSTRAN/faster-whisper](https://github.com/SYSTRAN/faster-whisper) | MIT |

O pip instala também o phonemizer e o espeak-ng (pelo `espeakng-loader`),
e o ambiente das rodadas, o `piper-tts`: os três sob GPL-3.0. Este
repositório não os inclui nem os modifica; quem distribui um pacote com eles
segue a licença deles. Modelos e áudio não entram no repositório: o
`baixar_modelos.py` os traz da fonte.

Limites: a voz não clona ninguém e não imita pessoa real; a pronúncia de
inglês depende do dicionário; o WER do Whisper mede a inteligibilidade, não
a naturalidade, que se confere de ouvido; os ajustes de prosódia foram
calibrados com as vozes `alex` e `dora` e podem não valer para outras.

## Pastas

```
normalizar.py, dicionario.tsv   texto -> fala (sem dependência)
kokoro.py, prosodia.py          síntese no Kokoro e prosódia frase a frase
narrar.py, audio.py             narração e acabamento a -16 LUFS
medir.py                        WER e vãos pelo Whisper
baixar_modelos.py               modelo e vozes, com SHA-256
requirements*.txt               narração, medida e Piper, cada um no seu ambiente
exemplos/                       os 4 exemplos e os arquivos deles
rodadas/                        calibração: gerar.py e refinar.py (Piper), calibrar.py (Kokoro), roteiro.txt
tests/                          unittest, sem modelo
modelos/, amostras/, saida/     gerados, fora do git
```

## Contribuir

Issue, sugestão de termo para o dicionário e pull request são bem-vindos:
veja o [CONTRIBUTING.md](CONTRIBUTING.md) e o
[código de conduta](CODE_OF_CONDUCT.md). Falha de segurança vai pelo aviso
privado ([SECURITY.md](SECURITY.md)).

<!-- outros-projetos:inicio -->
## Outros projetos

| Projeto | Para que serve |
|---|---|
| [numeros-publicos](https://github.com/peterwkdev-creator/numeros-publicos) · [site](https://www.numerospublicos.com.br) | Dados abertos de cada município brasileiro (IBGE, Tesouro Nacional, INEP), conferidos contra a fonte, uma página por município |
| [simples-nacional-br](https://github.com/peterwkdev-creator/simples-nacional-br) · [site](https://peterwkdev-creator.github.io/simples-nacional-br/) | Simples Nacional conferido contra a LC 123 e a LC 214: alíquota, DAS, repartição, Fator R e CNAE |
| [linguagem-simples-br](https://github.com/peterwkdev-creator/linguagem-simples-br) · [site](https://peterwkdev-creator.github.io/linguagem-simples-br/) | Verificador aberto da Lei 15.263/2025 (Linguagem Simples): confere um texto contra o art. 5º |
| [claude-context-cost](https://github.com/peterwkdev-creator/claude-context-cost) · [site](https://peterwkdev-creator.github.io/claude-context-cost/) | Quanto cada fonte (CLAUDE.md, regras, skills, memória) custa no contexto de uma sessão do Claude Code |
| [vra-anac](https://github.com/peterwkdev-creator/vra-anac) | Pontualidade dos voos domésticos do Brasil pelo VRA da ANAC |
| [carrossel-terminal](https://github.com/peterwkdev-creator/carrossel-terminal) | Carrossel do Instagram no visual de terminal: Markdown vira PNG, conferido antes de publicar, e o post vira Reel |
| [numerasheets-site](https://github.com/peterwkdev-creator/numerasheets-site) · [site](https://numerasheets.com) | Vitrine da loja NumeraSheets: modelos de planilha e calculadoras grátis |
<!-- outros-projetos:fim -->

## Licença

O código é [MIT](LICENSE). Os modelos e as vozes seguem a licença de cada
fonte, na tabela acima.
