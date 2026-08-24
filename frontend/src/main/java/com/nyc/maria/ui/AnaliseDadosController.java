package com.nyc.maria.ui;

import javafx.fxml.FXML;
import javafx.scene.control.Label;
import javafx.scene.control.TextArea;

public class AnaliseDadosController {
    @FXML private TextArea areaResultado;
    @FXML private Label labelStatus;

    public void initialize() {
        labelStatus.setText("Aguardando dados para análise (Fase 0 - esqueleto)");
    }
}
