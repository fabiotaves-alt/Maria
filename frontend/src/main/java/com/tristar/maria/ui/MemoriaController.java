package com.tristar.maria.ui;

import com.tristar.maria.dao.DatabaseManager;
import com.tristar.maria.dao.MemoriaDAO;
import javafx.fxml.FXML;
import javafx.scene.control.Alert;
import javafx.scene.control.ButtonType;
import javafx.scene.control.ListView;
import javafx.scene.control.TextField;

import java.sql.SQLException;
import java.util.List;

public class MemoriaController {
    @FXML private ListView<MemoriaItem> listaFatos;
    @FXML private TextField campoNovoFato;
    
    private DatabaseManager dbManager;
    private MemoriaDAO memoriaDAO;
    
    public static class MemoriaItem {
        private final Long id;
        private final String conteudo;
        private final String categoria;
        
        public MemoriaItem(Long id, String conteudo, String categoria) {
            this.id = id;
            this.conteudo = conteudo;
            this.categoria = categoria;
        }
        
        public Long getId() { return id; }
        public String getConteudo() { return conteudo; }
        public String getCategoria() { return categoria; }
        
        @Override
        public String toString() {
            return "[" + categoria + "] " + conteudo;
        }
    }
    
    public void initialize() {
        try {
            dbManager = DatabaseManager.getInstance();
            memoriaDAO = dbManager.getMemoriaDAO();
            carregarMemorias();
        } catch (SQLException e) {
            mostrarErro("Erro ao carregar memórias: " + e.getMessage());
        }
    }
    
    private void carregarMemorias() {
        try {
            listaFatos.getItems().clear();
            List<MemoriaDAO.Memoria> memorias = memoriaDAO.getMemorias(null);
            
            if (memorias.isEmpty()) {
                listaFatos.getItems().add(new MemoriaItem(null, "Nenhuma memória registrada", "sistema"));
            } else {
                for (MemoriaDAO.Memoria m : memorias) {
                    listaFatos.getItems().add(new MemoriaItem(m.getId(), m.getConteudo(), m.getCategoria()));
                }
            }
        } catch (SQLException e) {
            mostrarErro("Erro ao carregar memórias: " + e.getMessage());
        }
    }

    @FXML
    private void adicionarFato() {
        String fato = campoNovoFato.getText().trim();
        if (!fato.isEmpty()) {
            try {
                memoriaDAO.adicionarMemoria(fato, "manual", "usuario");
                carregarMemorias();
                campoNovoFato.clear();
            } catch (SQLException e) {
                mostrarErro("Erro ao adicionar memória: " + e.getMessage());
            }
        }
    }
    
    @FXML
    private void deletarFatoSelecionado() {
        MemoriaItem selecionado = listaFatos.getSelectionModel().getSelectedItem();
        if (selecionado != null && selecionado.getId() != null) {
            try {
                memoriaDAO.deletarMemoria(selecionado.getId());
                carregarMemorias();
            } catch (SQLException e) {
                mostrarErro("Erro ao deletar memória: " + e.getMessage());
            }
        }
    }
    
    @FXML
    private void limparTodasMemorias() {
        Alert alert = new Alert(Alert.AlertType.CONFIRMATION, "Tem certeza que deseja apagar todas as memórias?", ButtonType.YES, ButtonType.NO);
        alert.showAndWait().ifPresent(response -> {
            if (response == ButtonType.YES) {
                try {
                    memoriaDAO.limparTodasMemorias();
                    carregarMemorias();
                } catch (SQLException e) {
                    mostrarErro("Erro ao limpar memórias: " + e.getMessage());
                }
            }
        });
    }
    
    private void mostrarErro(String mensagem) {
        Alert alert = new Alert(Alert.AlertType.ERROR, mensagem, ButtonType.OK);
        alert.showAndWait();
    }
}
