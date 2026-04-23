import os
import time
import random
import logging
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

from core.database import criar_tabelas, buscar_produtos_ativos, salvar_preco, ultimo_preco, minimo_historico
from core.mailer import enviar_alerta
from parsers.amazon_parser import AmazonParser
from parsers.inthebox_parser import InTheBoxParser
from parsers.magalu_parser import MagaluParser
from parsers.mercadolivre_parser import MercadoLivreParser

load_dotenv()

#configura o sistema de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("data/pricewatch.log"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)

#dicionario que mapeia o nome da loja para a classe parser correspondente
PARSERS = {
    "amazon": AmazonParser(),
    "inthebox": InTheBoxParser(),
    "magalu": MagaluParser(),
    "mercadolivre": MercadoLivreParser(),
}

#lista de user agents para rotacionar
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
]

#função que gera um tempo aleatório de espera entre minimo e maximo
def jitter():
    minimo = int(os.getenv("JITTER_MIN", 60))
    maximo = int(os.getenv("JITTER_MAX", 1800))
    espera = random.randint(minimo, maximo)
    log.info(f"Jitter: aguardando {espera}s antes de iniciar...")
    time.sleep(espera)

#função que processa um produto
def processar_produto(page, produto):
    loja = produto["loja"]
    parser = PARSERS.get(loja)

    #verifica se o parser foi encontrado
    if not parser:
        log.warning(f"Nenhum parser encontrado para a loja '{loja}' (produto id={produto['id']})")
        return

    #faz o scraping do produto
    log.info(f"Scraping: {produto['nome']} ({loja})")
    preco_atual = parser.get_price(page, produto["url"])

    #verifica se o preço foi capturado
    if preco_atual is None:
        log.error(f"Falha ao capturar preco: {produto['nome']}")
        return

    #imprime o preço capturado
    log.info(f"Preco capturado: R$ {preco_atual:.2f}")

    preco_anterior = ultimo_preco(produto["id"])
    minimo = minimo_historico(produto["id"])
    config_alerta = produto["config_alerta"]

    salvar_preco(produto["id"], preco_atual)

    eh_minimo = minimo is not None and preco_atual < minimo

    deve_alertar = False
    if config_alerta is not None:
        # Alerta apenas quando o preço cruza o alvo vindo de cima (evita spam em dias consecutivos)
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
        except Exception as e:
            log.error(f"Erro ao enviar e-mail: {e}")
    else:
        log.info("Sem alerta. Historico atualizado.")

#função principal
def main():
    jitter()
    criar_tabelas()
    produtos = buscar_produtos_ativos()

    if not produtos:
        log.warning("Nenhum produto ativo encontrado no banco.")
        return

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        #itera sobre os produtos e processa cada um
        for produto in produtos:
            user_agent = random.choice(USER_AGENTS)
            context = browser.new_context(user_agent=user_agent)
            page = context.new_page()
            Stealth().apply_stealth_sync(page)

            try:
                processar_produto(page, produto)
            except Exception as e:
                log.error(f"Erro inesperado ao processar '{produto['nome']}': {e}")
            finally:
                context.close()

            time.sleep(random.randint(5, 20))

        browser.close()


if __name__ == "__main__":
    main()
