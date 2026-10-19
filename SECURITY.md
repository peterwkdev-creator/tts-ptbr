# Segurança

## Como avisar

Falha de segurança não vai em issue pública: use o aviso privado do GitHub,
em [Security → Report a vulnerability](https://github.com/peterwkdev-creator/tts-ptbr/security/advisories/new).
Diga a versão, o passo a passo para reproduzir e o efeito.

## O que esperar

- Primeira resposta em até 14 dias.
- A correção sai na última versão publicada; versões antigas não recebem
  correção.
- Crédito no [CHANGELOG.md](CHANGELOG.md) e no aviso, se você quiser.

## O que não é falha de segurança

Pronúncia errada ou resultado diferente do esperado é issue comum, pelo
modelo "Resultado diferente do esperado".
Escopo: scripts locais, sem servidor e sem chave de API. A rede só se usa
para baixar os modelos (`baixar_modelos.py`, com SHA-256 conferido, e o
Whisper na primeira medida); os scripts gravam arquivos só nas pastas
`modelos/`, `amostras/` e na pasta de saída que você indicar.
