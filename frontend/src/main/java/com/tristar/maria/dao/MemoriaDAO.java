package com.tristar.maria.dao;

import java.sql.*;
import java.util.ArrayList;
import java.util.List;

/**
 * DAO para gerenciamento de memórias de longo prazo.
 * Responsável por persistir e recuperar informações da tabela 'memorias'.
 */
public class MemoriaDAO {
    
    private final Connection connection;
    
    public MemoriaDAO(Connection connection) {
        this.connection = connection;
    }
    
    /**
     * Adiciona uma nova memória.
     */
    public void adicionarMemoria(String conteudo, String categoria, String origem) throws SQLException {
        String sql = "INSERT INTO memorias (conteudo, categoria, origem, created_at) VALUES (?, ?, ?, CURRENT_TIMESTAMP)";
        try (PreparedStatement stmt = connection.prepareStatement(sql)) {
            stmt.setString(1, conteudo);
            stmt.setString(2, categoria != null ? categoria : "geral");
            stmt.setString(3, origem != null ? origem : "manual");
            stmt.executeUpdate();
        }
    }
    
    /**
     * Recupera todas as memórias, opcionalmente filtradas por categoria.
     */
    public List<Memoria> getMemorias(String categoria) throws SQLException {
        StringBuilder sql = new StringBuilder("SELECT id, conteudo, categoria, origem, created_at FROM memorias");
        
        if (categoria != null && !categoria.isEmpty()) {
            sql.append(" WHERE categoria = ?");
        }
        sql.append(" ORDER BY created_at DESC");
        
        List<Memoria> memorias = new ArrayList<>();
        try (PreparedStatement stmt = connection.prepareStatement(sql.toString())) {
            if (categoria != null && !categoria.isEmpty()) {
                stmt.setString(1, categoria);
            }
            ResultSet rs = stmt.executeQuery();
            
            while (rs.next()) {
                Memoria memoria = new Memoria(
                    rs.getLong("id"),
                    rs.getString("conteudo"),
                    rs.getString("categoria"),
                    rs.getString("origem"),
                    rs.getTimestamp("created_at")
                );
                memorias.add(memoria);
            }
        }
        return memorias;
    }
    
    /**
     * Busca memórias por termo (LIKE).
     */
    public List<Memoria> buscarMemorias(String termo) throws SQLException {
        String sql = "SELECT id, conteudo, categoria, origem, created_at FROM memorias WHERE conteudo LIKE ? ORDER BY created_at DESC";
        List<Memoria> memorias = new ArrayList<>();
        
        try (PreparedStatement stmt = connection.prepareStatement(sql)) {
            stmt.setString(1, "%" + termo + "%");
            ResultSet rs = stmt.executeQuery();
            
            while (rs.next()) {
                Memoria memoria = new Memoria(
                    rs.getLong("id"),
                    rs.getString("conteudo"),
                    rs.getString("categoria"),
                    rs.getString("origem"),
                    rs.getTimestamp("created_at")
                );
                memorias.add(memoria);
            }
        }
        return memorias;
    }
    
    /**
     * Deleta uma memória específica pelo ID.
     */
    public void deletarMemoria(Long id) throws SQLException {
        String sql = "DELETE FROM memorias WHERE id = ?";
        try (PreparedStatement stmt = connection.prepareStatement(sql)) {
            stmt.setLong(1, id);
            stmt.executeUpdate();
        }
    }
    
    /**
     * Limpa todas as memórias.
     */
    public void limparTodasMemorias() throws SQLException {
        String sql = "DELETE FROM memorias";
        try (PreparedStatement stmt = connection.prepareStatement(sql)) {
            stmt.executeUpdate();
        }
    }
    
    /**
     * Conta o total de memórias.
     */
    public int contarMemorias() throws SQLException {
        String sql = "SELECT COUNT(*) as total FROM memorias";
        try (PreparedStatement stmt = connection.prepareStatement(sql)) {
            ResultSet rs = stmt.executeQuery();
            if (rs.next()) {
                return rs.getInt("total");
            }
        }
        return 0;
    }
    
    /**
     * Classe interna que representa uma memória.
     */
    public static class Memoria {
        private final Long id;
        private final String conteudo;
        private final String categoria;
        private final String origem;
        private final Timestamp createdAt;
        
        public Memoria(Long id, String conteudo, String categoria, String origem, Timestamp createdAt) {
            this.id = id;
            this.conteudo = conteudo;
            this.categoria = categoria;
            this.origem = origem;
            this.createdAt = createdAt;
        }
        
        public Long getId() { return id; }
        public String getConteudo() { return conteudo; }
        public String getCategoria() { return categoria; }
        public String getOrigem() { return origem; }
        public Timestamp getCreatedAt() { return createdAt; }
    }
}
