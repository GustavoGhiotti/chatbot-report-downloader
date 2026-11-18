"""Testa o parser booleano usado na leitura do .env."""

import unittest

from src.shared.utils.env_load import _bool


class TestEnvBool(unittest.TestCase):
    def test_verdadeiros(self):
        for valor in ("1", "true", "TRUE", "Yes", "sim", " y "):
            self.assertTrue(_bool(valor), valor)

    def test_falsos(self):
        for valor in ("0", "false", "nao", "no", "", "qualquer"):
            self.assertFalse(_bool(valor), valor)

    def test_none_usa_padrao(self):
        self.assertTrue(_bool(None, padrao=True))
        self.assertFalse(_bool(None, padrao=False))


if __name__ == "__main__":
    unittest.main()
