from app.db.session import normalize_database_url


def test_postgres_urls_use_psycopg3_driver():
    assert normalize_database_url("postgresql://user:pass@host/db") == "postgresql+psycopg://user:pass@host/db"
    assert normalize_database_url("postgres://user:pass@host/db") == "postgresql+psycopg://user:pass@host/db"


def test_explicit_or_sqlite_urls_are_left_unchanged():
    assert normalize_database_url("postgresql+psycopg://user:pass@host/db") == "postgresql+psycopg://user:pass@host/db"
    assert normalize_database_url("sqlite:///./creatoros.db") == "sqlite:///./creatoros.db"
