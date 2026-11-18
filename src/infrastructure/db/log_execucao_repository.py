"""Registro de execucao na tabela compartilhada LOGS_ROBOS.dbo.TB_LOG_EXECUCAO.

Funciona como "carimbo do dia": depois que o relatorio de uma data de referencia
(D-1) e transferido com sucesso, grava-se uma linha SUCESSO identificando o robo
(NM_CEDENTE fixo) e a data no NM_ARQUIVOS. Antes de rodar, o robo pergunta
`ja_transferido(data)`; se ja houver SUCESSO para aquela data, a automacao encerra
sem reabrir o navegador nem reenviar o arquivo. Assim, rodar varias vezes no mesmo
dia nao gera reprocessamento nem duplicidade.

Conexao segue o padrao dos demais robos do grupo (AutomacaoOrganizacaoArquivos):
pyodbc com "DRIVER=SQL SERVER" + TrustServerCertificate=YES, abrindo/fechando a
conexao por query. Configuracao em `SQL_CONFIG` (vars DB_LOGS_* no .env).
"""

import logging
import ntpath
import socket
import uuid
from datetime import date, datetime

from src.shared.utils.env_load import SQL_CONFIG

log = logging.getLogger("LogExecucaoRepository")

STATUS_SUCESSO = "SUCESSO"
STATUS_ERRO = "ERRO"


class Conexao:
    """Abre uma conexao pyodbc no padrao dos robos do grupo (DRIVER=SQL SERVER)."""

    def __init__(self, cfg: dict):
        self._cfg = cfg

    def obter_conexao(self):
        import pyodbc  # import tardio: so exige o driver quando o log esta habilitado

        if not self._cfg.get("server"):
            raise RuntimeError(
                "DB_LOGS_SERVER nao configurado no .env; nao e possivel registrar a execucao."
            )
        return pyodbc.connect(
            f"DRIVER={{{self._cfg['driver']}}};"
            f"SERVER={self._cfg['server']};"
            f"DATABASE={self._cfg['database']};"
            f"UID={self._cfg['user']};"
            f"PWD={self._cfg['password']};"
            "TrustServerCertificate=YES"
        )


class LogExecucaoRepository:
    """Acesso a TB_LOG_EXECUCAO para carimbar/consultar o processamento do dia."""

    def __init__(self, config: dict | None = None):
        self._cfg = config or SQL_CONFIG
        self._tabela = self._cfg["tabela"]
        self._nm_cedente = self._cfg["nm_cedente"]
        self._maquina = socket.gethostname()
        self._conexao = Conexao(self._cfg)

    @property
    def habilitado(self) -> bool:
        return bool(self._cfg.get("enabled", True))

    def _conectar(self):
        return self._conexao.obter_conexao()

    # ------------------------------------------------------------------ chave do dia
    @staticmethod
    def _chave_dia(data_ref: date) -> str:
        """Prefixo estavel da data de referencia usado no NM_ARQUIVOS."""
        return data_ref.isoformat()  # ex.: 2026-08-30

    def _nome_arquivo_registro(self, data_ref: date, arquivo) -> str:
        """Valor gravado em NM_ARQUIVOS: data de referencia + nome real do arquivo."""
        base = ntpath.basename(str(arquivo)) if arquivo else ""
        return f"{self._chave_dia(data_ref)}_{base}".rstrip("_")

    # ------------------------------------------------------------------ consulta
    def ja_transferido(self, data_ref: date) -> bool:
        """True se ja existe um SUCESSO deste robo para a data de referencia."""
        if not self.habilitado:
            log.warning("Registro SQL desabilitado (DB_LOGS_ENABLED=false); pulando verificacao.")
            return False

        query = (
            f"SELECT TOP (1) ID_LOG FROM {self._tabela} "
            "WHERE NM_CEDENTE = ? AND STATUS = ? AND NM_ARQUIVOS LIKE ?"
        )
        # A chave da data nao contem curinga de LIKE (%, _, []), entao pode ir direta.
        like = f"{self._chave_dia(data_ref)}%"
        conexao = self._conectar()
        try:
            cursor = conexao.cursor()
            cursor.execute(query, [self._nm_cedente, STATUS_SUCESSO, like])
            achou = cursor.fetchone() is not None
        finally:
            conexao.close()
        if achou:
            log.info(
                "Dia %s ja transferido por %s; nada a fazer.",
                data_ref.isoformat(), self._nm_cedente,
            )
        return achou

    # ------------------------------------------------------------------ gravacao
    def registrar(self, data_ref: date, status: str, dt_inicio: datetime,
                  dt_fim: datetime, mensagem: str, arquivo=None,
                  qtd_arquivos: int = 0) -> None:
        """Insere uma linha de execucao (SUCESSO ou ERRO) na tabela.

        Segue o layout de TB_LOG_EXECUCAO: ID_EXECUCAO e UNIQUEIDENTIFIER NOT NULL
        (geramos um GUID por execucao) e DT_REGISTRO tem DEFAULT GETDATE() (nao entra
        no INSERT).
        """
        if not self.habilitado:
            log.warning("Registro SQL desabilitado (DB_LOGS_ENABLED=false); nada gravado.")
            return

        query = f"""
            INSERT INTO {self._tabela}
                (ID_EXECUCAO, ID_MAPA, ID_CEDENTE, NM_CEDENTE, DT_INICIO, DT_FIM,
                 STATUS, QTD_ARQUIVOS, NM_ARQUIVOS, MENSAGEM, MAQUINA)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        parametros = [
            str(uuid.uuid4()),                # ID_EXECUCAO (GUID do disparo)
            self._cfg.get("id_mapa"),         # ID_MAPA (opcional: None se nao configurado)
            self._cfg.get("id_cedente"),      # ID_CEDENTE (opcional)
            self._nm_cedente,                 # NM_CEDENTE (identificacao fixa do robo)
            dt_inicio,
            dt_fim,
            status,
            qtd_arquivos,
            self._nome_arquivo_registro(data_ref, arquivo),
            (mensagem or "")[:4000],
            self._maquina,
        ]

        conexao = self._conectar()
        try:
            cursor = conexao.cursor()
            cursor.execute(query, parametros)
            conexao.commit()
        except Exception:
            conexao.rollback()
            raise
        finally:
            conexao.close()
        log.info(
            "Execucao registrada em %s: STATUS=%s data_ref=%s",
            self._tabela, status, data_ref.isoformat(),
        )

    def registrar_sucesso(self, data_ref: date, dt_inicio: datetime, dt_fim: datetime,
                          arquivo, caminho_destino: str) -> None:
        self.registrar(
            data_ref=data_ref,
            status=STATUS_SUCESSO,
            dt_inicio=dt_inicio,
            dt_fim=dt_fim,
            mensagem=f"Relatorio {data_ref.isoformat()} transferido para {caminho_destino}",
            arquivo=arquivo,
            qtd_arquivos=1,
        )

    def registrar_erro(self, data_ref: date, dt_inicio: datetime, dt_fim: datetime,
                       mensagem: str) -> None:
        self.registrar(
            data_ref=data_ref,
            status=STATUS_ERRO,
            dt_inicio=dt_inicio,
            dt_fim=dt_fim,
            mensagem=mensagem,
            arquivo=None,
            qtd_arquivos=0,
        )
