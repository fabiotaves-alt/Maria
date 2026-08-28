package com.tristar.maria.dao;

import java.sql.*;
import java.util.ArrayList;
import java.util.List;

/**
 * DAO para gerenciamento de automações.
 * Opera sobre a tabela unificada 'automacoes'.
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
        criarAutomacao(nome, null, gatilho, acao, null, ativa);
    }
    
    /**
     * Cria uma nova automação completa.
     */
    public void criarAutomacao(String nome, String descricao, String gatilho, String acao, String parametros, boolean ativa) throws SQLException {
        String sql = "INSERT INTO automacoes (nome, descricao, gatilho, acao, parametros, ativo, criado_em) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)";
        try (PreparedStatement stmt = connection.prepareStatement(sql)) {
            stmt.setString(1, nome);
            stmt.setString(2, descricao);
            stmt.setString(3, gatilho);
            stmt.setString(4, acao);
            stmt.setString(5, parametros);
            stmt.setBoolean(6, ativa);
            stmt.executeUpdate();
        }
    }
    
    /**
     * Recupera todas as automações ordenadas pelas mais recentes.
     */
    public List<Automacao> getTodasAutomacoes() throws SQLException {
        String sql = "SELECT id, nome, descricao, gatilho, acao, parametros, passos_json, ativo, execucoes_count, criado_em, ultima_execucao FROM automacoes ORDER BY criado_em DESC";
        List<Automacao> automacoes = new ArrayList<>();
        
        try (Statement stmt = connection.createStatement();
             ResultSet rs = stmt.executeQuery(sql)) {
            while (rs.next()) {
                automacoes.add(mapearAutomacao(rs));
            }
        }
        return automacoes;
    }
    
    /**
     * Recupera apenas automações ativas.
     */
    public List<Automacao> getAutomacoesAtivas() throws SQLException {
        String sql = "SELECT id, nome, descricao, gatilho, acao, parametros, passos_json, ativo, execucoes_count, criado_em, ultima_execucao FROM automacoes WHERE ativo = 1 ORDER BY criado_em DESC";
        List<Automacao> automacoes = new ArrayList<>();
        
        try (Statement stmt = connection.createStatement();
             ResultSet rs = stmt.executeQuery(sql)) {
            while (rs.next()) {
                automacoes.add(mapearAutomacao(rs));
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
            sql.append("ativo = ?, ");
            params.add(ativa ? 1 : 0);
        }
        
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
        String sql = "UPDATE automacoes SET ativo = ? WHERE id = ?";
        try (PreparedStatement stmt = connection.prepareStatement(sql)) {
            stmt.setInt(1, ativa ? 1 : 0);
            stmt.setLong(2, id);
            stmt.executeUpdate();
        }
    }
    
    /**
     * Conta o total de automações.
     */
    public int contarAutomacoes() throws SQLException {
        String sql = "SELECT COUNT(*) as total FROM automacoes";
        try (Statement stmt = connection.createStatement();
             ResultSet rs = stmt.executeQuery(sql)) {
            if (rs.next()) {
                return rs.getInt("total");
            }
        }
        return 0;
    }
    
    /**
     * Busca automações por nome.
     */
    public List<Automacao> buscarPorNome(String termo) throws SQLException {
        String sql = "SELECT id, nome, descricao, gatilho, acao, parametros, passos_json, ativo, execucoes_count, criado_em, ultima_execucao FROM automacoes WHERE nome LIKE ? ORDER BY criado_em DESC";
        List<Automacao> automacoes = new ArrayList<>();
        
        try (PreparedStatement stmt = connection.prepareStatement(sql)) {
            stmt.setString(1, "%" + (termo != null ? termo : "") + "%");
            try (ResultSet rs = stmt.executeQuery()) {
                while (rs.next()) {
                    automacoes.add(mapearAutomacao(rs));
                }
            }
        }
        return automacoes;
    }
    
    private Automacao mapearAutomacao(ResultSet rs) throws SQLException {
        return new Automacao(
            rs.getLong("id"),
            rs.getString("nome"),
            rs.getString("descricao"),
            rs.getString("gatilho"),
            rs.getString("acao"),
            rs.getString("parametros"),
            rs.getString("passos_json"),
            rs.getInt("ativo") == 1,
            rs.getInt("execucoes_count"),
            rs.getTimestamp("criado_em"),
            rs.getTimestamp("ultima_execucao")
        );
    }
    
    /**
     * Representação de uma automação.
     */
    public static class Automacao {
        private final Long id;
        private final String nome;
        private final String descricao;
        private final String gatilho;
        private final String acao;
        private final String parametros;
        private final String passosJson;
        private final boolean ativo;
        private final int execucoesCount;
        private final Timestamp criadoEm;
        private final Timestamp ultimaExecucao;
        
        public Automacao(Long id, String nome, String descricao, String gatilho, String acao, 
                         String parametros, String passosJson, boolean ativo, int execucoesCount, 
                         Timestamp criadoEm, Timestamp ultimaExecucao) {
            this.id = id;
            this.nome = nome;
            this.descricao = descricao;
            this.gatilho = gatilho;
            this.acao = acao;
            this.parametros = parametros;
            this.passosJson = passosJson;
            this.ativo = ativo;
            this.execucoesCount = execucoesCount;
            this.criadoEm = criadoEm;
            this.ultimaExecucao = ultimaExecucao;
        }
        
        public Long getId() { return id; }
        public String getNome() { return nome; }
        public String getDescricao() { return descricao; }
        public String getGatilho() { return gatilho; }
        public String getAcao() { return acao; }
        public String getParametros() { return parametros; }
        public String getPassosJson() { return passosJson; }
        public boolean isAtivo() { return ativo; }
        public boolean isAtiva() { return ativo; }
        public int getExecucoesCount() { return execucoesCount; }
        public Timestamp getCriadoEm() { return criadoEm; }
        public Timestamp getCreatedAt() { return criadoEm; }
        public Timestamp getUltimaExecucao() { return ultimaExecucao; }
    }
}
