import pytest
from parsers.amazon_parser import AmazonParser
from parsers.base_parser import BaseParser


@pytest.fixture(scope="module")
def amazon():
    return AmazonParser()


# --- _normalize_url ---

def test_normalize_url_dp(amazon):
    url = "https://www.amazon.com.br/Mouse-Logitech/dp/B07W8X4F48/ref=abc?pd=1"
    assert amazon._normalize_url(url) == "https://www.amazon.com.br/dp/B07W8X4F48"


def test_normalize_url_gp_product(amazon):
    url = "https://www.amazon.com.br/gp/product/8595086354/ref=xyz?smid=A1&psc=1"
    assert amazon._normalize_url(url) == "https://www.amazon.com.br/dp/8595086354"


def test_normalize_url_sem_asin_retorna_original(amazon):
    url = "https://www.amazon.com.br/s?k=mouse"
    assert amazon._normalize_url(url) == url


def test_normalize_url_remove_query_params(amazon):
    url = "https://www.amazon.com.br/dp/B07W8X4F48?tag=afiliado&ref=sr_1_1"
    assert "?" not in amazon._normalize_url(url)


# --- _preco_para_float ---

class ConcreteParser(BaseParser):
    def get_price(self, page, url): ...
    def get_name(self, page, url): ...


@pytest.fixture(scope="module")
def parser():
    return ConcreteParser()


@pytest.mark.parametrize("texto, esperado", [
    ("R$ 1.299,90",  1299.90),
    ("R$299,90",     299.90),
    ("R$\xa0176,33", 176.33),   # non-breaking space
    ("1299,90",      1299.90),
    ("R$ 49,00",     49.00),
    ("R$ 1.000,00",  1000.00),
])
def test_preco_para_float_valido(parser, texto, esperado):
    assert parser._preco_para_float(texto) == pytest.approx(esperado)


@pytest.mark.parametrize("texto", [
    "",
    "   ",
    "Indisponível",
    None,
    "$00",
])
def test_preco_para_float_invalido_retorna_none(parser, texto):
    assert parser._preco_para_float(texto) is None
