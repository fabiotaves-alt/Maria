package com.tristar.maria.dao;

import java.sql.*;
import java.util.ArrayList;
import java.util.List;

/**
 * DAO para gerenciamento de conversas e mensagens no banco de dados SQLite.
 * Opera sobre as tabelas 'conversas' e 'mensagens' (schema unificado).
 */
public class ConversaDAO {
    
    private final Connection connection;
    
    public ConversaDAO(Connection connection) {
        this.connection = connection;
    }
    
    /**
     * Cria uma nova conversa e retorna seu ID.
     */
    public long criarConversa(String titulo) throws SQLException {
        String sql = "INSERT INTO conversas (titulo, criado_em, atualizado_em) VALUES (?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)";
        try (PreparedStatement stmt = connection.prepareStatement(sql, Statement.RETURN_GENERATED_KEYS)) {
            stmt.setString(1, (titulo != null && !titulo.isBlank()) ? titulo : "Nova Conversa");
            stmt.executeUpdate();
            try (ResultSet rs = stmt.getGeneratedKeys()) {
                if (rs.next()) {
                    return rs.getLong(1);
                }
            }
        }
        return 1L;
    }
    
    /**
     * Obtém a conversa mais recente ou cria uma nova se nenhuma existir.
     */
    public long obterOuCriarConversaAtiva() throws SQLException {
        String sql = "SELECT id FROM conversas ORDER BY atualizado_em DESC, id DESC LIMIT 1";
        try (Statement stmt = connection.createStatement();
             ResultSet rs = stmt.executeQuery(sql)) {
            if (rs.next()) {
                return rs.getLong("id");
            }
        }
        return criarConversa("Nova Conversa");
    }
    
    /**
     * Salva uma mensagem vinculada a uma conversa.
     */
    public void salvarMensagem(long conversaId, String role, String conteudo, String anexos) throws SQLException {
        String sql = "INSERT INTO mensagens (conversa_id, role, conteudo, anexos, criado_em) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)";
        try (PreparedStatement stmt = connection.prepareStatement(sql)) {
            stmt.setLong(1, conversaId);
            stmt.setString(2, role != null ? role : "user");
            stmt.setString(3, conteudo != null ? conteudo : "");
            stmt.setString(4, anexos);
            stmt.executeUpdate();
        }
        // Atualiza timestamp da conversa pai
        String updateSql = "UPDATE conversas SET atualizado_em = CURRENT_TIMESTAMP WHERE id = ?";
        try (PreparedStatement stmt = connection.prepareStatement(updateSql)) {
            stmt.setLong(1, conversaId);
            stmt.executeUpdate();
        }
    }
    
    /**
     * Sobrecarga de compatibilidade para salvar mensagem.
     */
    public void salvarMensagem(String role, String content, String sessionId) throws SQLException {
        long conversaId = obterOuCriarConversaAtiva();
        salvarMensagem(conversaId, role, content, null);
    }
    
    /**
     * Recupera todas as mensagens de uma conversa.
     */
    public List<Mensagem> getMensagensPorConversa(long conversaId) throws SQLException {
        String sql = "SELECT id, conversa_id, role, conteudo, anexos, criado_em FROM mensagens WHERE conversa_id = ? ORDER BY criado_em ASC, id ASC";
        List<Mensagem> mensagens = new ArrayList<>();
        
        try (PreparedStatement stmt = connection.prepareStatement(sql)) {
            stmt.setLong(1, conversaId);
            try (ResultSet rs = stmt.executeQuery()) {
                while (rs.next()) {
                    Mensagem msg = new Mensagem(
                        rs.getLong("id"),
                        rs.getLong("conversa_id"),
                        rs.getString("role"),
                        rs.getString("conteudo"),
                        rs.getString("anexos"),
                        rs.getTimestamp("criado_em")
                    );
                    mensagens.add(msg);
                }
            }
        }
        return mensagens;
    }
    
    /**
     * Sobrecarga de compatibilidade para buscar mensagens da conversa ativa.
     */
    public List<Mensagem> getMensagensPorSessao(String sessionId) throws SQLException {
        long conversaId = obterOuCriarConversaAtiva();
        return getMensagensPorConversa(conversaId);
    }
    
    /**
     * Deleta uma conversa e todas as mensagens associadas (via ON DELETE CASCADE).
     */
    public void limparConversa(long conversaId) throws SQLException {
        String sql = "DELETE FROM conversas WHERE id = ?";
        try (PreparedStatement stmt = connection.prepareStatement(sql)) {
            stmt.setLong(1, conversaId);
            stmt.executeUpdate();
        }
    }
    
    /**
     * Sobrecarga de compatibilidade para limpar a conversa ativa.
     */
    public void limparSessao(String sessionId) throws SQLException {
        long conversaId = obterOuCriarConversaAtiva();
        limparConversa(conversaId);
    }
    
    /**
     * Conta o número de mensagens de uma conversa.
     */
    public int contarMensagens(long conversaId) throws SQLException {
        String sql = "SELECT COUNT(*) as total FROM mensagens WHERE conversa_id = ?";
        try (PreparedStatement stmt = connection.prepareStatement(sql)) {
            stmt.setLong(1, conversaId);
            try (ResultSet rs = stmt.executeQuery()) {
                if (rs.next()) {
                    return rs.getInt("total");
                }
            }
        }
        return 0;
    }
    
    /**
     * Sobrecarga de compatibilidade para contar mensagens da conversa ativa.
     */
    public int contarMensagens(String sessionId) throws SQLException {
        long conversaId = obterOuCriarConversaAtiva();
        return contarMensagens(conversaId);
    }
    
    /**
     * Representação de uma mensagem no banco.
     */
    public static class Mensagem {
        private final Long id;
        private final Long conversaId;
        private final String role;
        private final String conteudo;
        private final String anexos;
        private final Timestamp criadoEm;
        
        public Mensagem(Long id, Long conversaId, String role, String conteudo, String anexos, Timestamp criadoEm) {
            this.id = id;
            this.conversaId = conversaId;
            this.role = role;
            this.conteudo = conteudo;
            this.anexos = anexos;
            this.criadoEm = criadoEm;
        }
        
        public Long getId() { return id; }
        public Long getConversaId() { return conversaId; }
        public String getRole() { return role; }
        public String getConteudo() { return conteudo; }
        public String getContent() { return conteudo; }
        public String getAnexos() { return anexos; }
        public Timestamp getCriadoEm() { return criadoEm; }
        public Timestamp getCreatedAt() { return criadoEm; }
        public String getSessionId() { return String.valueOf(conversaId); }
    }
    
    /**
     * Representação de uma conversa.
     */
    public static class Conversa {
        private final Long id;
        private final String titulo;
        private final Timestamp criadoEm;
        private final Timestamp atualizadoEm;
        
        public Conversa(Long id, String titulo, Timestamp criadoEm, Timestamp atualizadoEm) {
            this.id = id;
            this.titulo = titulo;
            this.criadoEm = criadoEm;
            this.atualizadoEm = atualizadoEm;
        }
        
        public Long getId() { return id; }
        public String getTitulo() { return titulo; }
        public Timestamp getCriadoEm() { return criadoEm; }
        public Timestamp getAtualizadoEm() { return atualizadoEm; }
    }
}
