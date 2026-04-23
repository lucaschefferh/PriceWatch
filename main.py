import os
import time
import random
import logging
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

from core.database import criar_tabelas, buscar_produtos_ativos, salvar_preco, ultimo_preco, minimo_historico
from core.mailer import enviar_alerta, enviar_resumo_diario
from parsers.amazon_parser import AmazonParser
from parsers.inthebox_parser import InTheBoxParser
from parsers.magalu_parser import MagaluParser
from parsers.mercadolivre_parser import MercadoLivreParser

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("data/pricewatch.log"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)

PARSERS = {
    "amazon": AmazonParser(),
    "inthebox": InTheBoxParser(),
    "magalu": MagaluParser(),
    "mercadolivre": MercadoLivreParser(),
}

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
]

def jitter():
    minimo = int(os.getenv("JITTER_MIN", 60))
    maximo = int(os.getenv("JITTER_MAX", 1800))
    espera = random.randint(minimo, maximo)
    log.info(f"Jitter: aguardando {espera}s antes de iniciar...")
    time.sleep(espera)

def processar_produto(page, produto) -> dict:
    """Processa um produto e retorna dict com resultado para o resumo diário."""
    resultado = {
        "nome": produto["nome"],
        "loja": produto["loja"],
        "url": produto["url"],
        "preco_atual": None,
        "preco_anterior": None,
        "erro": False,
        "alerta_enviado": False,
    }

    loja = produto["loja"]
    parser = PARSERS.get(loja)

    if not parser:
        log.warning(f"Nenhum parser encontrado para a loja '{loja}' (produto id={produto['id']})")
        resultado["erro"] = True
        return resultado

    log.info(f"Scraping: {produto['nome']} ({loja})")
    preco_atual = None
    for tentativa in range(3):
        try:
            preco_atual = parser.get_price(page, produto["url"])
        except Exception as e:
            log.warning(f"Tentativa {tentativa + 1} excecao: {e}")

        if preco_atual is not None:
            break

        if tentativa < 2:
            espera = 30 * (2 ** tentativa)  # 30s, 60s
            log.warning(f"Tentativa {tentativa + 1} falhou. Aguardando {espera}s...")
            time.sleep(espera)

    if preco_atual is None:
        log.error(f"Falha ao capturar preco apos 3 tentativas: {produto['nome']}")
        resultado["erro"] = True
        return resultado

    log.info(f"Preco capturado: R$ {preco_atual:.2f}")

    preco_anterior = ultimo_preco(produto["id"])
    minimo = minimo_historico(produto["id"])
    config_alerta = produto["config_alerta"]

    salvar_preco(produto["id"], preco_atual)

    resultado["preco_atual"] = preco_atual
    resultado["preco_anterior"] = preco_anterior

    eh_minimo = minimo is not None and preco_atual < minimo

    deve_alertar = False
    if config_alerta is not None:
        cruzou_alvo = preco_atual <= config_alerta and (preco_anterior is None or preco_anterior > config_alerta)
        if cruzou_alvo:
            deve_alertar = True
            log.info(f"Preco alvo atingido: R${preco_atual:.2f} <= alvo R${config_alerta:.2f}")
    elif preco_anterior is not None and preco_atual < preco_anterior:
        deve_alertar = True
        log.info(f"Queda detectada: R${preco_anterior:.2f} -> R${preco_atual:.2f}")

    if deve_alertar:
        try:
            enviar_alerta(produto["nome"], preco_anterior, preco_atual, produto["url"], eh_minimo_historico=eh_minimo)
            log.info(f"Alerta enviado.{' (minimo historico)' if eh_minimo else ''}")
            resultado["alerta_enviado"] = True
        except Exception as e:
            log.error(f"Erro ao enviar e-mail: {e}")
    else:
        log.info("Sem alerta. Historico atualizado.")

    return resultado

def main():
    jitter()
    criar_tabelas()
    produtos = buscar_produtos_ativos()

    if not produtos:
        log.warning("Nenhum produto ativo encontrado no banco.")
        return

    resultados = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        for produto in produtos:
            user_agent = random.choice(USER_AGENTS)
            context = browser.new_context(user_agent=user_agent)
            page = context.new_page()
            Stealth().apply_stealth_sync(page)

            try:
                resultado = processar_produto(page, produto)
                resultados.append(resultado)
            except Exception as e:
                log.error(f"Erro inesperado ao processar '{produto['nome']}': {e}")
                resultados.append({
                    "nome": produto["nome"],
                    "loja": produto["loja"],
                    "url": produto["url"],
                    "preco_atual": None,
                    "preco_anterior": None,
                    "erro": True,
                    "alerta_enviado": False,
                })
            finally:
                context.close()

            time.sleep(random.randint(5, 20))

        browser.close()

    try:
        enviar_resumo_diario(resultados)
        log.info("Resumo diario enviado.")
    except Exception as e:
        log.error(f"Erro ao enviar resumo diario: {e}")


if __name__ == "__main__":
    main()
