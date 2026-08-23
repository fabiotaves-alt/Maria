def test_tabelas_criadas(conn):
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tabelas = {row[0] for row in cursor.fetchall()}
    esperadas = {
        "conversas", "mensagens", "memoria",
        "arquivos_indexados", "automacoes", "configuracoes",
    }
    assert esperadas.issubset(tabelas)


def test_idempotencia(conn):
    from database.schema import init_db
    init_db(conn)  # segunda chamada não deve falhar
    test_tabelas_criadas(conn)