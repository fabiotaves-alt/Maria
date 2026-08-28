package com.tristar.maria.dao;

import java.sql.*;
import java.util.Optional;

/**
 * Gerenciador de conexão com o banco de dados SQLite.
 * Responsável por criar e gerenciar a conexão com o banco de dados.
 */
public class DatabaseManager {
    
    private static final String DB_URL = "jdbc:sqlite:../shared/maria.db";
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
     * Conecta ao banco de dados e inicializa as tabelas se necessário.
     */
    public synchronized Connection conectar() throws SQLException {
        if (connection == null || connection.isClosed()) {
            connection = DriverManager.getConnection(DB_URL);
            connection.setAutoCommit(true);
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
                System.err.println("Erro ao fechar conexão: " + e.getMessage());
            }
            connection = null;
        }
    }
    
    /**
     * Inicializa todas as tabelas do banco de dados.
     */
    public void inicializarTabelas() throws SQLException {
        Connection conn = conectar();
        try (Statement stmt = conn.createStatement()) {
            
            // Tabela de conversas (compatível com backend)
            stmt.execute("""
                CREATE TABLE IF NOT EXISTS conversas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sessao_id TEXT NOT NULL,
                    titulo TEXT DEFAULT 'Conversa',
                    data_inicio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    data_fim TIMESTAMP
                )
            """);
            
            // Tabela de mensagens (compatível com backend)
            stmt.execute("""
                CREATE TABLE IF NOT EXISTS mensagens (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversa_id INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    conteudo TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    anexos TEXT,
                    FOREIGN KEY (conversa_id) REFERENCES conversas(id)
                )
            """);
            
            // Tabela de memória (compatível com backend)
            stmt.execute("""
                CREATE TABLE IF NOT EXISTS memoria (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    categoria TEXT DEFAULT 'geral',
                    conteudo TEXT NOT NULL,
                    relevancia REAL DEFAULT 1.0,
                    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """);
            
            // Tabela de arquivos indexados (compatível com backend)
            stmt.execute("""
                CREATE TABLE IF NOT EXISTS arquivos_indexados (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    caminho TEXT NOT NULL UNIQUE,
                    tipo TEXT NOT NULL,
                    metadata TEXT,
                    data_indexacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """);
            
            // Tabela de automações (compatível com backend)
            stmt.execute("""
                CREATE TABLE IF NOT EXISTS automacoes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    gatilho TEXT NOT NULL,
                    acao TEXT NOT NULL,
                    parametros TEXT,
                    ativo BOOLEAN DEFAULT 1
                )
            """);
            
            // Tabela de configurações (compatível com backend)
            stmt.execute("""
                CREATE TABLE IF NOT EXISTS configuracoes (
                    chave TEXT PRIMARY KEY,
                    valor TEXT NOT NULL,
                    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """);
            
            // Índices para melhor performance
            stmt.execute("CREATE INDEX IF NOT EXISTS idx_conversas_sessao ON conversas(sessao_id)");
            stmt.execute("CREATE INDEX IF NOT EXISTS idx_mensagens_conversa ON mensagens(conversa_id)");
            stmt.execute("CREATE INDEX IF NOT EXISTS idx_memoria_categoria ON memoria(categoria)");
            stmt.execute("CREATE INDEX IF NOT EXISTS idx_arquivos_tipo ON arquivos_indexados(tipo)");
            stmt.execute("CREATE INDEX IF NOT EXISTS idx_automacoes_ativo ON automacoes(ativo)");
            
        }
    }
    
    /**
     * Obtém um ConversaDAO para operar na tabela de conversas.
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
