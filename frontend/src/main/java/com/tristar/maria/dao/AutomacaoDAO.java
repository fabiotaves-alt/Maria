package com.tristar.maria.dao;

import java.sql.*;
import java.util.ArrayList;
import java.util.List;

/**
 * DAO para gerenciamento de automações.
 * Responsável por persistir e recuperar automações da tabela 'automacoes'.
 */
public class AutomacaoDAO {
    
    private final Connection connection;
    
    public AutomacaoDAO(Connection connection) {
        this.connection = connection;
    }
    
    /**
     * Cria uma nova automação.
     */
    public void criarAutomacao(String nome, String gatilho, String acao, boolean ativa) throws SQLException {
        String sql = "INSERT INTO automacoes (nome, gatilho, acao, ativa, created_at) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)";
        try (PreparedStatement stmt = connection.prepareStatement(sql)) {
            stmt.setString(1, nome);
            stmt.setString(2, gatilho);
            stmt.setString(3, acao);
            stmt.setBoolean(4, ativa);
            stmt.executeUpdate();
        }
    }
    
    /**
     * Recupera todas as automações.
     */
    public List<Automacao> getTodasAutomacoes() throws SQLException {
        String sql = "SELECT id, nome, gatilho, acao, ativa, created_at FROM automacoes ORDER BY created_at DESC";
        List<Automacao> automacoes = new ArrayList<>();
        
        try (PreparedStatement stmt = connection.prepareStatement(sql)) {
            ResultSet rs = stmt.executeQuery();
            
            while (rs.next()) {
                Automacao automacao = new Automacao(
                    rs.getLong("id"),
                    rs.getString("nome"),
                    rs.getString("gatilho"),
                    rs.getString("acao"),
                    rs.getBoolean("ativa"),
                    rs.getTimestamp("created_at")
                );
                automacoes.add(automacao);
            }
        }
        return automacoes;
    }
    
    /**
     * Recupera apenas as automações ativas.
     */
    public List<Automacao> getAutomacoesAtivas() throws SQLException {
        String sql = "SELECT id, nome, gatilho, acao, ativa, created_at FROM automacoes WHERE ativa = 1 ORDER BY created_at DESC";
        List<Automacao> automacoes = new ArrayList<>();
        
        try (PreparedStatement stmt = connection.prepareStatement(sql)) {
            ResultSet rs = stmt.executeQuery();
            
            while (rs.next()) {
                Automacao automacao = new Automacao(
                    rs.getLong("id"),
                    rs.getString("nome"),
                    rs.getString("gatilho"),
                    rs.getString("acao"),
                    rs.getBoolean("ativa"),
                    rs.getTimestamp("created_at")
                );
                automacoes.add(automacao);
            }
        }
        return automacoes;
    }
    
    /**
     * Atualiza uma automação existente.
     */
    public void atualizarAutomacao(Long id, String nome, String gatilho, String acao, Boolean ativa) throws SQLException {
        StringBuilder sql = new StringBuilder("UPDATE automacoes SET ");
        List<Object> params = new ArrayList<>();
        
        if (nome != null) {
            sql.append("nome = ?, ");
            params.add(nome);
        }
        if (gatilho != null) {
            sql.append("gatilho = ?, ");
            params.add(gatilho);
        }
        if (acao != null) {
            sql.append("acao = ?, ");
            params.add(acao);
        }
        if (ativa != null) {
            sql.append("ativa = ?, ");
            params.add(ativa ? 1 : 0);
        }
        
        // Remove última vírgula e espaço
        String sqlStr = sql.toString();
        if (sqlStr.endsWith(", ")) {
            sqlStr = sqlStr.substring(0, sqlStr.length() - 2);
        }
        
        sqlStr += " WHERE id = ?";
        
        try (PreparedStatement stmt = connection.prepareStatement(sqlStr)) {
            for (int i = 0; i < params.size(); i++) {
                stmt.setObject(i + 1, params.get(i));
            }
            stmt.setLong(params.size() + 1, id);
            stmt.executeUpdate();
        }
    }
    
    /**
     * Deleta uma automação pelo ID.
     */
    public void deletarAutomacao(Long id) throws SQLException {
        String sql = "DELETE FROM automacoes WHERE id = ?";
        try (PreparedStatement stmt = connection.prepareStatement(sql)) {
            stmt.setLong(1, id);
            stmt.executeUpdate();
        }
    }
    
    /**
     * Ativa ou desativa uma automação.
     */
    public void toggleAtiva(Long id, boolean ativa) throws SQLException {
        String sql = "UPDATE automacoes SET ativa = ? WHERE id = ?";
        try (PreparedStatement stmt = connection.prepareStatement(sql)) {
            stmt.setBoolean(1, ativa);
            stmt.setLong(2, id);
            stmt.executeUpdate();
        }
    }
    
    /**
     * Conta o total de automações.
     */
    public int contarAutomacoes() throws SQLException {
        String sql = "SELECT COUNT(*) as total FROM automacoes";
        try (PreparedStatement stmt = connection.prepareStatement(sql)) {
            ResultSet rs = stmt.executeQuery();
            if (rs.next()) {
                return rs.getInt("total");
            }
        }
        return 0;
    }
    
    /**
     * Busca automações por nome (LIKE).
     */
    public List<Automacao> buscarPorNome(String termo) throws SQLException {
        String sql = "SELECT id, nome, gatilho, acao, ativa, created_at FROM automacoes WHERE nome LIKE ? ORDER BY created_at DESC";
        List<Automacao> automacoes = new ArrayList<>();
        
        try (PreparedStatement stmt = connection.prepareStatement(sql)) {
            stmt.setString(1, "%" + termo + "%");
            ResultSet rs = stmt.executeQuery();
            
            while (rs.next()) {
                Automacao automacao = new Automacao(
                    rs.getLong("id"),
                    rs.getString("nome"),
                    rs.getString("gatilho"),
                    rs.getString("acao"),
                    rs.getBoolean("ativa"),
                    rs.getTimestamp("created_at")
                );
                automacoes.add(automacao);
            }
        }
        return automacoes;
    }
    
    /**
     * Classe interna que representa uma automação.
     */
    public static class Automacao {
        private final Long id;
        private final String nome;
        private final String gatilho;
        private final String acao;
        private final boolean ativa;
        private final Timestamp createdAt;
        
        public Automacao(Long id, String nome, String gatilho, String acao, boolean ativa, Timestamp createdAt) {
            this.id = id;
            this.nome = nome;
            this.gatilho = gatilho;
            this.acao = acao;
            this.ativa = ativa;
            this.createdAt = createdAt;
        }
        
        public Long getId() { return id; }
        public String getNome() { return nome; }
        public String getGatilho() { return gatilho; }
        public String getAcao() { return acao; }
        public boolean isAtiva() { return ativa; }
        public Timestamp getCreatedAt() { return createdAt; }
    }
}
