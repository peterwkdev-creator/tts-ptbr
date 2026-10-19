# Como contribuir

Pronúncia errada ou resultado inesperado: abra uma issue pelo modelo
"Resultado diferente do esperado". Termo que falta no dicionário, ideia ou
dúvida: pelo modelo "Sugestão ou dúvida". Para mandar código:

- Os testes rodam do checkout, sem modelo baixado e sem instalar nada:

  ```bash
  python -m unittest
  ```

- O normalizador (`normalizar.py`) usa só a biblioteca padrão; mantenha assim.
- Mudança de pronúncia ou de prosódia vem com a medida: o WER do `medir.py`
  antes e depois, e a frase ouvida. Não pode piorar o WER.
- Todo caso novo do normalizador entra em `CASOS` (`normalizar.py`), com o
  resultado esperado escrito à mão; termo novo vai no `dicionario.tsv`.
- Exemplos e testes só com textos inventados: nada de dado real de pessoa
  ou de empresa.
- Código, mensagens e documentação em português do Brasil.
- Mudança de comportamento entra no [CHANGELOG.md](CHANGELOG.md).
- Código próprio: não traga código copiado de outro projeto, mesmo de
  licença livre. O que você contribui sai sob a [licença MIT](LICENSE) do
  projeto.
