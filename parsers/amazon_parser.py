from playwright.sync_api import Page
from .base_parser import BaseParser


class AmazonParser(BaseParser):

    def get_price(self, page: Page, url: str) -> float | None:
        page.goto(url, wait_until="domcontentloaded", timeout=30000)

        seletores = [
            ".a-price .a-offscreen",
            "#priceblock_ourprice",
            "#priceblock_dealprice",
        ]
        for seletor in seletores:
            el = page.query_selector(seletor)
            if el:
                preco = self._preco_para_float(el.inner_text())
                if preco:
                    return preco

        return None

    def get_name(self, page: Page, url: str) -> str | None:
        el = page.query_selector("#productTitle")
        if el:
            return el.inner_text().strip()
        return None
