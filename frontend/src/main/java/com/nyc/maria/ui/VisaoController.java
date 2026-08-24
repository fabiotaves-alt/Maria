package com.nyc.maria.ui;

import javafx.fxml.FXML;
import javafx.scene.control.Label;
import javafx.scene.image.ImageView;

public class VisaoController {
    @FXML private ImageView imagemPreview;
    @FXML private Label labelAnalise;

    public void initialize() {
        labelAnalise.setText("Nenhuma imagem analisada (Fase 0 - esqueleto)");
    }

    @FXML
    private void carregarImagem() {
        labelAnalise.setText("Funcionalidade será implementada na Fase 3");
    }
}
