package com.tristar.maria.ui;

import com.tristar.maria.bridge.BridgeManager;
import com.tristar.maria.bridge.Resposta;
import javafx.application.Platform;
import javafx.fxml.FXML;
import javafx.geometry.Pos;
import javafx.scene.Node;
import javafx.scene.control.*;
import javafx.scene.image.Image;
import javafx.scene.image.ImageView;
import javafx.scene.layout.HBox;
import javafx.scene.layout.Priority;
import javafx.scene.layout.VBox;
import javafx.scene.shape.Circle;
import javafx.stage.FileChooser;
import javafx.stage.Stage;

import java.io.*;
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
    @FXML private Label btnAnexar;
    @FXML private Label btnVoz;

    // Gravação de áudio
    private javax.sound.sampled.TargetDataLine linhaAudio;
    private ByteArrayOutputStream bufferAudio;
    private boolean gravando = false;

    private void atualizarStatus(String texto, String corHex) {
        labelStatus.setText(texto);
        labelStatus.setStyle("-fx-text-fill: " + corHex + ";");
    }

    public void initialize() {
        atualizarStatus("●  conectando...", "#f59e0b");
        try {
            BridgeManager.getInstance().enviar("ping", null)
                    .thenAccept(resposta -> Platform.runLater(() -> processarHandshake(resposta)))
                    .exceptionally(erro -> {
                        Platform.runLater(() -> atualizarStatus("●  offline: " + erro.getMessage(), "#ef4444"));
                        return null;
                    });
        } catch (IOException e) {
            atualizarStatus("●  offline: " + e.getMessage(), "#ef4444");
        }
    }

    private void processarHandshake(Resposta resposta) {
        if ("ok".equals(resposta.getStatus()) && "pong".equals(resposta.getDados())) {
            atualizarStatus("●  online", "#22c55e");
        } else {
            atualizarStatus("●  offline: " + resposta.getMensagemErro(), "#ef4444");
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
        atualizarStatus("●  pensando...", "#f59e0b");

        try {
            BridgeManager.getInstance().enviar("chat", Map.of("mensagem", texto))
                    .thenAccept(resposta -> Platform.runLater(() -> processarResposta(resposta)))
                    .exceptionally(erro -> {
                        Platform.runLater(() -> {
                            adicionarBalaoMaria("[erro] " + erro.getMessage());
                            atualizarStatus("●  online", "#22c55e");
                        });
                        return null;
                    });
        } catch (IOException e) {
            atualizarStatus("●  off: " + e.getMessage(), "#ef4444");
        }
    }

    private void processarResposta(Resposta resposta) {
        if ("ok".equals(resposta.getStatus())) {
            Object dados = resposta.getDados();
            adicionarBalaoMaria(dados != null ? dados.toString() : "(sem resposta)");
        } else {
            adicionarBalaoMaria("[erro] " + resposta.getMensagemErro());
        }
        atualizarStatus("●  online", "#22c55e");
    }

    // ── Ações do header (dropdown) ─────────────────────────────
    @FXML
    private void limparConversa() {
        areaMensagens.getChildren().clear();
    }

    @FXML
    private void exportarConversa() {
        FileChooser fileChooser = new FileChooser();
        fileChooser.getExtensionFilters().add(new FileChooser.ExtensionFilter("Texto", "*.txt"));
        fileChooser.setInitialFileName("conversa_maria.txt");
        
        Stage stage = (Stage) areaMensagens.getScene().getWindow();
        File file = fileChooser.showSaveDialog(stage);
        
        if (file != null) {
            try (FileWriter writer = new FileWriter(file)) {
                for (javafx.scene.Node node : areaMensagens.getChildren()) {
                    if (node instanceof HBox) {
                        HBox hbox = (HBox) node;
                        for (javafx.scene.Node child : hbox.getChildren()) {
                            if (child instanceof VBox) {
                                VBox grupo = (VBox) child;
                                for (javafx.scene.Node item : grupo.getChildren()) {
                                    if (item instanceof Label) {
                                        Label label = (Label) item;
                                        if (!label.getStyleClass().contains("msg-meta")) {
                                            writer.write(label.getText());
                                            writer.write("\n");
                                        }
                                    }
                                }
                            }
                        }
                        writer.write("---\n");
                    }
                }
                Platform.runLater(() -> adicionarBalaoMaria("✓ Conversa exportada para: " + file.getName()));
            } catch (IOException e) {
                Platform.runLater(() -> adicionarBalaoMaria("✗ Erro ao exportar: " + e.getMessage()));
            }
        }
    }
    // ── Ação de anexar arquivo ─────────────────────────────
    @FXML
    private void onAnexar() {
        FileChooser fileChooser = new FileChooser();
        fileChooser.getExtensionFilters().add(new FileChooser.ExtensionFilter("Todos os arquivos", "*.*"));
        
        Stage stage = (Stage) areaMensagens.getScene().getWindow();
        File file = fileChooser.showOpenDialog(stage);
        
        if (file != null) {
            adicionarBalaoUsuario("📎 Anexando: " + file.getName());
            atualizarStatus("●  enviando...", "#f59e0b");
            
            try {
                BridgeManager.getInstance().enviar("upload_arquivo", Map.of("caminho", file.getAbsolutePath()))
                    .thenAccept(resposta -> Platform.runLater(() -> {
                        if ("ok".equals(resposta.getStatus())) {
                            adicionarBalaoMaria("✓ Arquivo anexado: " + file.getName());
                        } else {
                            adicionarBalaoMaria("✗ Erro: " + resposta.getMensagemErro());
                        }
                        atualizarStatus("●  online", "#22c55e");
                    }))
                    .exceptionally(erro -> {
                        Platform.runLater(() -> {
                            adicionarBalaoMaria("✗ Erro: " + erro.getMessage());
                            atualizarStatus("●  online", "#22c55e");
                        });
                        return null;
                    });
            } catch (IOException e) {
                atualizarStatus("●  off: " + e.getMessage(), "#ef4444");
            }
        }
    }

    // ── Ação de voz (gravação e transcrição) ─────────────────────────────
    @FXML
    private void onVoz() {
        if (!gravando) {
            iniciarGravacao();
        } else {
            pararGravacaoETranscrever();
        }
    }

    private void iniciarGravacao() {
        try {
            javax.sound.sampled.AudioFormat formato = new javax.sound.sampled.AudioFormat(16000, 16, 1, true, false);
            javax.sound.sampled.DataLine.Info info = new javax.sound.sampled.DataLine.Info(javax.sound.sampled.TargetDataLine.class, formato);
            linhaAudio = (javax.sound.sampled.TargetDataLine) javax.sound.sampled.AudioSystem.getLine(info);
            linhaAudio.open(formato);
            linhaAudio.start();
            bufferAudio = new ByteArrayOutputStream();
            gravando = true;
            
            if (btnVoz != null) btnVoz.setStyle("-fx-opacity: 1.0; -fx-background-color: #e74c3c;");
            
            // Thread para ler áudio
            new Thread(() -> {
                byte[] buffer = new byte[4096];
                while (gravando) {
                    int bytesRead = linhaAudio.read(buffer, 0, buffer.length);
                    if (bytesRead > 0) {
                        bufferAudio.write(buffer, 0, bytesRead);
                    }
                }
            }).start();
            
            atualizarStatus("●  gravando...", "#ef4444");
        } catch (Exception e) {
            Platform.runLater(() -> {
                adicionarBalaoMaria("✗ Erro ao iniciar gravação: " + e.getMessage());
                gravando = false;
            });
        }
    }

    private void pararGravacaoETranscrever() {
        gravando = false;
        if (linhaAudio != null) {
            linhaAudio.stop();
            linhaAudio.close();
        }
        
        if (btnVoz != null) btnVoz.setStyle("");
        atualizarStatus("●  transcrevendo...", "#f59e0b");
        
        // Salvar áudio em arquivo temporário
        File tempFile = new File(System.getProperty("java.io.tmpdir"), "maria_audio_" + System.currentTimeMillis() + ".wav");
        try (FileOutputStream fos = new FileOutputStream(tempFile)) {
            fos.write(bufferAudio.toByteArray());
            
            // Enviar para backend transcrever
            BridgeManager.getInstance().enviar("transcrever_audio", Map.of("caminho", tempFile.getAbsolutePath()))
                .thenAccept(resposta -> Platform.runLater(() -> {
                    if ("ok".equals(resposta.getStatus())) {
                        String transcricao = resposta.getDados() != null ? resposta.getDados().toString() : "";
                        campoMensagem.setText(transcricao);
                        adicionarBalaoMaria("✓ Áudio transcrito");
                    } else {
                        adicionarBalaoMaria("✗ Erro na transcrição: " + resposta.getMensagemErro());
                    }
                    atualizarStatus("●  online", "#22c55e");
                }))
                .exceptionally(erro -> {
                    Platform.runLater(() -> {
                        adicionarBalaoMaria("✗ Erro: " + erro.getMessage());
                        atualizarStatus("●  online", "#22c55e");
                    });
                    return null;
                });
        } catch (IOException e) {
            Platform.runLater(() -> {
                adicionarBalaoMaria("✗ Erro ao salvar áudio: " + e.getMessage());
                atualizarStatus("●  online", "#22c55e");
            });
        }
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
        Node avatar = criarAvatarMaria();

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

    private Node criarAvatarMaria() {
        java.net.URL recurso = getClass().getResource("/com/tristar/maria/maria-avatar-circle.png");
        if (recurso != null) {
            ImageView avatar = new ImageView(new Image(recurso.toExternalForm()));
            avatar.setFitWidth(36);
            avatar.setFitHeight(36);
            avatar.setPreserveRatio(false);
            avatar.setClip(new Circle(18, 18, 18));
            return avatar;
        }
        Label fallback = new Label("M");
        fallback.getStyleClass().add("avatar");
        return fallback;
    }
}