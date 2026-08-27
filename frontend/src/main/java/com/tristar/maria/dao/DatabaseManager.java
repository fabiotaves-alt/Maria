package com.tristar.maria.dao;

import java.sql.*;
import java.util.Optional;

/**
 * Gerenciador de conexão com o banco de dados SQLite.
 * Responsável por criar e gerenciar a conexão com o banco de dados.
 */
public class DatabaseManager {
    
    private static final String DB_URL = "jdbc:sqlite:./maria.db";
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
            
            // Tabela de conversas
            stmt.execute("""
                CREATE TABLE IF NOT EXISTS conversas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """);
            
            // Tabela de memórias
            stmt.execute("""
                CREATE TABLE IF NOT EXISTS memorias (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conteudo TEXT NOT NULL,
                    categoria TEXT DEFAULT 'geral',
                    origem TEXT DEFAULT 'manual',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """);
            
            // Tabela de automações
            stmt.execute("""
                CREATE TABLE IF NOT EXISTS automacoes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    gatilho TEXT NOT NULL,
                    acao TEXT NOT NULL,
                    ativa BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """);
            
            // Tabela de configurações
            stmt.execute("""
                CREATE TABLE IF NOT EXISTS configuracoes (
                    chave TEXT PRIMARY KEY,
                    valor TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """);
            
            // Tabela de arquivos
            stmt.execute("""
                CREATE TABLE IF NOT EXISTS arquivos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    caminho TEXT NOT NULL,
                    tipo TEXT NOT NULL,
                    tamanho_bytes INTEGER,
                    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """);
            
            // Tabela de logs
            stmt.execute("""
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nivel TEXT NOT NULL,
                    mensagem TEXT NOT NULL,
                    contexto TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """);
            
            // Índices para melhor performance
            stmt.execute("CREATE INDEX IF NOT EXISTS idx_conversas_session ON conversas(session_id)");
            stmt.execute("CREATE INDEX IF NOT EXISTS idx_conversas_created ON conversas(created_at)");
            stmt.execute("CREATE INDEX IF NOT EXISTS idx_memorias_categoria ON memorias(categoria)");
            stmt.execute("CREATE INDEX IF NOT EXISTS idx_automacoes_ativa ON automacoes(ativa)");
            stmt.execute("CREATE INDEX IF NOT EXISTS idx_arquivos_tipo ON arquivos(tipo)");
            stmt.execute("CREATE INDEX IF NOT EXISTS idx_logs_nivel ON logs(nivel)");
            
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
