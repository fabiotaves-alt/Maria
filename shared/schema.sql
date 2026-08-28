-- ============================================================================
-- Schema unificado do banco de dados MARIA (SQLite compartilhado)
-- Padrão de nomenclatura: Português do Brasil
-- ============================================================================

PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

-- 1. Tabela: conversas (sessões de chat)
CREATE TABLE IF NOT EXISTS conversas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo TEXT NOT NULL DEFAULT 'Nova Conversa',
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Tabela: mensagens (histórico de cada conversa)
CREATE TABLE IF NOT EXISTS mensagens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversa_id INTEGER NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'system')),
    conteudo TEXT NOT NULL,
    anexos TEXT,  -- JSON com caminhos/metadados de anexos
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversa_id) REFERENCES conversas(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_mensagens_conversa 
ON mensagens(conversa_id);

-- 3. Tabela: memoria (fatos persistentes sobre o usuário - RAG)
CREATE TABLE IF NOT EXISTS memoria (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fato TEXT NOT NULL UNIQUE,
    categoria TEXT DEFAULT 'geral',  -- ex: 'pessoal', 'trabalho', 'preferencias'
    relevancia REAL DEFAULT 1.0,
    fonte TEXT DEFAULT 'manual',      -- ex: 'chat', 'arquivo', 'manual'
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_memoria_categoria 
ON memoria(categoria);

-- 4. Tabela: arquivos_indexados (metadados de arquivos processados)
CREATE TABLE IF NOT EXISTS arquivos_indexados (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    caminho TEXT NOT NULL UNIQUE,
    tipo TEXT NOT NULL,             -- 'excel', 'word', 'pdf', 'txt', 'audio'
    tamanho_bytes INTEGER,
    hash_checksum TEXT,             -- para detectar mudanças
    indexado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ultima_leitura TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_arquivos_tipo 
ON arquivos_indexados(tipo);

-- 5. Tabela: automacoes (automações salvas pelo usuário)
CREATE TABLE IF NOT EXISTS automacoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL UNIQUE,
    descricao TEXT,
    gatilho TEXT NOT NULL,
    acao TEXT NOT NULL,
    parametros TEXT,
    passos_json TEXT,               -- JSON com passos detalhados (opcional)
    ativo BOOLEAN DEFAULT 1,
    execucoes_count INTEGER DEFAULT 0,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ultima_execucao TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_automacoes_ativo 
ON automacoes(ativo);

-- 6. Tabela: configuracoes (preferências do usuário)
CREATE TABLE IF NOT EXISTS configuracoes (
    chave TEXT PRIMARY KEY,
    valor TEXT NOT NULL,
    descricao TEXT,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Configurações padrão iniciais
INSERT OR IGNORE INTO configuracoes (chave, valor, descricao)
VALUES 
    ('tema_escuro', 'true', 'Usar tema escuro na interface'),
    ('modelo_ollama', 'qwen3.5:4b', 'Modelo padrão do Ollama'),
    ('idioma', 'pt-BR', 'Idioma da interface'),
    ('notificacoes_som', 'true', 'Emitir sons de notificação');
