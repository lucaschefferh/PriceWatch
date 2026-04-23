from datetime import datetime, timedelta
from core.mailer import _gerar_grafico_base64
import base64


def _historico(n: int, preco_base: float = 300.0) -> list[dict]:
    return [
        {
            "preco": preco_base - i * 2,
            "data_captura": (datetime.now() - timedelta(days=n - i)).isoformat(),
        }
        for i in range(n)
    ]


def test_grafico_sem_dados_retorna_none():
    assert _gerar_grafico_base64([]) is None


def test_grafico_com_um_ponto_retorna_none():
    assert _gerar_grafico_base64(_historico(1)) is None


def test_grafico_retorna_base64_valido():
    resultado = _gerar_grafico_base64(_historico(10))
    assert resultado is not None
    decoded = base64.b64decode(resultado)
    assert decoded[:4] == b"\x89PNG"  # assinatura PNG


def test_grafico_com_historico_longo():
    resultado = _gerar_grafico_base64(_historico(60))
    assert resultado is not None
    assert len(resultado) > 1000
