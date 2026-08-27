package com.tristar.maria.ui;

import com.tristar.maria.dao.DatabaseManager;
import com.tristar.maria.dao.AutomacaoDAO;
import javafx.fxml.FXML;
import javafx.scene.control.*;

import java.sql.SQLException;
import java.util.List;

public class AutomacoesController {
    @FXML private ListView<AutomacaoItem> listaAutomacoes;
    @FXML private TextField campoNome;
    @FXML private TextField campoGatilho;
    @FXML private TextField campoAcao;
    @FXML private CheckBox checkAtiva;
    
    private DatabaseManager dbManager;
    private AutomacaoDAO automacaoDAO;
    
    public static class AutomacaoItem {
        private final Long id;
        private final String nome;
        private final String gatilho;
        private final String acao;
        private final boolean ativa;
        
        public AutomacaoItem(Long id, String nome, String gatilho, String acao, boolean ativa) {
            this.id = id;
            this.nome = nome;
            this.gatilho = gatilho;
            this.acao = acao;
            this.ativa = ativa;
        }
        
        public Long getId() { return id; }
        public String getNome() { return nome; }
        public String getGatilho() { return gatilho; }
        public String getAcao() { return acao; }
        public boolean isAtiva() { return ativa; }
        
        @Override
        public String toString() {
            String status = ativa ? "✓" : "✗";
            return status + " [" + nome + "] Gatilho: " + gatilho + " → Ação: " + acao;
        }
    }
    
    public void initialize() {
        try {
            dbManager = DatabaseManager.getInstance();
            automacaoDAO = dbManager.getAutomacaoDAO();
            carregarAutomacoes();
        } catch (SQLException e) {
            mostrarErro("Erro ao carregar automações: " + e.getMessage());
        }
    }
    
    private void carregarAutomacoes() {
        try {
            listaAutomacoes.getItems().clear();
            List<AutomacaoDAO.Automacao> automacoes = automacaoDAO.getTodasAutomacoes();
            
            if (automacoes.isEmpty()) {
                listaAutomacoes.getItems().add(new AutomacaoItem(null, "Nenhuma automação", "-", "-", false));
            } else {
                for (AutomacaoDAO.Automacao a : automacoes) {
                    listaAutomacoes.getItems().add(new AutomacaoItem(a.getId(), a.getNome(), a.getGatilho(), a.getAcao(), a.isAtiva()));
                }
            }
        } catch (SQLException e) {
            mostrarErro("Erro ao carregar automações: " + e.getMessage());
        }
    }

    @FXML
    private void novaAutomacao() {
        String nome = campoNome != null ? campoNome.getText().trim() : "";
        String gatilho = campoGatilho != null ? campoGatilho.getText().trim() : "";
        String acao = campoAcao != null ? campoAcao.getText().trim() : "";
        boolean ativa = checkAtiva != null && checkAtiva.isSelected();
        
        if (!nome.isEmpty() && !gatilho.isEmpty() && !acao.isEmpty()) {
            try {
                automacaoDAO.criarAutomacao(nome, gatilho, acao, ativa);
                carregarAutomacoes();
                limparCampos();
            } catch (SQLException e) {
                mostrarErro("Erro ao criar automação: " + e.getMessage());
            }
        } else {
            mostrarErro("Preencha todos os campos obrigatórios (nome, gatilho e ação).");
        }
    }
    
    @FXML
    private void deletarAutomacaoSelecionada() {
        AutomacaoItem selecionado = listaAutomacoes.getSelectionModel().getSelectedItem();
        if (selecionado != null && selecionado.getId() != null) {
            try {
                automacaoDAO.deletarAutomacao(selecionado.getId());
                carregarAutomacoes();
            } catch (SQLException e) {
                mostrarErro("Erro ao deletar automação: " + e.getMessage());
            }
        }
    }
    
    @FXML
    private void toggleAutomacaoSelecionada() {
        AutomacaoItem selecionado = listaAutomacoes.getSelectionModel().getSelectedItem();
        if (selecionado != null && selecionado.getId() != null) {
            try {
                automacaoDAO.toggleAtiva(selecionado.getId(), !selecionado.isAtiva());
                carregarAutomacoes();
            } catch (SQLException e) {
                mostrarErro("Erro ao alternar automação: " + e.getMessage());
            }
        }
    }
    
    private void limparCampos() {
        if (campoNome != null) campoNome.clear();
        if (campoGatilho != null) campoGatilho.clear();
        if (campoAcao != null) campoAcao.clear();
        if (checkAtiva != null) checkAtiva.setSelected(true);
    }
    
    private void mostrarErro(String mensagem) {
        Alert alert = new Alert(Alert.AlertType.ERROR, mensagem, ButtonType.OK);
        alert.showAndWait();
    }
}
