import sqlite3
import os
from datetime import datetime
from dotenv import load_dotenv


#carrega .env e passa para a variável DB_PATH
load_dotenv()

DB_PATH = os.getenv("DB_PATH", "data/prices.db")

#cria conexão com o banco
def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

#função para criar as tabelas dentro do banco de dados
def criar_tabelas():
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS produtos (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                nome          TEXT NOT NULL,
                url           TEXT NOT NULL UNIQUE,
                loja          TEXT NOT NULL,
                config_alerta REAL,
                ativo         BOOLEAN NOT NULL DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS historico_precos (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                produto_id    INTEGER NOT NULL,
                preco         REAL NOT NULL,
                data_captura  DATETIME NOT NULL,
                FOREIGN KEY (produto_id) REFERENCES produtos(id)
            );
        """)


#Função para inserir o produto no banco de dados
def inserir_produto(nome: str, url: str, loja: str, config_alerta: float = None) -> int:
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO produtos (nome, url, loja, config_alerta) VALUES (?, ?, ?, ?)",
            (nome, url, loja, config_alerta),
        )
        return cursor.lastrowid

#função que retorna os produtos que estão sendo atualizados
def buscar_produtos_ativos() -> list[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM produtos WHERE ativo = 1"
        ).fetchall()


#função para salvar o preço do produto
def salvar_preco(produto_id: int, preco: float):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO historico_precos (produto_id, preco, data_captura) VALUES (?, ?, ?)",
            (produto_id, preco, datetime.now().isoformat()),
        )

#retorna o ultimo preço do produto desejado
def ultimo_preco(produto_id: int) -> float | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT preco FROM historico_precos WHERE produto_id = ? ORDER BY data_captura DESC LIMIT 1",
            (produto_id,),
        ).fetchone()
        return row["preco"] if row else None

#retorna o histórico de preços dos últimos N dias para gerar o gráfico
def historico_precos_produto(produto_id: int, dias: int = 60) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT preco, data_captura FROM historico_precos
               WHERE produto_id = ? AND data_captura >= datetime('now', ?)
               ORDER BY data_captura ASC""",
            (produto_id, f"-{dias} days"),
        ).fetchall()
        return [dict(r) for r in rows]

#retorna o menor preço já registrado para o produto
def minimo_historico(produto_id: int) -> float | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT MIN(preco) as minimo FROM historico_precos WHERE produto_id = ?",
            (produto_id,),
        ).fetchone()
        return row["minimo"] if row and row["minimo"] is not None else None

#retorna a média semestral do produto
def media_semestral(produto_id: int) -> float | None:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT AVG(preco) as media FROM historico_precos
            WHERE produto_id = ?
              AND data_captura >= datetime('now', '-6 months')
            """,
            (produto_id,),
        ).fetchone()
        return row["media"] if row else None
