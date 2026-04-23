from datetime import datetime, timedelta
import core.database as db


def _produto(nome="Produto Teste", url="https://exemplo.com/p1", loja="amazon", config_alerta=None):
    return db.inserir_produto(nome, url, loja, config_alerta)


def test_inserir_produto_retorna_id():
    pid = _produto()
    assert isinstance(pid, int) and pid > 0


def test_buscar_produtos_ativos():
    _produto(url="https://a.com/1")
    _produto(url="https://a.com/2")
    ativos = db.buscar_produtos_ativos()
    assert len(ativos) == 2


def test_produto_inativo_nao_retorna():
    pid = _produto()
    with db.get_connection() as conn:
        conn.execute("UPDATE produtos SET ativo = 0 WHERE id = ?", (pid,))
    assert len(db.buscar_produtos_ativos()) == 0


def test_ultimo_preco_sem_historico_retorna_none():
    pid = _produto()
    assert db.ultimo_preco(pid) is None


def test_salvar_e_recuperar_ultimo_preco():
    pid = _produto()
    db.salvar_preco(pid, 299.90)
    db.salvar_preco(pid, 249.90)
    assert db.ultimo_preco(pid) == 249.90


def test_minimo_historico():
    pid = _produto()
    for preco in [500.0, 300.0, 450.0, 280.0, 320.0]:
        db.salvar_preco(pid, preco)
    assert db.minimo_historico(pid) == 280.0


def test_minimo_historico_sem_historico_retorna_none():
    pid = _produto()
    assert db.minimo_historico(pid) is None


def test_historico_precos_produto_ordem_crescente():
    pid = _produto()
    precos = [100.0, 90.0, 85.0]
    for p in precos:
        db.salvar_preco(pid, p)
    historico = db.historico_precos_produto(pid)
    assert [r["preco"] for r in historico] == precos


def test_historico_precos_produto_respeita_janela_dias():
    pid = _produto()
    db.salvar_preco(pid, 200.0)
    # Insere registro antigo (70 dias atrás) diretamente
    data_antiga = (datetime.now() - timedelta(days=70)).isoformat()
    with db.get_connection() as conn:
        conn.execute(
            "INSERT INTO historico_precos (produto_id, preco, data_captura) VALUES (?, ?, ?)",
            (pid, 999.0, data_antiga),
        )
    historico = db.historico_precos_produto(pid, dias=60)
    assert all(r["preco"] != 999.0 for r in historico)


def test_config_alerta_salvo_e_recuperado():
    pid = db.inserir_produto("X", "https://x.com", "magalu", config_alerta=350.0)
    produto = next(p for p in db.buscar_produtos_ativos() if p["id"] == pid)
    assert produto["config_alerta"] == 350.0
