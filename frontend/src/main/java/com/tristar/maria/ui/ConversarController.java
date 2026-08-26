package com.tristar.maria.ui;

import com.tristar.maria.bridge.BridgeManager;
import com.tristar.maria.bridge.Resposta;
import javafx.application.Platform;
import javafx.fxml.FXML;
import javafx.geometry.Pos;
import javafx.scene.control.Label;
import javafx.scene.control.TextField;
import javafx.scene.layout.HBox;
import javafx.scene.layout.Priority;
import javafx.scene.layout.VBox;

import java.io.IOException;
import java.time.LocalTime;
import java.time.format.DateTimeFormatter;
import java.util.Map;

/**
 * Controller da aba Conversar — painel de chat permanente à direita,
 * integrado à bridge Python (comandos ping/chat).
 */
public class ConversarController {

    private static final DateTimeFormatter HORA = DateTimeFormatter.ofPattern("HH:mm");

    @FXML private VBox areaMensagens;
    @FXML private TextField campoMensagem;
    @FXML private Label labelStatus;

    public void initialize() {
        labelStatus.setText("●  conectando...");
        try {
            BridgeManager.getInstance().enviar("ping", null)
                    .thenAccept(resposta -> Platform.runLater(() -> processarHandshake(resposta)))
                    .exceptionally(erro -> {
                        Platform.runLater(() -> labelStatus.setText("●  offline: " + erro.getMessage()));
                        return null;
                    });
        } catch (IOException e) {
            labelStatus.setText("●  offline: " + e.getMessage());
        }
    }

    private void processarHandshake(Resposta resposta) {
        if ("ok".equals(resposta.getStatus()) && "pong".equals(resposta.getDados())) {
            labelStatus.setText("●  online");
        } else {
            labelStatus.setText("●  offline: " + resposta.getMensagemErro());
        }
    }

    /**
     * Preenche o campo de mensagem (usado pelas ações rápidas do hero).
     */
    public void definirMensagem(String texto) {
        campoMensagem.setText(texto);
        campoMensagem.requestFocus();
    }

    @FXML
    private void enviarMensagem() {
        String texto = campoMensagem.getText().trim();
        if (texto.isEmpty()) {
            return;
        }
        adicionarBalaoUsuario(texto);
        campoMensagem.clear();
        labelStatus.setText("●  pensando...");

        try {
            BridgeManager.getInstance().enviar("chat", Map.of("mensagem", texto))
                    .thenAccept(resposta -> Platform.runLater(() -> processarResposta(resposta)))
                    .exceptionally(erro -> {
                        Platform.runLater(() -> {
                            adicionarBalaoMaria("[erro] " + erro.getMessage());
                            labelStatus.setText("●  online");
                        });
                        return null;
                    });
        } catch (IOException e) {
            labelStatus.setText("●  off: " + e.getMessage());
        }
    }

    private void processarResposta(Resposta resposta) {
        if ("ok".equals(resposta.getStatus())) {
            Object dados = resposta.getDados();
            adicionarBalaoMaria(dados != null ? dados.toString() : "(sem resposta)");
        } else {
            adicionarBalaoMaria("[erro] " + resposta.getMensagemErro());
        }
        labelStatus.setText("●  online");
    }

    // ── Construção das bolhas ─────────────────────────────
    private void adicionarBalaoUsuario(String texto) {
        Label balao = new Label(texto);
        balao.setWrapText(true);
        balao.setMaxWidth(320);
        balao.getStyleClass().add("bubble-user");

        Label hora = new Label(LocalTime.now().format(HORA));
        hora.getStyleClass().add("msg-meta");

        VBox grupo = new VBox(4, balao, hora);
        grupo.setAlignment(Pos.CENTER_RIGHT);

        HBox linha = new HBox();
        linha.setAlignment(Pos.CENTER_RIGHT);
        HBox.setHgrow(grupo, Priority.NEVER);
        linha.getChildren().add(grupo);
        areaMensagens.getChildren().add(linha);
    }

    private void adicionarBalaoMaria(String texto) {
        Label avatar = new Label("M");
        avatar.getStyleClass().add("avatar");

        Label balao = new Label(texto);
        balao.setWrapText(true);
        balao.setMaxWidth(280);
        balao.getStyleClass().add("bubble-maria");

        Label hora = new Label(LocalTime.now().format(HORA));
        hora.getStyleClass().add("msg-meta");

        VBox grupo = new VBox(4, balao, hora);
        grupo.setAlignment(Pos.CENTER_LEFT);

        HBox linha = new HBox(8, avatar, grupo);
        linha.setAlignment(Pos.CENTER_LEFT);
        areaMensagens.getChildren().add(linha);
    }
}