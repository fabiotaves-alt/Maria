"""
Schema do banco de dados MARIA — SQLite compartilhado.

Tabelas:
- conversas: sessões de conversa (histórico)
- mensagens: mensagens individuais (vinculadas a conversas)
- memoria: fatos persistentes sobre o usuário (RAG)
- arquivos_indexados: metadados de arquivos processados
- automacoes: automações salvas pelo usuário
- configuracoes: preferências (tema, modelo, etc.)

Nota: Este módulo é usado tanto pelo backend Python quanto pode ser
consultado pelo frontend Java via JDBC para leitura/escrita compartilhada.
Para evitar conflitos de escrita concorrente:
- Backend Python escreve em: conversas, mensagens, memoria, arquivos_indexados
- Frontend Java lê todas as tabelas e escreve em: configuracoes, automacoes
- WAL mode já está ativo em connection.py para permitir leituras simultâneas
"""

from database.connection import get_connection


def init_db():
    """Cria as tabelas se não existirem."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Tabela: conversas (sessões de chat)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL DEFAULT 'Nova Conversa',
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Tabela: mensagens (histórico de cada conversa)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mensagens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversa_id INTEGER NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
            conteudo TEXT NOT NULL,
            anexos TEXT,  -- JSON com caminhos de arquivos anexados
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (conversa_id) REFERENCES conversas(id) ON DELETE CASCADE
        )
    """)
    
    # Índice para busca rápida por conversa
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_mensagens_conversa 
        ON mensagens(conversa_id)
    """)
    
    # Tabela: memoria (fatos persistentes sobre o usuário - RAG)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS memoria (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fato TEXT NOT NULL UNIQUE,
            categoria TEXT,  -- ex: 'pessoal', 'trabalho', 'preferencias'
            relevancia REAL DEFAULT 1.0,
            fonte TEXT,  -- origem do fato (ex: 'chat', 'arquivo', 'manual')
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Tabela: arquivos_indexados (metadados de arquivos processados)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS arquivos_indexados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            caminho TEXT NOT NULL UNIQUE,
            tipo TEXT NOT NULL,  -- 'excel', 'word', 'pdf', 'txt', 'audio'
            tamanho_bytes INTEGER,
            hash_checksum TEXT,  -- para detectar mudanças
            indexado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ultima_leitura TIMESTAMP
        )
    """)
    
    # Tabela: automacoes (automações salvas pelo usuário)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS automacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE,
            descricao TEXT,
            passos_json TEXT NOT NULL,  -- JSON com sequência de ações
            gatilho TEXT,  -- comando ou evento que dispara
            ativo BOOLEAN DEFAULT 1,
            execucoes_count INTEGER DEFAULT 0,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ultima_execucao TIMESTAMP
        )
    """)
    
    # Tabela: configuracoes (preferências do usuário)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS configuracoes (
            chave TEXT PRIMARY KEY,
            valor TEXT NOT NULL,
            descricao TEXT,
            atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Inserir configurações padrão
    cursor.execute("""
        INSERT OR IGNORE INTO configuracoes (chave, valor, descricao)
        VALUES 
            ('tema_escuro', 'true', 'Usar tema escuro na interface'),
            ('modelo_ollama', 'qwen3.5:4b', 'Modelo padrão do Ollama'),
            ('idioma', 'pt-BR', 'Idioma da interface'),
            ('notificacoes_som', 'true', 'Emitir sons de notificação')
    """)
    
    conn.commit()
    conn.close()


def limpar_tudo():
    """Reseta o banco de dados (apenas para testes/desenvolvimento)."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("DROP TABLE IF EXISTS mensagens")
    cursor.execute("DROP TABLE IF EXISTS automacoes")
    cursor.execute("DROP TABLE IF EXISTS arquivos_indexados")
    cursor.execute("DROP TABLE IF EXISTS memoria")
    cursor.execute("DROP TABLE IF EXISTS configuracoes")
    cursor.execute("DROP TABLE IF EXISTS conversas")
    
    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    print("✅ Banco de dados inicializado com sucesso!")
    print("📁 Local: shared/maria.db")
