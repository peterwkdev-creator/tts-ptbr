"""O README: os blocos de código Python rodam como estão, sem modelo baixado."""
import contextlib
import io
import re
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
README = RAIZ / "README.md"
# bloco que precisa de modelo leva este comentário e não roda aqui
COM_MODELO = "# precisa do modelo"


class TestExemplosDoReadme(unittest.TestCase):

    def test_blocos_python_rodam(self):
        blocos = re.findall(r"```python\n(.*?)```",
                            README.read_text(encoding="utf-8"), re.S)
        rodam = [b for b in blocos if COM_MODELO not in b]
        self.assertGreaterEqual(len(rodam), 1)
        sys.path.insert(0, str(RAIZ))
        for i, bloco in enumerate(rodam, 1):
            # a saída esperada fica em comentário; o print não sai no meio
            # dos testes
            with self.subTest(bloco=i), contextlib.redirect_stdout(io.StringIO()):
                exec(compile(bloco, f"README, bloco {i}", "exec"), {})


if __name__ == "__main__":
    unittest.main()
