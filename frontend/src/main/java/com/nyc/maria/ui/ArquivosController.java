package com.nyc.maria.ui;

import javafx.fxml.FXML;
import javafx.scene.control.Label;
import javafx.scene.control.ListView;

public class ArquivosController {
    @FXML private ListView<String> listaArquivos;
    @FXML private Label labelStatus;

    public void initialize() {
        labelStatus.setText("Nenhum arquivo carregado (Fase 0 - esqueleto)");
    }

    @FXML
    private void selecionarArquivo() {
        labelStatus.setText("Funcionalidade será implementada na Fase 2");
    }
}
