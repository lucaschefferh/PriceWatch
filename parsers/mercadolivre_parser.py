from playwright.sync_api import Page
from .base_parser import BaseParser


class MercadoLivreParser(BaseParser):

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

        # Fallback CSS — retorna só a parte inteira; centavos ignorados (precisão suficiente)
        el = page.query_selector(".ui-pdp-price__second-line .andes-money-amount__fraction")
        if el:
            preco = self._preco_para_float(el.inner_text())
            if preco:
                return preco

        return None

    def get_name(self, page: Page, url: str) -> str | None:
        data = self._extrair_json_ld(page)
        if data:
            nome = data.get("name")
            if nome:
                return nome.strip()
        el = page.query_selector("h1.ui-pdp-title")
        if el:
            return el.inner_text().strip()
        return None
