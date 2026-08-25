package com.tristar.maria.ui;

import com.tristar.maria.bridge.BridgeManager;
import com.tristar.maria.bridge.Resposta;
import javafx.application.Platform;
import javafx.fxml.FXML;
import javafx.scene.control.Label;
import javafx.scene.control.TextField;
import javafx.scene.layout.VBox;

import java.io.IOException;
import java.util.Map;

/**
 * Controller da aba Conversar — integrado à bridge Python (comandos ping/chat).
 */
public class ConversarController {

    @FXML private VBox areaMensagens;
    @FXML private TextField campoMensagem;
    @FXML private Label labelStatus;

    public void initialize() {
        labelStatus.setText("Conectando ao backend...");
        try {
            BridgeManager.getInstance().enviar("ping", null)
                    .thenAccept(resposta -> Platform.runLater(() -> processarHandshake(resposta)))
                    .exceptionally(erro -> {
                        Platform.runLater(() -> labelStatus.setText("Falha no handshake: " + erro.getMessage()));
                        return null;
                    });
        } catch (IOException e) {
            labelStatus.setText("Falha ao conectar: " + e.getMessage());
        }
    }

    private void processarHandshake(Resposta resposta) {
        if ("ok".equals(resposta.getStatus()) && "pong".equals(resposta.getDados())) {
            labelStatus.setText("Conectado. Digite sua mensagem.");
        } else {
            labelStatus.setText("Handshake falhou: " + resposta.getMensagemErro());
        }
    }

    @FXML
    private void enviarMensagem() {
        String texto = campoMensagem.getText().trim();
        if (texto.isEmpty()) {
            return;
        }

        adicionarMensagem("Você: " + texto, "#e3f2fd");
        campoMensagem.clear();
        labelStatus.setText("Aguardando resposta...");

        try {
            BridgeManager.getInstance().enviar("chat", Map.of("mensagem", texto))
                    .thenAccept(resposta -> Platform.runLater(() -> processarResposta(resposta)))
                    .exceptionally(erro -> {
                        Platform.runLater(() ->
                                adicionarMensagem("[ERRO] " + erro.getMessage(), "#ffcdd2"));
                        return null;
                    });
        } catch (IOException e) {
            labelStatus.setText("Erro ao enviar: " + e.getMessage());
        }
    }

    private void processarResposta(Resposta resposta) {
        if ("ok".equals(resposta.getStatus())) {
            Object dados = resposta.getDados();
            adicionarMensagem("Maria: " + (dados != null ? dados.toString() : "(sem resposta)"), "#f1f1f1");
        } else {
            adicionarMensagem("[ERRO] " + resposta.getMensagemErro(), "#ffcdd2");
        }
        labelStatus.setText("Pronto.");
    }

    private void adicionarMensagem(String texto, String corFundo) {
        Label msg = new Label(texto);
        msg.setWrapText(true);
        msg.setStyle("-fx-background-color: " + corFundo + "; -fx-padding: 8; -fx-background-radius: 8;");
        areaMensagens.getChildren().add(msg);
    }
}
