package com.nyc.maria.ui;

import javafx.fxml.FXML;
import javafx.scene.control.Label;
import javafx.scene.control.TextField;
import javafx.scene.layout.VBox;

/**
 * Controller da aba Conversar (esqueleto Fase 0).
 */
public class ConversarController {

    @FXML private VBox areaMensagens;
    @FXML private TextField campoMensagem;
    @FXML private Label labelStatus;

    public void initialize() {
        labelStatus.setText("Aguardando conexão...");
    }

    @FXML
    private void enviarMensagem() {
        String texto = campoMensagem.getText().trim();
        if (texto.isEmpty()) return;

        // Adiciona mensagem do usuário na área de chat
        Label msgUsuario = new Label("Você: " + texto);
        msgUsuario.setStyle("-fx-background-color: #e3f2fd; -fx-padding: 8; -fx-background-radius: 8;");
        areaMensagens.getChildren().add(msgUsuario);

        campoMensagem.clear();
        labelStatus.setText("Enviado (backend será integrado na Fase 1)");
    }
}
