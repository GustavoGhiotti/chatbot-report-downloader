"""Testa o parsing do cabecalho do calendario (PT/EN)."""

import unittest
from datetime import date

from src.infrastructure.voxi.voxi_relatorio_scraper import parse_mes_ano


class TestParseMesAno(unittest.TestCase):
    def test_portugues(self):
        self.assertEqual(parse_mes_ano("agosto de 2026"), date(2026, 8, 1))

    def test_portugues_maiusculas_e_espacos(self):
        self.assertEqual(parse_mes_ano("  Dezembro 2025 "), date(2025, 12, 1))

    def test_ingles(self):
        self.assertEqual(parse_mes_ano("August 2026"), date(2026, 8, 1))

    def test_sem_ano_retorna_none(self):
        self.assertIsNone(parse_mes_ano("agosto"))

    def test_texto_vazio_retorna_none(self):
        self.assertIsNone(parse_mes_ano(""))
        self.assertIsNone(parse_mes_ano(None))


if __name__ == "__main__":
    unittest.main()
