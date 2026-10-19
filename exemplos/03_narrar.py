"""Exemplo 3: narrar um texto curto num WAV, com o tempo de cada frase.

Precisa do requirements.txt instalado, do modelo baixado
(python baixar_modelos.py) e do ffmpeg no PATH. Grava em saida/exemplo/:
voz.wav (-16 LUFS) e tempos.json (início e fim de cada frase, em segundos).

  python exemplos/03_narrar.py [voz]      voz: alex (padrão), dora, alex-rr...
"""
import json
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SAIDA = RAIZ / "saida" / "exemplo"

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    voz = sys.argv[1] if len(sys.argv) > 1 else "alex"
    # a mesma linha de comando que um script de vídeo usaria
    subprocess.run([sys.executable, "narrar.py", "exemplos/narracao.txt",
                    str(SAIDA), voz], cwd=RAIZ, check=True)
    tempos = json.loads((SAIDA / "tempos.json").read_text(encoding="utf-8"))
    print(f"{tempos['versao']}, voz {tempos['voz']}, {tempos['duracao']} s")
    for frase in tempos["frases"]:
        print(f"  slide {frase['slide']}: {frase['inicio']:6.2f} a "
              f"{frase['fim']:6.2f} s  {frase['texto']}")
