"""Scraper da tela /relatorios do voxi.example.

Fluxo: seleciona o tipo de relatorio no combobox, define Data Inicio/Fim,
clica em "Exportar Excel" e salva o download num diretorio local temporario.
"""

import logging
import re
from datetime import date
from pathlib import Path

from playwright.sync_api import Download, Page

log = logging.getLogger("VoxiScraper")

MESES_PT = {
    1: "janeiro", 2: "fevereiro", 3: "março", 4: "abril", 5: "maio", 6: "junho",
    7: "julho", 8: "agosto", 9: "setembro", 10: "outubro", 11: "novembro", 12: "dezembro",
}
MESES_EN = {
    1: "january", 2: "february", 3: "march", 4: "april", 5: "may", 6: "june",
    7: "july", 8: "august", 9: "september", 10: "october", 11: "november", 12: "december",
}
_TODOS_MESES = {**{v: k for k, v in MESES_PT.items()}, **{v: k for k, v in MESES_EN.items()}}


def parse_mes_ano(texto: str | None) -> date | None:
    """Extrai (ano, mes) do cabecalho de um calendario. Ex.: 'agosto de 2026' -> date(2026,8,1)."""
    if not texto:
        return None
    texto = texto.strip().lower()
    ano_match = re.search(r"(20\d{2})", texto)
    if not ano_match:
        return None
    for nome, num in _TODOS_MESES.items():
        if nome in texto:
            return date(int(ano_match.group(1)), num, 1)
    return None

PREV_SELECTORS = [
    "button[name='previous-month']",
    "button[aria-label*='anterior' i]",
    "button[aria-label*='previous' i]",
    ".rdp-button_previous",
    ".rdp-nav_button_previous",
]


class VoxiRelatorioScraper:
    def __init__(self, tipo_relatorio: str, download_dir: Path):
        self._tipo = tipo_relatorio
        self._download_dir = download_dir
        self._download_dir.mkdir(parents=True, exist_ok=True)

    def exportar(self, page: Page, data_alvo: date) -> Path:
        """Executa o export e retorna o caminho do arquivo baixado."""
        log.info("Selecionando tipo de relatorio: %s", self._tipo)
        self._selecionar_tipo(page)

        log.info("Definindo periodo (Data Inicio e Data Fim) para %s", data_alvo.isoformat())
        self._definir_data(page, "Data Início", data_alvo)
        self._definir_data(page, "Data Fim", data_alvo)

        log.info("Clicando em 'Exportar Excel' e aguardando download")
        download = self._exportar_e_baixar(page)

        destino = self._download_dir / download.suggested_filename
        download.save_as(str(destino))
        log.info("Download concluido: %s", destino.name)
        return destino

    # ------------------------------------------------------------------ tipo
    def _selecionar_tipo(self, page: Page) -> None:
        trigger = page.locator("button[role='combobox']").first
        trigger.wait_for(state="visible")
        if (trigger.inner_text() or "").strip().startswith(self._tipo):
            log.info("Tipo de relatorio ja selecionado")
            return
        trigger.click()
        opcao = page.get_by_role("option", name=re.compile(re.escape(self._tipo), re.I))
        opcao.first.wait_for(state="visible")
        opcao.first.click()
        page.wait_for_timeout(300)

    # ------------------------------------------------------------------ datas
    def _definir_data(self, page: Page, label: str, alvo: date) -> None:
        esperado = f"{alvo.day:02d}/{alvo.month:02d}/{alvo.year}"
        trigger = self._trigger_data(page, label)

        for tentativa in range(1, 3):
            if (trigger.inner_text() or "").strip().endswith(esperado):
                log.info("%s ja esta em %s", label, esperado)
                return
            trigger.click()
            popover = page.locator("[role='dialog']").last
            popover.wait_for(state="visible")
            self._navegar_para_mes(page, popover, alvo)
            self._clicar_dia(popover, alvo)
            page.wait_for_timeout(300)
            if (trigger.inner_text() or "").strip().endswith(esperado):
                log.info("%s definido para %s", label, esperado)
                return
            log.warning("%s ainda nao esta em %s (tentativa %s)", label, esperado, tentativa)

        raise RuntimeError(f"Nao foi possivel definir '{label}' para {esperado}")

    def _trigger_data(self, page: Page, label: str):
        # botao popover-trigger dentro do bloco que contem o label
        bloco = page.locator("div.space-y-2").filter(has=page.get_by_text(label, exact=True))
        botao = bloco.locator("button[data-slot='popover-trigger']")
        if botao.count() > 0:
            return botao.first
        # fallback: botao logo apos o label
        return page.get_by_text(label, exact=True).locator(
            "xpath=following::button[1]"
        )

    def _navegar_para_mes(self, page: Page, popover, alvo: date) -> None:
        alvo_idx = alvo.year * 12 + alvo.month
        for _ in range(24):
            atual = self._mes_visivel(popover)
            if atual is None:
                # nao consegui ler o cabecalho: aborta a navegacao e tenta clicar o dia
                log.debug("Cabecalho do calendario nao lido; seguindo sem navegar")
                return
            atual_idx = atual.year * 12 + atual.month
            if atual_idx == alvo_idx:
                return
            if atual_idx > alvo_idx:
                self._clicar_prev(popover)
            else:
                self._clicar_next(popover)
            page.wait_for_timeout(200)

    def _mes_visivel(self, popover):
        texto = ""
        for selector in ("[aria-live='polite']", "[role='status']", ".rdp-caption_label",
                         ".rdp-month_caption", ".rdp-caption"):
            try:
                loc = popover.locator(selector)
                if loc.count() > 0:
                    texto = loc.first.inner_text().strip().lower()
                    if texto:
                        break
            except Exception:
                continue
        if not texto:
            try:
                texto = popover.inner_text().strip().lower()
            except Exception:
                return None
        return parse_mes_ano(texto)

    def _clicar_prev(self, popover) -> None:
        self._clicar_nav(popover, PREV_SELECTORS, fallback_index=0)

    def _clicar_next(self, popover) -> None:
        selectors = [
            "button[name='next-month']",
            "button[aria-label*='próximo' i]",
            "button[aria-label*='proximo' i]",
            "button[aria-label*='next' i]",
            ".rdp-button_next",
            ".rdp-nav_button_next",
        ]
        self._clicar_nav(popover, selectors, fallback_index=-1)

    def _clicar_nav(self, popover, selectors, fallback_index: int) -> None:
        for selector in selectors:
            try:
                loc = popover.locator(selector)
                if loc.count() > 0 and loc.first.is_visible():
                    loc.first.click()
                    return
            except Exception:
                continue
        # fallback: botoes de navegacao costumam ser os primeiros do calendario
        try:
            botoes = popover.locator("button")
            botoes.nth(fallback_index if fallback_index >= 0 else botoes.count() - 1).click()
        except Exception:
            log.warning("Botao de navegacao do calendario nao encontrado")

    def _clicar_dia(self, popover, alvo: date) -> None:
        # No voxi.example (react-day-picker) cada dia e um <button> cujo aria-label
        # traz a data completa, ex.: "quarta-feira, 26 de agosto de 2026".
        # Selecionar por aria-label elimina a ambiguidade dos dias "de fora"
        # (ha dois "26" quando o mes anterior aparece no inicio da grade).
        alvo_txt = f"{alvo.day} de {MESES_PT[alvo.month]} de {alvo.year}"
        loc = popover.locator(f'button[aria-label*="{alvo_txt}"]')
        if loc.count() > 0:
            loc.first.click()
            return
        # fallback: casar pelo aria-label via regex (acentos/variacoes)
        alvo_regex = re.compile(rf"\b{alvo.day}\s+de\s+{MESES_PT[alvo.month]}\s+de\s+{alvo.year}\b", re.I)
        alt = popover.get_by_role("button", name=alvo_regex)
        if alt.count() > 0:
            alt.first.click()
            return
        raise RuntimeError(f"Dia nao encontrado no calendario: {alvo_txt}")

    # ------------------------------------------------------------------ export
    def _exportar_e_baixar(self, page: Page, timeout_ms: int = 120000) -> Download:
        botao = page.get_by_role("button", name=re.compile(r"exportar\s+excel", re.I))
        with page.expect_download(timeout=timeout_ms) as dl_info:
            botao.first.click()
        return dl_info.value
