"""Gerencia o navegador Playwright e garante uma sessao logada no voxi.example.

Uso:
    with VoxiSession() as page:
        ...  # page ja esta autenticado e em /relatorios
"""

import logging
from pathlib import Path

from playwright.sync_api import sync_playwright

from src.infrastructure.voxi.voxi_login import fazer_login, precisa_login
from src.shared.utils.env_load import VOXI_CONFIG

log = logging.getLogger("VoxiSession")

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class VoxiSession:
    def __init__(self, headless: bool | None = None):
        self._headless = VOXI_CONFIG["headless"] if headless is None else headless
        self._timeout = VOXI_CONFIG["timeout_ms"]
        self._pw = None
        self._browser = None
        self._context = None
        self._page = None

    def __enter__(self):
        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch(headless=self._headless)

        storage = self._session_file()
        context_kwargs = {"accept_downloads": True}
        if storage.exists():
            log.info("Reutilizando sessao salva em %s", storage)
            context_kwargs["storage_state"] = str(storage)

        self._context = self._browser.new_context(**context_kwargs)
        self._context.set_default_timeout(self._timeout)
        self._page = self._context.new_page()

        self._garantir_login()
        return self._page

    def __exit__(self, exc_type, exc, tb):
        for fechar in (
            lambda: self._context and self._context.close(),
            lambda: self._browser and self._browser.close(),
            lambda: self._pw and self._pw.stop(),
        ):
            try:
                fechar()
            except Exception:
                pass
        return False

    def _garantir_login(self) -> None:
        page = self._page
        page.goto(VOXI_CONFIG["relatorios_url"], wait_until="domcontentloaded")
        self._aguardar_estabilizar(page)  # a SPA pode redirecionar para /login

        if precisa_login(page):
            page.goto(VOXI_CONFIG["login_url"], wait_until="domcontentloaded")
            self._aguardar_estabilizar(page)
            if not fazer_login(page, self._timeout):
                raise RuntimeError("Falha no login do voxi.example")
            self._salvar_sessao()
            page.goto(VOXI_CONFIG["relatorios_url"], wait_until="domcontentloaded")
            self._aguardar_estabilizar(page)
        else:
            log.info("Sessao ja autenticada")

    @staticmethod
    def _aguardar_estabilizar(page) -> None:
        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            page.wait_for_timeout(2000)

    def _salvar_sessao(self) -> None:
        storage = self._session_file()
        storage.parent.mkdir(parents=True, exist_ok=True)
        self._context.storage_state(path=str(storage))
        log.info("Sessao salva em %s", storage)

    def _session_file(self) -> Path:
        caminho = Path(VOXI_CONFIG["session_path"])
        if not caminho.is_absolute():
            caminho = PROJECT_ROOT / caminho
        return caminho
