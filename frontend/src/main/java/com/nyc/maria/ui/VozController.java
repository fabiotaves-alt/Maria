package com.nyc.maria.ui;

import javafx.fxml.FXML;
import javafx.scene.control.Label;
import javafx.scene.control.TextArea;
import javafx.scene.control.Button;

public class VozController {
    @FXML private Button btnGravar;
    @FXML private Label labelStatus;
    @FXML private TextArea areaTranscricao;

    public void initialize() {
        labelStatus.setText("Pronto para gravar (Fase 0 - esqueleto)");
    }

    @FXML
    private void iniciarGravacao() {
        labelStatus.setText("Funcionalidade será implementada na Fase 4");
    }
}
