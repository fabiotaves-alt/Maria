package com.tristar.maria.dao;

import java.sql.*;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

/**
 * DAO para gerenciamento de configurações do sistema.
 * Responsável por persistir e recuperar configurações da tabela 'configuracoes'.
 */
public class ConfiguracaoDAO {
    
    private final Connection connection;
    
    public ConfiguracaoDAO(Connection connection) {
        this.connection = connection;
    }
    
    /**
     * Salva ou atualiza uma configuração (UPSERT).
     */
    public void salvarConfiguracao(String chave, String valor) throws SQLException {
        String sql = "INSERT OR REPLACE INTO configuracoes (chave, valor, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)";
        try (PreparedStatement stmt = connection.prepareStatement(sql)) {
            stmt.setString(1, chave);
            stmt.setString(2, valor);
            stmt.executeUpdate();
        }
    }
    
    /**
     * Recupera o valor de uma configuração pela chave.
     */
    public Optional<String> getValor(String chave) throws SQLException {
        String sql = "SELECT valor FROM configuracoes WHERE chave = ?";
        try (PreparedStatement stmt = connection.prepareStatement(sql)) {
            stmt.setString(1, chave);
            ResultSet rs = stmt.executeQuery();
            
            if (rs.next()) {
                return Optional.ofNullable(rs.getString("valor"));
            }
        }
        return Optional.empty();
    }
    
    /**
     * Recupera todas as configurações.
     */
    public List<Configuracao> getTodasConfiguracoes() throws SQLException {
        String sql = "SELECT chave, valor, updated_at FROM configuracoes ORDER BY chave ASC";
        List<Configuracao> configuracoes = new ArrayList<>();
        
        try (PreparedStatement stmt = connection.prepareStatement(sql)) {
            ResultSet rs = stmt.executeQuery();
            
            while (rs.next()) {
                Configuracao config = new Configuracao(
                    rs.getString("chave"),
                    rs.getString("valor"),
                    rs.getTimestamp("updated_at")
                );
                configuracoes.add(config);
            }
        }
        return configuracoes;
    }
    
    /**
     * Deleta uma configuração pela chave.
     */
    public void deletarConfiguracao(String chave) throws SQLException {
        String sql = "DELETE FROM configuracoes WHERE chave = ?";
        try (PreparedStatement stmt = connection.prepareStatement(sql)) {
            stmt.setString(1, chave);
            stmt.executeUpdate();
        }
    }
    
    /**
     * Verifica se uma configuração existe.
     */
    public boolean existe(String chave) throws SQLException {
        String sql = "SELECT COUNT(*) as total FROM configuracoes WHERE chave = ?";
        try (PreparedStatement stmt = connection.prepareStatement(sql)) {
            stmt.setString(1, chave);
            ResultSet rs = stmt.executeQuery();
            if (rs.next()) {
                return rs.getInt("total") > 0;
            }
        }
        return false;
    }
    
    /**
     * Conta o total de configurações salvas.
     */
    public int contarConfiguracoes() throws SQLException {
        String sql = "SELECT COUNT(*) as total FROM configuracoes";
        try (PreparedStatement stmt = connection.prepareStatement(sql)) {
            ResultSet rs = stmt.executeQuery();
            if (rs.next()) {
                return rs.getInt("total");
            }
        }
        return 0;
    }
    
    /**
     * Classe interna que representa uma configuração.
     */
    public static class Configuracao {
        private final String chave;
        private final String valor;
        private final Timestamp updatedAt;
        
        public Configuracao(String chave, String valor, Timestamp updatedAt) {
            this.chave = chave;
            this.valor = valor;
            this.updatedAt = updatedAt;
        }
        
        public String getChave() { return chave; }
        public String getValor() { return valor; }
        public Timestamp getUpdatedAt() { return updatedAt; }
    }
}
