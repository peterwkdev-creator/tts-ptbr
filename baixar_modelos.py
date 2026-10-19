"""Baixa o modelo e as vozes para modelos/, da fonte oficial, conferindo o SHA-256.

  - Kokoro-82M (Apache 2.0), na versão ONNX do kokoro-onnx: release
    model-files-v1.0 de github.com/thewh1teagle/kokoro-onnx. A release não
    publica hash; o SHA-256 abaixo é o do arquivo que baixamos e usamos.
  - Vozes pt_BR do Piper (com --piper; só as rodadas usam): huggingface.co/
    rhasspy/piper-voices, tag v1.0.0. O SHA-256 do .onnx é o que o Hugging
    Face publica (cabeçalho X-Linked-ETag do LFS); o do .onnx.json, o nosso.
  - O Whisper (medir.py) não passa por aqui: o faster-whisper baixa o
    Systran/faster-whisper-small sozinho na primeira medida.

Arquivo que já existe com o hash certo não se baixa de novo; hash errado
apaga o download e para com erro.

Uso:
  python baixar_modelos.py            só o Kokoro (o que narrar.py usa)
  python baixar_modelos.py --piper    o Kokoro e as vozes do Piper
"""
import hashlib
import sys
import urllib.request
from pathlib import Path

MODELOS = Path(__file__).parent / "modelos"
KOKORO = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/"
PIPER = "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/pt/pt_BR/"

# destino em modelos/ -> (URL, SHA-256)
ARQUIVOS = {
    "kokoro/kokoro-v1.0.onnx": (
        KOKORO + "kokoro-v1.0.onnx",
        "7d5df8ecf7d4b1878015a32686053fd0eebe2bc377234608764cc0ef3636a6c5"),
    "kokoro/voices-v1.0.bin": (
        KOKORO + "voices-v1.0.bin",
        "bca610b8308e8d99f32e6fe4197e7ec01679264efed0cac9140fe9c29f1fbf7d"),
}
VOZES_PIPER = {
    "faber": ("858555e3a064209c57088fe6bd70c4c3dc54d03eaa00c45d5ecaf43a33f95aa7",
              "7e694de195ae3fc36dd732c445eb04fb49b649854893cb5506b978f0d50a1d6f"),
    "cadu": ("765f0809a6ea9035d4a6d0d008dbf8876e68b2dd32029312672fa8f405bdb535",
             "5fe03aa3d4901880554905b12075713cd552598c8a350455a1ec73f8b4e6be19"),
    "jeff": ("3a6f4c46355813c2b7bbc4d16b6d13d60ed72074b952a393baace82a7d0c94b5",
             "7bf8145b572b36806f5ce0f1d3322b6711975bc7d0473e8d36fced4a9ec0030d"),
}
for _voz, (_onnx, _json) in VOZES_PIPER.items():
    _nome = f"pt_BR-{_voz}-medium.onnx"
    ARQUIVOS["piper:" + _nome] = (f"{PIPER}{_voz}/medium/{_nome}", _onnx)
    ARQUIVOS["piper:" + _nome + ".json"] = (f"{PIPER}{_voz}/medium/{_nome}.json", _json)


def sha256(caminho):
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def baixar(destino, url, esperado):
    if destino.exists() and sha256(destino) == esperado:
        print(f"já existe: {destino.name}")
        return
    destino.parent.mkdir(parents=True, exist_ok=True)
    parcial = destino.with_name(destino.name + ".parcial")
    print(f"baixando {url}")
    urllib.request.urlretrieve(url, parcial)
    obtido = sha256(parcial)
    if obtido != esperado:
        parcial.unlink()
        sys.exit(f"hash diferente em {destino.name}: {obtido} (esperado {esperado})")
    parcial.replace(destino)
    print(f"ok: {destino.name}")


def main():
    piper = "--piper" in sys.argv[1:]
    for nome, (url, esperado) in ARQUIVOS.items():
        if nome.startswith("piper:"):
            if not piper:
                continue
            nome = nome.removeprefix("piper:")
        baixar(MODELOS / nome, url, esperado)


if __name__ == "__main__":
    main()
