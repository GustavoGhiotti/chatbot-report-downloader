"""Testa a logica do registro de execucao (sem conectar no SQL Server real)."""

import unittest
import uuid
from datetime import date, datetime
from unittest import mock

from src.infrastructure.db.log_execucao_repository import (
    STATUS_SUCESSO,
    LogExecucaoRepository,
)

CONFIG = {
    "enabled": True,
    "driver": "SQL SERVER",
    "server": "10.0.0.66",
    "database": "LOGS_ROBOS",
    "user": "u",
    "password": "p",
    "tabela": "TB_LOG_EXECUCAO",
    "nm_cedente": "RoboBulkChatBot",
    "id_cedente": None,
    "id_mapa": None,
}


class _FakeCursor:
    def __init__(self, resultado):
        self._resultado = resultado
        self.executed = []  # lista de (sql, parametros)

    def execute(self, sql, parametros=None):
        self.executed.append((sql, parametros))
        return self

    def fetchone(self):
        return self._resultado


class _FakeConn:
    def __init__(self, cursor):
        self._cursor = cursor
        self.committed = False
        self.rolled_back = False
        self.closed = False

    def cursor(self):
        return self._cursor

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def close(self):
        self.closed = True


def _repo(cursor, config=None):
    repo = LogExecucaoRepository(config=config or dict(CONFIG))
    repo._conectar = lambda: _FakeConn(cursor)  # type: ignore[method-assign]
    return repo


class TestChaveArquivo(unittest.TestCase):
    def test_chave_dia_iso(self):
        self.assertEqual(LogExecucaoRepository._chave_dia(date(2026, 8, 30)), "2026-08-30")

    def test_nome_arquivo_registro_prefixa_a_data(self):
        repo = _repo(_FakeCursor(None))
        nome = repo._nome_arquivo_registro(date(2026, 8, 30), r"C:\tmp\Campanhas.xlsx")
        self.assertEqual(nome, "2026-08-30_Campanhas.xlsx")

    def test_nome_arquivo_registro_sem_arquivo(self):
        repo = _repo(_FakeCursor(None))
        self.assertEqual(repo._nome_arquivo_registro(date(2026, 8, 30), None), "2026-08-30")


class TestJaTransferido(unittest.TestCase):
    def test_retorna_true_quando_ha_sucesso(self):
        cursor = _FakeCursor(resultado=(123,))
        repo = _repo(cursor)
        self.assertTrue(repo.ja_transferido(date(2026, 8, 30)))
        sql, params = cursor.executed[0]
        self.assertIn("STATUS = ?", sql)
        self.assertEqual(params, ["RoboBulkChatBot", STATUS_SUCESSO, "2026-08-30%"])

    def test_retorna_false_quando_nao_ha_registro(self):
        repo = _repo(_FakeCursor(resultado=None))
        self.assertFalse(repo.ja_transferido(date(2026, 8, 30)))

    def test_desabilitado_nao_conecta_e_retorna_false(self):
        cfg = dict(CONFIG, enabled=False)
        repo = LogExecucaoRepository(config=cfg)
        repo._conectar = mock.Mock(side_effect=AssertionError("nao deveria conectar"))
        self.assertFalse(repo.ja_transferido(date(2026, 8, 30)))


class TestRegistrar(unittest.TestCase):
    def test_registrar_sucesso_monta_insert_e_commita(self):
        cursor = _FakeCursor(None)
        conn = _FakeConn(cursor)
        repo = LogExecucaoRepository(config=dict(CONFIG))
        repo._conectar = lambda: conn  # type: ignore[method-assign]
        repo.registrar_sucesso(
            data_ref=date(2026, 8, 30),
            dt_inicio=datetime(2026, 8, 31, 6, 0, 0),
            dt_fim=datetime(2026, 8, 31, 6, 1, 0),
            arquivo=r"C:\tmp\Campanhas.xlsx",
            caminho_destino=r"\\srv\share\Campanhas.xlsx",
        )
        sql, params = cursor.executed[0]
        self.assertIn("INSERT INTO TB_LOG_EXECUCAO", sql)
        self.assertIn("ID_EXECUCAO", sql)
        # ID_EXECUCAO deve ser um GUID valido
        uuid.UUID(params[0])
        self.assertIn("RoboBulkChatBot", params)
        self.assertIn(STATUS_SUCESSO, params)
        self.assertIn("2026-08-30_Campanhas.xlsx", params)
        self.assertTrue(conn.committed)
        self.assertTrue(conn.closed)

    def test_ids_opcionais_entram_quando_configurados(self):
        cfg = dict(CONFIG, id_cedente=7, id_mapa=42)
        cursor = _FakeCursor(None)
        repo = _repo(cursor, config=cfg)
        repo.registrar_sucesso(
            data_ref=date(2026, 8, 30),
            dt_inicio=datetime(2026, 8, 31, 6, 0, 0),
            dt_fim=datetime(2026, 8, 31, 6, 1, 0),
            arquivo="Campanhas.xlsx",
            caminho_destino=r"\\srv\share\Campanhas.xlsx",
        )
        _, params = cursor.executed[0]
        self.assertIn(7, params)
        self.assertIn(42, params)


if __name__ == "__main__":
    unittest.main()
