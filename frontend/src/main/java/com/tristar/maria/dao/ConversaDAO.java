package com.tristar.maria.dao;

import java.sql.*;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

/**
 * DAO para gerenciamento de conversas no banco de dados SQLite.
 * Responsável por persistir e recuperar mensagens da tabela 'conversas'.
 */
public class ConversaDAO {
    
    private final Connection connection;
    
    public ConversaDAO(Connection connection) {
        this.connection = connection;
    }
    
    /**
     * Salva uma nova mensagem na conversa.
     */
    public void salvarMensagem(String role, String content, String sessionId) throws SQLException {
        String sql = "INSERT INTO conversas (role, content, session_id, created_at) VALUES (?, ?, ?, CURRENT_TIMESTAMP)";
        try (PreparedStatement stmt = connection.prepareStatement(sql)) {
            stmt.setString(1, role);
            stmt.setString(2, content);
            stmt.setString(3, sessionId);
            stmt.executeUpdate();
        }
    }
    
    /**
     * Recupera todas as mensagens de uma sessão específica.
     */
    public List<Mensagem> getMensagensPorSessao(String sessionId) throws SQLException {
        String sql = "SELECT id, role, content, session_id, created_at FROM conversas WHERE session_id = ? ORDER BY created_at ASC";
        List<Mensagem> mensagens = new ArrayList<>();
        
        try (PreparedStatement stmt = connection.prepareStatement(sql)) {
            stmt.setString(1, sessionId);
            ResultSet rs = stmt.executeQuery();
            
            while (rs.next()) {
                Mensagem msg = new Mensagem(
                    rs.getLong("id"),
                    rs.getString("role"),
                    rs.getString("content"),
                    rs.getString("session_id"),
                    rs.getTimestamp("created_at")
                );
                mensagens.add(msg);
            }
        }
        return mensagens;
    }
    
    /**
     * Deleta todas as mensagens de uma sessão.
     */
    public void limparSessao(String sessionId) throws SQLException {
        String sql = "DELETE FROM conversas WHERE session_id = ?";
        try (PreparedStatement stmt = connection.prepareStatement(sql)) {
            stmt.setString(1, sessionId);
            stmt.executeUpdate();
        }
    }
    
    /**
     * Conta o número de mensagens em uma sessão.
     */
    public int contarMensagens(String sessionId) throws SQLException {
        String sql = "SELECT COUNT(*) as total FROM conversas WHERE session_id = ?";
        try (PreparedStatement stmt = connection.prepareStatement(sql)) {
            stmt.setString(1, sessionId);
            ResultSet rs = stmt.executeQuery();
            if (rs.next()) {
                return rs.getInt("total");
            }
        }
        return 0;
    }
    
    /**
     * Classe interna que representa uma mensagem.
     */
    public static class Mensagem {
        private final Long id;
        private final String role;
        private final String content;
        private final String sessionId;
        private final Timestamp createdAt;
        
        public Mensagem(Long id, String role, String content, String sessionId, Timestamp createdAt) {
            this.id = id;
            this.role = role;
            this.content = content;
            this.sessionId = sessionId;
            this.createdAt = createdAt;
        }
        
        public Long getId() { return id; }
        public String getRole() { return role; }
        public String getContent() { return content; }
        public String getSessionId() { return sessionId; }
        public Timestamp getCreatedAt() { return createdAt; }
    }
}
