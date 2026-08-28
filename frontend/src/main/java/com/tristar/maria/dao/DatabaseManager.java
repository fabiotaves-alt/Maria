package com.tristar.maria.dao;

import java.io.File;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.sql.*;

/**
 * Gerenciador de conexão com o banco de dados SQLite unificado do MARIA.
 * Responsável por gerenciar a conexão JDBC com 'shared/maria.db' e inicializar o schema.
 */
public class DatabaseManager {
    
    private Connection connection;
    private static DatabaseManager instance;
    
    private DatabaseManager() {}
    
    /**
     * Obtém a instância singleton do DatabaseManager.
     */
    public static synchronized DatabaseManager getInstance() {
        if (instance == null) {
            instance = new DatabaseManager();
        }
        return instance;
    }
    
    /**
     * Resolve o caminho absoluto para o banco SQLite compartilhado 'shared/maria.db'.
     */
    public static Path resolverCaminhoBanco() {
        Path atual = Paths.get("").toAbsolutePath().normalize();
        if (atual.endsWith("frontend")) {
            return atual.getParent().resolve("shared").resolve("maria.db");
        }
        return atual.resolve("shared").resolve("maria.db");
    }
    
    /**
     * Retorna a URL JDBC para o SQLite.
     */
    public static String getJdbcUrl() {
        Path caminhoBanco = resolverCaminhoBanco();
        File pastaPai = caminhoBanco.getParent().toFile();
        if (!pastaPai.exists()) {
            pastaPai.mkdirs();
        }
        return "jdbc:sqlite:" + caminhoBanco.toString().replace("\\", "/");
    }
    
    /**
     * Conecta ao banco de dados e aplica PRAGMAs recomendados (WAL, foreign keys).
     */
    public synchronized Connection conectar() throws SQLException {
        if (connection == null || connection.isClosed()) {
            connection = DriverManager.getConnection(getJdbcUrl());
            connection.setAutoCommit(true);
            try (Statement pragmaStmt = connection.createStatement()) {
                pragmaStmt.execute("PRAGMA foreign_keys = ON;");
                pragmaStmt.execute("PRAGMA journal_mode = WAL;");
            }
        }
        return connection;
    }
    
    /**
     * Fecha a conexão com o banco de dados.
     */
    public synchronized void fechar() {
        if (connection != null) {
            try {
                connection.close();
            } catch (SQLException e) {
                System.err.println("Erro ao fechar conexão SQLite: " + e.getMessage());
            }
            connection = null;
        }
    }
    
    /**
     * Inicializa todas as tabelas do banco de dados conforme o schema unificado em shared/schema.sql.
     */
    public void inicializarTabelas() throws SQLException {
        Connection conn = conectar();
        try (Statement stmt = conn.createStatement()) {
            
            // 1. Tabela: conversas (sessões de chat)
            stmt.execute("""
                CREATE TABLE IF NOT EXISTS conversas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    titulo TEXT NOT NULL DEFAULT 'Nova Conversa',
                    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """);
            
            // 2. Tabela: mensagens (histórico de cada conversa)
            stmt.execute("""
                CREATE TABLE IF NOT EXISTS mensagens (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversa_id INTEGER NOT NULL,
                    role TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'system')),
                    conteudo TEXT NOT NULL,
                    anexos TEXT,
                    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (conversa_id) REFERENCES conversas(id) ON DELETE CASCADE
                )
            """);
            
            // 3. Tabela: memoria (fatos persistentes sobre o usuário - RAG)
            stmt.execute("""
                CREATE TABLE IF NOT EXISTS memoria (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fato TEXT NOT NULL UNIQUE,
                    categoria TEXT DEFAULT 'geral',
                    relevancia REAL DEFAULT 1.0,
                    fonte TEXT DEFAULT 'manual',
                    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """);
            
            // 4. Tabela: arquivos_indexados (metadados de arquivos processados)
            stmt.execute("""
                CREATE TABLE IF NOT EXISTS arquivos_indexados (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    caminho TEXT NOT NULL UNIQUE,
                    tipo TEXT NOT NULL,
                    tamanho_bytes INTEGER,
                    hash_checksum TEXT,
                    indexado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ultima_leitura TIMESTAMP
                )
            """);
            
            // 5. Tabela: automacoes (automações salvas pelo usuário)
            stmt.execute("""
                CREATE TABLE IF NOT EXISTS automacoes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL UNIQUE,
                    descricao TEXT,
                    gatilho TEXT NOT NULL,
                    acao TEXT NOT NULL,
                    parametros TEXT,
                    passos_json TEXT,
                    ativo BOOLEAN DEFAULT 1,
                    execucoes_count INTEGER DEFAULT 0,
                    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ultima_execucao TIMESTAMP
                )
            """);
            
            // 6. Tabela: configuracoes (preferências do usuário)
            stmt.execute("""
                CREATE TABLE IF NOT EXISTS configuracoes (
                    chave TEXT PRIMARY KEY,
                    valor TEXT NOT NULL,
                    descricao TEXT,
                    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """);
            
            // Migrações preventivas para bancos locais existentes
            garantirColuna(conn, "configuracoes", "descricao", "TEXT");
            garantirColuna(conn, "memoria", "fato", "TEXT");
            garantirColuna(conn, "memoria", "fonte", "TEXT DEFAULT 'manual'");
            garantirColuna(conn, "automacoes", "descricao", "TEXT");
            garantirColuna(conn, "automacoes", "passos_json", "TEXT");
            garantirColuna(conn, "automacoes", "execucoes_count", "INTEGER DEFAULT 0");
            garantirColuna(conn, "automacoes", "ultima_execucao", "TIMESTAMP");
            
            // Inserir configurações padrão iniciais
            stmt.execute("""
                INSERT OR IGNORE INTO configuracoes (chave, valor, descricao)
                VALUES 
                    ('tema_escuro', 'true', 'Usar tema escuro na interface'),
                    ('modelo_ollama', 'qwen3.5:4b', 'Modelo padrão do Ollama'),
                    ('idioma', 'pt-BR', 'Idioma da interface'),
                    ('notificacoes_som', 'true', 'Emitir sons de notificação')
            """);
            
            // Índices de performance
            stmt.execute("CREATE INDEX IF NOT EXISTS idx_mensagens_conversa ON mensagens(conversa_id)");
            stmt.execute("CREATE INDEX IF NOT EXISTS idx_memoria_categoria ON memoria(categoria)");
            stmt.execute("CREATE INDEX IF NOT EXISTS idx_arquivos_tipo ON arquivos_indexados(tipo)");
            stmt.execute("CREATE INDEX IF NOT EXISTS idx_automacoes_ativo ON automacoes(ativo)");
        }
    }
    
    private void garantirColuna(Connection conn, String tabela, String coluna, String tipo) {
        try (Statement stmt = conn.createStatement()) {
            stmt.execute("ALTER TABLE " + tabela + " ADD COLUMN " + coluna + " " + tipo);
        } catch (SQLException ignored) {
            // Coluna já existe
        }
    }
    
    /**
     * Obtém um ConversaDAO para operar nas tabelas de conversas e mensagens.
     */
    public ConversaDAO getConversaDAO() throws SQLException {
        return new ConversaDAO(conectar());
    }
    
    /**
     * Obtém um MemoriaDAO para operar na tabela de memórias.
     */
    public MemoriaDAO getMemoriaDAO() throws SQLException {
        return new MemoriaDAO(conectar());
    }
    
    /**
     * Obtém um AutomacaoDAO para operar na tabela de automações.
     */
    public AutomacaoDAO getAutomacaoDAO() throws SQLException {
        return new AutomacaoDAO(conectar());
    }
    
    /**
     * Obtém um ConfiguracaoDAO para operar na tabela de configurações.
     */
    public ConfiguracaoDAO getConfiguracaoDAO() throws SQLException {
        return new ConfiguracaoDAO(conectar());
    }
}
