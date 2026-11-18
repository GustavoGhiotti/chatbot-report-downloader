"""Destino SMB: registra a sessao e grava o arquivo no compartilhamento.

Baseado no padrao do RoboCargas / AutomacaoOrganizacaoArquivos.
"""

import logging
import ntpath
import shutil

import smbclient

from src.shared.utils.env_load import SMB_CONFIG

log = logging.getLogger("SmbDestino")


class SmbDestino:
    def __init__(self, servidor: str | None = None, usuario: str | None = None,
                 senha: str | None = None, share_path: str | None = None):
        self._servidor = servidor or SMB_CONFIG["server"]
        self._usuario = usuario or SMB_CONFIG["user"]
        self._senha = senha or SMB_CONFIG["password"]
        self._share_path = (share_path or SMB_CONFIG["share_path"]).rstrip("\\/")

    def conectar(self) -> None:
        # Padrao dos robos do grupo (ex.: Atlas): se houver credenciais no .env,
        # registra a sessao com elas; caso contrario, usa a sessao ja autenticada
        # do Windows (conexao existente do PC).
        if self._usuario or self._senha:
            smbclient.register_session(
                server=self._servidor, username=self._usuario, password=self._senha
            )
            log.info("Sessao SMB registrada em %s (credenciais do .env)", self._servidor)
        else:
            smbclient.register_session(server=self._servidor)
            log.info("Sessao SMB registrada em %s (sessao existente do Windows)", self._servidor)

    def desconectar(self) -> None:
        try:
            smbclient.unregister_session(server=self._servidor)
        except Exception:
            pass

    def _caminho_destino(self, nome: str) -> str:
        return f"{self._share_path}\\{nome}"

    def enviar(self, arquivo_local, nome_destino: str | None = None) -> str:
        """Copia o arquivo local para o compartilhamento. Retorna o caminho UNC final."""
        nome = nome_destino or ntpath.basename(str(arquivo_local))
        destino = self._caminho_destino(nome)

        smbclient.makedirs(self._share_path, exist_ok=True)
        with open(arquivo_local, "rb") as origem, smbclient.open_file(destino, mode="wb") as saida:
            shutil.copyfileobj(origem, saida)

        log.info("Arquivo gravado no destino SMB: %s", destino)
        return destino
