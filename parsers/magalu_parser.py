from playwright.sync_api import Page
from .base_parser import BaseParser


class MagaluParser(BaseParser):

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

        # Fallback CSS — o elemento retorna várias linhas; a última contém o valor limpo
        el = page.query_selector('p[data-testid="price-value"]')
        if el:
            ultima_linha = el.inner_text().strip().split("\n")[-1]
            preco = self._preco_para_float(ultima_linha)
            if preco:
                return preco

        return None

    def get_name(self, page: Page, url: str) -> str | None:
        data = self._extrair_json_ld(page)
        if data:
            nome = data.get("name")
            if nome:
                return nome.strip()
        return None
