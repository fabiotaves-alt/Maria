package com.nyc.maria.ui;

import javafx.fxml.FXML;
import javafx.scene.control.ChoiceBox;
import javafx.scene.control.Label;
import javafx.scene.control.TextField;

public class ConfiguracoesController {
    @FXML private ChoiceBox<String> choiceTema;
    @FXML private TextField campoModelo;
    @FXML private Label labelCaminhoDB;

    public void initialize() {
        choiceTema.getItems().addAll("Claro", "Escuro");
        choiceTema.setValue("Escuro");
        campoModelo.setText("llama3.1:8b");
        labelCaminhoDB.setText("Caminho: ./shared/maria.db (padrão)");
    }

    @FXML
    private void selecionarCaminhoDB() {
        labelCaminhoDB.setText("Caminho: seleção será implementada na Fase 7");
    }

    @FXML
    private void salvarConfiguracoes() {
        System.out.println("Configurações salvas (placeholder - Fase 0)");
    }
}
