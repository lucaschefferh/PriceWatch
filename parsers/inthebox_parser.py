from playwright.sync_api import Page
from .base_parser import BaseParser


class InTheBoxParser(BaseParser):

    def get_price(self, page: Page, url: str) -> float | None:
        page.goto(url, wait_until="domcontentloaded", timeout=30000)

        data = self._extrair_json_ld(page)
        if data:
            try:
                oferta = data.get("offers", {})
                if isinstance(oferta, list):
                    oferta = oferta[0]
                preco = oferta.get("price")
                if preco:
                    return float(preco)
            except (KeyError, ValueError, TypeError):
                pass

        # Fallback CSS — elemento contém preço na primeira linha
        el = page.query_selector("[data-price]")
        if el:
            primeira_linha = el.inner_text().strip().split("\n")[0]
            preco = self._preco_para_float(primeira_linha)
            if preco:
                return preco

        return None

    def get_name(self, page: Page, url: str) -> str | None:
        data = self._extrair_json_ld(page)
        if data:
            nome = data.get("name")
            if nome:
                return nome.strip()
        el = page.query_selector("h1")
        if el:
            return el.inner_text().strip()
        return None
