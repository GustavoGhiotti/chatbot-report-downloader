"""Carrega o .env e expoe as configuracoes em dicionarios simples."""

import logging
import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(PROJECT_ROOT / ".env")


def _bool(valor: str | None, padrao: bool = False) -> bool:
    if valor is None:
        return padrao
    return valor.strip().lower() in {"1", "true", "yes", "sim", "y"}


VOXI_CONFIG = {
    "login_url": os.getenv("VOXI_LOGIN_URL", "https://voxi.example/login").strip(),
    "relatorios_url": os.getenv("VOXI_RELATORIOS_URL", "https://voxi.example/relatorios").strip(),
    "username": os.getenv("VOXI_USERNAME"),
    "password": os.getenv("VOXI_PASSWORD"),
    "tipo_relatorio": os.getenv("VOXI_TIPO_RELATORIO", "Campanhas (Excel)").strip(),
    "headless": _bool(os.getenv("VOXI_HEADLESS"), padrao=True),
    "session_path": os.getenv(
        "VOXI_SESSION_PATH",
        "src/infrastructure/voxi/session/storage.json",
    ).strip(),
    "timeout_ms": int(os.getenv("VOXI_TIMEOUT_MS", "60000")),
}

SMB_CONFIG = {
    "server": os.getenv("SMB_SERVER", "10.0.0.72").strip(),
    "share_path": os.getenv(
        "SMB_SHARE_PATH",
        r"\\10.0.0.72\Automacao\RELATORIOS_CAMPANHAS_CHATBOT",
    ).strip(),
    "user": os.getenv("SMB_USER"),
    "password": os.getenv("SMB_PASSWORD"),
}


def _int(valor: str | None) -> int | None:
    if valor is None or valor.strip() == "":
        return None
    try:
        return int(valor.strip())
    except ValueError:
        return None


# Registro de execucao na tabela compartilhada LOGS_ROBOS.dbo.TB_LOG_EXECUCAO.
# Serve de "carimbo do dia": marca que o relatorio de uma data ja foi transferido,
# para o robo poder rodar varias vezes sem reprocessar/reenviar.
# Segue o padrao de conexao dos demais robos do grupo (AutomacaoOrganizacaoArquivos):
# pyodbc com DRIVER=SQL SERVER + TrustServerCertificate=YES, vars DB_LOGS_*.
SQL_CONFIG = {
    "enabled": _bool(os.getenv("DB_LOGS_ENABLED"), padrao=True),
    "driver": os.getenv("DB_LOGS_DRIVER", "SQL SERVER").strip(),
    "server": (os.getenv("DB_LOGS_SERVER") or "10.0.0.66").strip(),
    "database": os.getenv("DB_LOGS_DATABASE", "LOGS_ROBOS").strip(),
    "user": os.getenv("DB_LOGS_USER"),
    "password": os.getenv("DB_LOGS_PASSWORD"),
    "tabela": os.getenv("DB_LOGS_TABELA", "TB_LOG_EXECUCAO").strip(),
    # Identificacao fixa deste robo na tabela compartilhada.
    "nm_cedente": os.getenv("ROBO_NM_CEDENTE", "RoboBulkChatBot").strip(),
    "id_cedente": _int(os.getenv("ROBO_ID_CEDENTE")),  # opcional (so grava se informado)
    "id_mapa": _int(os.getenv("ROBO_ID_MAPA")),        # opcional (so grava se informado)
}

LOG_CONFIG = {
    "level": logging.DEBUG if _bool(os.getenv("ROBO_DEBUG")) else logging.INFO,
}
