"""Orquestra o fluxo: login -> export do relatorio de campanhas (D-1) -> SMB."""

import logging
from datetime import date, datetime, timedelta
from pathlib import Path

from src.infrastructure.voxi.voxi_relatorio_scraper import VoxiRelatorioScraper
from src.infrastructure.voxi.voxi_session import VoxiSession
from src.infrastructure.db.log_execucao_repository import LogExecucaoRepository
from src.infrastructure.smb.smb_destino import SmbDestino
from src.shared.utils.env_load import VOXI_CONFIG

log = logging.getLogger("RelatorioCampanhasService")

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DOWNLOAD_DIR = PROJECT_ROOT / "downloads"


class RelatorioCampanhasService:
    def __init__(self, headless: bool | None = None,
                 repositorio_log: LogExecucaoRepository | None = None):
        self._headless = headless
        self._log_repo = repositorio_log or LogExecucaoRepository()

    def executar(self, data_alvo: date | None = None) -> str:
        alvo = data_alvo or (date.today() - timedelta(days=1))
        log.info("Iniciando export do relatorio de campanhas para %s", alvo.isoformat())

        # Idempotencia: se o dia ja foi transferido com sucesso, encerra sem
        # reabrir o navegador nem reenviar o arquivo (pode rodar N vezes por dia).
        if self._log_repo.ja_transferido(alvo):
            msg = f"[JA TRANSFERIDO] {alvo.isoformat()} - nada a fazer."
            log.info(msg)
            return msg

        dt_inicio = datetime.now()
        try:
            scraper = VoxiRelatorioScraper(
                tipo_relatorio=VOXI_CONFIG["tipo_relatorio"],
                download_dir=DOWNLOAD_DIR,
            )

            with VoxiSession(headless=self._headless) as page:
                arquivo_local = scraper.exportar(page, alvo)

            destino = SmbDestino()
            destino.conectar()
            try:
                caminho_final = destino.enviar(arquivo_local)
            finally:
                destino.desconectar()
        except Exception as exc:  # noqa: BLE001
            # Falhou: registra ERRO (nao bloqueia futuras tentativas, que checam SUCESSO).
            self._registrar_seguro(
                lambda: self._log_repo.registrar_erro(
                    alvo, dt_inicio, datetime.now(), f"{type(exc).__name__}: {exc}"
                )
            )
            raise

        # Sucesso: carimba o dia na TB_LOG_EXECUCAO (marca do "transferido do dia").
        self._registrar_seguro(
            lambda: self._log_repo.registrar_sucesso(
                alvo, dt_inicio, datetime.now(), arquivo_local, caminho_final
            )
        )

        log.info("Concluido. Arquivo publicado em: %s", caminho_final)
        return caminho_final

    @staticmethod
    def _registrar_seguro(acao) -> None:
        """Registra no banco sem deixar uma falha de log derrubar a automacao."""
        try:
            acao()
        except Exception as exc:  # noqa: BLE001
            log.error("Falha ao registrar execucao na TB_LOG_EXECUCAO: %s", exc)
