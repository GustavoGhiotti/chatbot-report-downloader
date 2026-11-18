"""Configuracao de logging: arquivo rotativo + console."""

import logging
import os
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

from src.shared.utils.env_load import LOG_CONFIG


def configurar_logging(log_filename: str = "robo_bulk_chatbot.log") -> None:
    log_dir = Path(__file__).resolve().parent / "log"
    os.makedirs(log_dir, exist_ok=True)
    log_path = log_dir / (log_filename or "robo_bulk_chatbot.log")

    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s - %(message)s")

    file_handler = TimedRotatingFileHandler(
        log_path, when="D", interval=2, backupCount=5, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(LOG_CONFIG.get("level", logging.INFO))
    root.handlers.clear()
    root.addHandler(file_handler)
    root.addHandler(console_handler)

    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("playwright").setLevel(logging.WARNING)
    logging.getLogger("smbprotocol").setLevel(logging.WARNING)
