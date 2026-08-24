package com.nyc.maria.ui;

import javafx.fxml.FXML;
import javafx.scene.control.ListView;

public class AutomacoesController {
    @FXML private ListView<String> listaAutomacoes;

    public void initialize() {
        listaAutomacoes.getItems().add("(Nenhuma automação configurada - Fase 0)");
    }

    @FXML
    private void novaAutomacao() {
        listaAutomacoes.getItems().add("Nova automação (placeholder)");
    }
}
