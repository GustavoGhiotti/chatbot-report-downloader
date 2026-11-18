"""Ponto de entrada do RoboBulkChatBot.

Exporta o relatorio "Campanhas (Excel)" do voxi.example referente ao dia anterior (D-1)
e publica no compartilhamento SMB de destino.

Uso:
    python main.py                    # usa D-1 (ontem)
    python main.py --data 2026-08-26  # forca uma data (YYYY-MM-DD)
    python main.py --no-headless      # abre o navegador visivel
"""

import argparse
import logging
import sys
from datetime import date, datetime

from src.application.service.relatorio_campanhas_service import RelatorioCampanhasService
from src.infrastructure.logging.log_config import configurar_logging


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Exporta o relatorio de campanhas do voxi.example")
    parser.add_argument("--data", help="Data de referencia no formato YYYY-MM-DD (padrao: D-1)")
    parser.add_argument("--no-headless", action="store_true", help="Abre o navegador visivel")
    return parser.parse_args()


def _data_alvo(valor: str | None) -> date | None:
    if not valor:
        return None
    try:
        return datetime.strptime(valor, "%Y-%m-%d").date()
    except ValueError:
        raise SystemExit(f"Data invalida: '{valor}'. Use o formato YYYY-MM-DD.")


def main() -> int:
    args = _parse_args()
    configurar_logging()
    log = logging.getLogger("main")

    headless = False if args.no_headless else None  # None = usa VOXI_HEADLESS do .env
    service = RelatorioCampanhasService(headless=headless)

    try:
        caminho = service.executar(data_alvo=_data_alvo(args.data))
        log.info("Sucesso: %s", caminho)
        return 0
    except Exception as exc:  # noqa: BLE001
        log.exception("Falha ao executar o robo: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
