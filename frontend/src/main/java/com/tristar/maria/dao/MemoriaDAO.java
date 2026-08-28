package com.tristar.maria.dao;

import java.sql.*;
import java.util.ArrayList;
import java.util.List;

/**
 * DAO para gerenciamento de memórias de longo prazo (RAG).
 * Opera sobre a tabela unificada 'memoria'.
 */
public class MemoriaDAO {
    
    private final Connection connection;
    
    public MemoriaDAO(Connection connection) {
        this.connection = connection;
    }
    
    /**
     * Adiciona uma nova memória persistente.
     */
    public void adicionarMemoria(String fato, String categoria, String fonte) throws SQLException {
        String sql = "INSERT OR REPLACE INTO memoria (fato, categoria, relevancia, fonte, criado_em) VALUES (?, ?, 1.0, ?, CURRENT_TIMESTAMP)";
        try (PreparedStatement stmt = connection.prepareStatement(sql)) {
            stmt.setString(1, fato);
            stmt.setString(2, (categoria != null && !categoria.isBlank()) ? categoria : "geral");
            stmt.setString(3, (fonte != null && !fonte.isBlank()) ? fonte : "manual");
            stmt.executeUpdate();
        }
    }
    
    /**
     * Recupera memórias ordenadas pelas mais recentes.
     */
    public List<Memoria> getMemorias(String categoria) throws SQLException {
        StringBuilder sql = new StringBuilder("SELECT id, fato, categoria, relevancia, fonte, criado_em FROM memoria");
        if (categoria != null && !categoria.isBlank()) {
            sql.append(" WHERE categoria = ?");
        }
        sql.append(" ORDER BY criado_em DESC");
        
        List<Memoria> memorias = new ArrayList<>();
        try (PreparedStatement stmt = connection.prepareStatement(sql.toString())) {
            if (categoria != null && !categoria.isBlank()) {
                stmt.setString(1, categoria);
            }
            try (ResultSet rs = stmt.executeQuery()) {
                while (rs.next()) {
                    Memoria memoria = new Memoria(
                        rs.getLong("id"),
                        rs.getString("fato"),
                        rs.getString("categoria"),
                        rs.getDouble("relevancia"),
                        rs.getString("fonte"),
                        rs.getTimestamp("criado_em")
                    );
                    memorias.add(memoria);
                }
            }
        }
        return memorias;
    }
    
    /**
     * Busca memórias por termo.
     */
    public List<Memoria> buscarMemorias(String termo) throws SQLException {
        String sql = "SELECT id, fato, categoria, relevancia, fonte, criado_em FROM memoria WHERE fato LIKE ? ORDER BY criado_em DESC";
        List<Memoria> memorias = new ArrayList<>();
        
        try (PreparedStatement stmt = connection.prepareStatement(sql)) {
            stmt.setString(1, "%" + (termo != null ? termo : "") + "%");
            try (ResultSet rs = stmt.executeQuery()) {
                while (rs.next()) {
                    Memoria memoria = new Memoria(
                        rs.getLong("id"),
                        rs.getString("fato"),
                        rs.getString("categoria"),
                        rs.getDouble("relevancia"),
                        rs.getString("fonte"),
                        rs.getTimestamp("criado_em")
                    );
                    memorias.add(memoria);
                }
            }
        }
        return memorias;
    }
    
    /**
     * Deleta uma memória específica pelo ID.
     */
    public void deletarMemoria(Long id) throws SQLException {
        String sql = "DELETE FROM memoria WHERE id = ?";
        try (PreparedStatement stmt = connection.prepareStatement(sql)) {
            stmt.setLong(1, id);
            stmt.executeUpdate();
        }
    }
    
    /**
     * Limpa todas as memórias.
     */
    public void limparTodasMemorias() throws SQLException {
        String sql = "DELETE FROM memoria";
        try (Statement stmt = connection.createStatement()) {
            stmt.executeUpdate(sql);
        }
    }
    
    /**
     * Conta o total de memórias cadastradas.
     */
    public int contarMemorias() throws SQLException {
        String sql = "SELECT COUNT(*) as total FROM memoria";
        try (Statement stmt = connection.createStatement();
             ResultSet rs = stmt.executeQuery(sql)) {
            if (rs.next()) {
                return rs.getInt("total");
            }
        }
        return 0;
    }
    
    /**
     * Classe que representa um fato/memória persistente.
     */
    public static class Memoria {
        private final Long id;
        private final String fato;
        private final String categoria;
        private final Double relevancia;
        private final String fonte;
        private final Timestamp criadoEm;
        
        public Memoria(Long id, String fato, String categoria, Double relevancia, String fonte, Timestamp criadoEm) {
            this.id = id;
            this.fato = fato;
            this.categoria = categoria;
            this.relevancia = relevancia;
            this.fonte = fonte;
            this.criadoEm = criadoEm;
        }
        
        public Long getId() { return id; }
        public String getFato() { return fato; }
        public String getConteudo() { return fato; }
        public String getCategoria() { return categoria; }
        public Double getRelevancia() { return relevancia; }
        public String getFonte() { return fonte; }
        public String getOrigem() { return fonte; }
        public Timestamp getCriadoEm() { return criadoEm; }
        public Timestamp getCreatedAt() { return criadoEm; }
    }
}
