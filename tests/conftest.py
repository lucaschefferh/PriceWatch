import pytest
import core.database as db


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    """Redireciona todas as operações de BD para um arquivo temporário por teste."""
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "test.db"))
    db.criar_tabelas()
