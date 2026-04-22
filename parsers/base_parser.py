from abc import ABC, abstractmethod
from playwright.sync_api import Page


class BaseParser(ABC):
    """Interface comum para todos os parsers de loja."""

    @abstractmethod
    def get_price(self, page: Page, url: str) -> float | None:
        """Navega até a URL e retorna o preco como float, ou None se falhar."""
        ...

    @abstractmethod
    def get_name(self, page: Page, url: str) -> str | None:
        """Retorna o nome do produto, ou None se falhar."""
        ...

    def _extrair_json_ld(self, page: Page) -> dict | None:
        """Tenta extrair o primeiro bloco JSON-LD da pagina."""
        import json
        elements = page.query_selector_all('script[type="application/ld+json"]')
        for el in elements:
            try:
                data = json.loads(el.inner_text())
                if isinstance(data, list):
                    data = data[0]
                if data.get("@type") == "Product":
                    return data
            except (json.JSONDecodeError, AttributeError):
                continue
        return None

    def _preco_para_float(self, valor: str) -> float | None:
        """Converte string de preco (ex: 'R$ 1.299,90') para float."""
        try:
            limpo = valor.replace("R$", "").replace(".", "").replace(",", ".").strip()
            return float(limpo)
        except (ValueError, AttributeError):
            return None
