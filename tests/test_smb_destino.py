"""Testa a montagem do caminho de destino no SMB (sem IO de rede)."""

import unittest

from src.infrastructure.smb.smb_destino import SmbDestino


class TestSmbDestino(unittest.TestCase):
    def _destino(self, share_path):
        return SmbDestino(
            servidor="10.0.0.72", usuario="u", senha="p", share_path=share_path
        )

    def test_caminho_destino_basico(self):
        d = self._destino(r"\\10.0.0.72\Automacao\RELATORIOS_CAMPANHAS_CHATBOT")
        self.assertEqual(
            d._caminho_destino("relatorio.xlsx"),
            r"\\10.0.0.72\Automacao\RELATORIOS_CAMPANHAS_CHATBOT\relatorio.xlsx",
        )

    def test_share_path_com_barra_final_e_normalizado(self):
        d = self._destino(r"\\10.0.0.72\Automacao\RELATORIOS_CAMPANHAS_CHATBOT\\")
        self.assertEqual(
            d._caminho_destino("a.xlsx"),
            r"\\10.0.0.72\Automacao\RELATORIOS_CAMPANHAS_CHATBOT\a.xlsx",
        )


if __name__ == "__main__":
    unittest.main()
