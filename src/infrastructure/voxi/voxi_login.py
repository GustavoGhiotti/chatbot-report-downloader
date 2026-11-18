"""Login no voxi.example: detecta a tela de login e preenche e-mail/senha."""

import logging
import re

from playwright.sync_api import Page

from src.shared.utils.env_load import VOXI_CONFIG

log = logging.getLogger("VoxiLogin")

EMAIL_SELECTORS = [
    "#email",
    "input[autocomplete='username']",
    "input[name*='email' i]",
    "input[id*='email' i]",
    "input[type='email']",
]
PASSWORD_SELECTORS = [
    "#password",
    "input[type='password']",
    "input[name*='password' i]",
    "input[id*='password' i]",
]
SUBMIT_REGEX = re.compile(r"^\s*(entrar|login|log in|sign in|acessar|continuar)\s*$", re.I)


def precisa_login(page: Page) -> bool:
    """True se a pagina atual parece ser a tela de login."""
    try:
        url = (page.url or "").lower()
    except Exception:
        url = ""
    login_url = (VOXI_CONFIG.get("login_url") or "").lower()
    if login_url and login_url in url:
        return True
    if "login" in url or "signin" in url:
        return True
    return _tem_campo(page, PASSWORD_SELECTORS)


def _tem_campo(page: Page, selectors: list[str]) -> bool:
    for selector in selectors:
        try:
            if page.locator(selector).count() > 0:
                return True
        except Exception:
            continue
    return False


def fazer_login(page: Page, timeout_ms: int) -> bool:
    """Preenche credenciais e confirma. Retorna True se saiu da tela de login."""
    username = VOXI_CONFIG.get("username")
    password = VOXI_CONFIG.get("password")
    if not username or not password:
        log.error("VOXI_USERNAME/VOXI_PASSWORD nao configurados no .env")
        return False

    log.info("Tela de login detectada; preenchendo credenciais")
    if not _preencher(page, EMAIL_SELECTORS, username, timeout_ms):
        log.error("Campo de e-mail/usuario nao encontrado na tela de login")
        return False
    if not _preencher(page, PASSWORD_SELECTORS, password, timeout_ms):
        log.error("Campo de senha nao encontrado na tela de login")
        return False

    _submeter(page)

    try:
        page.wait_for_url(
            lambda url: "login" not in (url or "").lower(),
            timeout=timeout_ms,
        )
    except Exception:
        pass

    if precisa_login(page):
        log.error("Login nao concluido: ainda na tela de login (verifique credenciais)")
        return False

    log.info("Login concluido com sucesso")
    return True


def _preencher(page: Page, selectors: list[str], valor: str, timeout_ms: int) -> bool:
    for selector in selectors:
        try:
            locator = page.locator(selector)
            if locator.count() == 0:
                continue
            campo = locator.first
            campo.wait_for(state="visible", timeout=min(timeout_ms, 10000))
            campo.click()
            campo.fill("")
            campo.fill(valor)
            return True
        except Exception:
            continue
    return False


def _submeter(page: Page) -> None:
    try:
        botao = page.get_by_role("button", name=SUBMIT_REGEX)
        if botao.count() > 0:
            botao.first.click(timeout=5000)
            return
    except Exception:
        pass
    for selector in ("button[type='submit']", "form button"):
        try:
            page.locator(selector).first.click(timeout=5000)
            return
        except Exception:
            continue
    # ultimo recurso: enviar Enter no campo de senha
    try:
        page.locator(PASSWORD_SELECTORS[0]).first.press("Enter")
    except Exception:
        pass
