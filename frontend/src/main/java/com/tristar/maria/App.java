package com.tristar.maria;

import com.tristar.maria.bridge.PythonBridgeService;
import com.tristar.maria.bridge.Resposta;
import javafx.application.Application;
import javafx.application.Platform;
import javafx.geometry.Insets;
import javafx.geometry.Pos;
import javafx.scene.Scene;
import javafx.scene.control.Button;
import javafx.scene.control.Label;
import javafx.scene.control.TextArea;
import javafx.scene.control.TextField;
import javafx.scene.layout.BorderPane;
import javafx.scene.layout.HBox;
import javafx.scene.layout.VBox;
import javafx.scene.text.Font;
import javafx.stage.Stage;

import java.io.IOException;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.concurrent.CompletableFuture;

/**
 * MARIA — Interface JavaFX (Fase 0 — esqueleto).
 *
 * Responsabilidades:
 *     - Exibir a janela principal "Maria — Fase 0 (esqueleto)"
 *     - Iniciar o processo Python via PythonBridgeService (../backend/main.py --bridge)
 *     - Enviar mensagens de chat ao backend e exibir as respostas
 *     - Realizar o handshake ping/pong na inicialização
 *
 * Uso (Maven):
 *     mvn javafx:run  (a partir de frontend/)
 */
public class App extends Application {

    private static final String CAMINHO_PYTHON = "../.venv/Scripts/python.exe";
    private static final String CAMINHO_SCRIPT_MAIN = "../backend/main.py";

    private PythonBridgeService ponte;
    private TextArea areaChat;
    private TextField campoEntrada;
    private Label labelStatus;

    public static void main(String[] args) {
        launch(args);
    }

    @Override
    public void start(Stage palco) {
        palco.setTitle("Maria — Fase 0 (esqueleto)");

        // ── Área de chat ──────────────────────────────────────
        areaChat = new TextArea();
        areaChat.setEditable(false);
        areaChat.setWrapText(true);
        areaChat.setFont(Font.font("Consolas", 13));
        areaChat.setPromptText("Aguardando conexão com o backend...");

        // ── Campo de entrada + botão enviar ───────────────────
        campoEntrada = new TextField();
        campoEntrada.setPromptText("Digite sua mensagem...");
        campoEntrada.setOnAction(e -> enviarMensagem());

        Button botaoEnviar = new Button("Enviar");
        botaoEnviar.setOnAction(e -> enviarMensagem());

        HBox barraEntrada = new HBox(8, campoEntrada, botaoEnviar);
        barraEntrada.setPadding(new Insets(8));
        barraEntrada.setAlignment(Pos.CENTER);
        HBox.setHgrow(campoEntrada, javafx.scene.layout.Priority.ALWAYS);

        // ── Status ────────────────────────────────────────────
        labelStatus = new Label("Inicializando...");
        labelStatus.setStyle("-fx-text-fill: #666;");

        VBox rodape = new VBox(4, barraEntrada, labelStatus);
        rodape.setPadding(new Insets(8));

        // ── Layout principal ──────────────────────────────────
        BorderPane raiz = new BorderPane();
        raiz.setCenter(areaChat);
        raiz.setBottom(rodape);

        Scene cena = new Scene(raiz, 720, 480);
        palco.setScene(cena);

        palco.setOnCloseRequest(e -> encerrar());
        palco.show();

        // ── Iniciar ponte com o backend ───────────────────────
        iniciarBackend();
    }

    /**
     * Inicia o processo Python via PythonBridgeService e executa o
     * handshake ping/pong.
     */
    private void iniciarBackend() {
        ponte = new PythonBridgeService();
        try {
            Path raizProjeto = Paths.get("").toAbsolutePath().normalize();
            String caminhoPython = raizProjeto.resolve(CAMINHO_PYTHON).toString();
            String caminhoScript = raizProjeto.resolve(CAMINHO_SCRIPT_MAIN).toString();

            labelStatus.setText("Iniciando backend Python: " + caminhoPython + " " + caminhoScript);
            ponte.iniciar(caminhoPython, caminhoScript);

            // Handshake ping/pong
            ponte.enviar("ping", null)
                    .thenAccept(resposta -> Platform.runLater(() -> processarResposta("ping", resposta)))
                    .exceptionally(erro -> {
                        Platform.runLater(() -> {
                            labelStatus.setText("Falha no handshake: " + erro.getMessage());
                            areaChat.appendText("[ERRO] " + erro.getMessage() + "\n");
                        });
                        return null;
                    });
        } catch (IOException e) {
            labelStatus.setText("Falha ao iniciar backend: " + e.getMessage());
            areaChat.appendText("[ERRO] " + e.getMessage() + "\n");
        }
    }

    /**
     * Envia a mensagem digitada ao backend via bridge.
     */
    private void enviarMensagem() {
        String texto = campoEntrada.getText().trim();
        if (texto.isEmpty() || ponte == null) {
            return;
        }
        campoEntrada.clear();
        areaChat.appendText("Você: " + texto + "\n");

        try {
            ponte.enviar("chat", java.util.Map.of("mensagem", texto))
                    .thenAccept(resposta -> Platform.runLater(() -> processarResposta("chat", resposta)));
        } catch (IOException e) {
            areaChat.appendText("[ERRO] " + e.getMessage() + "\n");
        }
    }

    /**
     * Processa uma resposta do backend e exibe no chat.
     */
    private void processarResposta(String comando, Resposta resposta) {
        if ("ping".equals(comando)) {
            if ("ok".equals(resposta.getStatus()) && "pong".equals(resposta.getDados())) {
                labelStatus.setText("Conectado ao backend Python (ping/pong). Pronto para conversar.");
                areaChat.appendText("[SISTEMA] Backend conectado. Digite sua mensagem.\n");
            } else {
                labelStatus.setText("Handshake falhou: " + resposta.getMensagemErro());
            }
            return;
        }

        // Resposta de chat
        if ("ok".equals(resposta.getStatus())) {
            Object dados = resposta.getDados();
            areaChat.appendText("Maria: " + (dados != null ? dados.toString() : "(sem resposta)") + "\n");
        } else {
            areaChat.appendText("[ERRO] " + resposta.getMensagemErro() + "\n");
        }
    }

    /**
     * Encerra o processo Python ao fechar a janela.
     */
    private void encerrar() {
        if (ponte != null) {
            try {
                ponte.enviar("encerrar", null);
            } catch (IOException ignored) {
                // Processo já pode ter encerrado
            }
            ponte.encerrar();
        }
        Platform.exit();
    }
}