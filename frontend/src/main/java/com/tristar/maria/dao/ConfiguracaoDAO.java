package com.tristar.maria.dao;

import java.sql.*;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

/**
 * DAO para gerenciamento de configurações do sistema.
 * Opera sobre a tabela unificada 'configuracoes'.
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
        salvarConfiguracao(chave, valor, null);
    }
    
    /**
     * Salva ou atualiza uma configuração com descrição.
     */
    public void salvarConfiguracao(String chave, String valor, String descricao) throws SQLException {
        String sql = """
            INSERT INTO configuracoes (chave, valor, descricao, atualizado_em)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(chave) DO UPDATE SET
                valor = excluded.valor,
                descricao = COALESCE(excluded.descricao, configuracoes.descricao),
                atualizado_em = CURRENT_TIMESTAMP
        """;
        try (PreparedStatement stmt = connection.prepareStatement(sql)) {
            stmt.setString(1, chave);
            stmt.setString(2, valor);
            stmt.setString(3, descricao);
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
            try (ResultSet rs = stmt.executeQuery()) {
                if (rs.next()) {
                    return Optional.ofNullable(rs.getString("valor"));
                }
            }
        }
        return Optional.empty();
    }
    
    /**
     * Alias de busca para compatibilidade com testes e controllers.
     */
    public Optional<String> buscarConfiguracao(String chave) throws SQLException {
        return getValor(chave);
    }
    
    /**
     * Recupera todas as configurações.
     */
    public List<Configuracao> getTodasConfiguracoes() throws SQLException {
        String sql = "SELECT chave, valor, descricao, atualizado_em FROM configuracoes ORDER BY chave ASC";
        List<Configuracao> configuracoes = new ArrayList<>();
        
        try (Statement stmt = connection.createStatement();
             ResultSet rs = stmt.executeQuery(sql)) {
            while (rs.next()) {
                Configuracao config = new Configuracao(
                    rs.getString("chave"),
                    rs.getString("valor"),
                    rs.getString("descricao"),
                    rs.getTimestamp("atualizado_em")
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
     * Verifica se uma chave existe.
     */
    public boolean existe(String chave) throws SQLException {
        String sql = "SELECT COUNT(*) as total FROM configuracoes WHERE chave = ?";
        try (PreparedStatement stmt = connection.prepareStatement(sql)) {
            stmt.setString(1, chave);
            try (ResultSet rs = stmt.executeQuery()) {
                if (rs.next()) {
                    return rs.getInt("total") > 0;
                }
            }
        }
        return false;
    }
    
    /**
     * Conta o total de configurações cadastradas.
     */
    public int contarConfiguracoes() throws SQLException {
        String sql = "SELECT COUNT(*) as total FROM configuracoes";
        try (Statement stmt = connection.createStatement();
             ResultSet rs = stmt.executeQuery(sql)) {
            if (rs.next()) {
                return rs.getInt("total");
            }
        }
        return 0;
    }
    
    /**
     * Representação de uma configuração.
     */
    public static class Configuracao {
        private final String chave;
        private final String valor;
        private final String descricao;
        private final Timestamp atualizadoEm;
        
        public Configuracao(String chave, String valor, String descricao, Timestamp atualizadoEm) {
            this.chave = chave;
            this.valor = valor;
            this.descricao = descricao;
            this.atualizadoEm = atualizadoEm;
        }
        
        public String getChave() { return chave; }
        public String getValor() { return valor; }
        public String getDescricao() { return descricao; }
        public Timestamp getAtualizadoEm() { return atualizadoEm; }
        public Timestamp getUpdatedAt() { return atualizadoEm; }
    }
}
