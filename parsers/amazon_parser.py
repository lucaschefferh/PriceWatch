import re
from playwright.sync_api import Page
from .base_parser import BaseParser


class AmazonParser(BaseParser):

    def _normalize_url(self, url: str) -> str:
        """Extrai o ASIN e retorna a URL canônica /dp/{ASIN}, descartando parâmetros de sessão."""
        match = re.search(r'/(?:dp|gp/product)/([A-Z0-9]{10})', url)
        if match:
            return f"https://www.amazon.com.br/dp/{match.group(1)}"
        return url

    # Escopos que contêm apenas o preço do produto principal (excluem produtos relacionados)
    _PRICE_SCOPES = [
        "#corePriceDisplay_desktop_feature_div",
        "#apex_offerDisplay_desktop",
        "#buybox",
        "#price_inside_buybox",
    ]

    def get_price(self, page: Page, url: str) -> float | None:
        page.goto(self._normalize_url(url), wait_until="domcontentloaded", timeout=30000)

        # Prioridade 1: whole+fraction dentro do escopo do produto.
        # Em produtos com desconto, .a-offscreen do preço atual fica vazio (Amazon só preenche o riscado),
        # então whole/fraction é o único indicador confiável do preço exibido.
        for scope_sel in self._PRICE_SCOPES:
            scope = page.query_selector(scope_sel)
            if not scope:
                continue
            whole = scope.query_selector("span.a-price-whole")
            fraction = scope.query_selector("span.a-price-fraction")
            if whole:
                texto_whole = (whole.text_content() or "").strip().rstrip(",").strip()
                texto_frac = (fraction.text_content() or "00").strip() if fraction else "00"
                preco = self._preco_para_float(f"{texto_whole},{texto_frac}")
                if preco:
                    return preco

        # Prioridade 2: .a-offscreen dentro do escopo, excluindo preços de comparação (.a-text-price).
        # Funciona em produtos sem desconto onde .a-offscreen é preenchido corretamente.
        for scope_sel in self._PRICE_SCOPES:
            scope = page.query_selector(scope_sel)
            if not scope:
                continue
            for el in scope.query_selector_all(".a-price:not(.a-text-price) .a-offscreen"):
                preco = self._preco_para_float(el.text_content())
                if preco:
                    return preco

        # Fallback: primeiro whole+fraction da página inteira
        whole = page.query_selector("span.a-price-whole")
        fraction = page.query_selector("span.a-price-fraction")
        if whole:
            texto_whole = (whole.text_content() or "").strip().rstrip(",").strip()
            texto_frac = (fraction.text_content() or "00").strip() if fraction else "00"
            preco = self._preco_para_float(f"{texto_whole},{texto_frac}")
            if preco:
                return preco

        # Seletores legados (layouts antigos da Amazon)
        for seletor in ["#priceblock_ourprice", "#priceblock_dealprice"]:
            el = page.query_selector(seletor)
            if el:
                preco = self._preco_para_float(el.text_content())
                if preco:
                    return preco

        return None

    def get_name(self, page: Page, url: str) -> str | None:
        el = page.query_selector("#productTitle")
        if el:
            return el.inner_text().strip()
        return None
