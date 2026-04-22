"""
Uso: python adicionar_produto.py
Cadastra um novo produto no banco de dados de forma interativa.
"""
from core.database import criar_tabelas, inserir_produto

LOJAS_VALIDAS = ["amazon", "inthebox", "magalu", "mercadolivre"]


def main():
    criar_tabelas()

    print("=== PriceWatch — Adicionar Produto ===\n")

    nome = input("Nome do produto: ").strip()
    url = input("URL do produto: ").strip()

    print(f"Lojas disponíveis: {', '.join(LOJAS_VALIDAS)}")
    loja = input("Loja: ").strip().lower()

    if loja not in LOJAS_VALIDAS:
        print(f"Loja invalida. Escolha entre: {', '.join(LOJAS_VALIDAS)}")
        return

    alerta_input = input("Valor de alerta personalizado (deixe em branco para ignorar): ").strip()
    config_alerta = float(alerta_input.replace(",", ".")) if alerta_input else None

    produto_id = inserir_produto(nome, url, loja, config_alerta)
    print(f"\nProduto cadastrado com sucesso! ID: {produto_id}")


if __name__ == "__main__":
    main()
