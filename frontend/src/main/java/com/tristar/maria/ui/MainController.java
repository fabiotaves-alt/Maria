package com.tristar.maria.ui;

import javafx.animation.Animation;
import javafx.animation.KeyFrame;
import javafx.animation.PauseTransition;
import javafx.animation.Timeline;
import javafx.application.Platform;
import javafx.fxml.FXML;
import javafx.fxml.FXMLLoader;
import javafx.scene.Node;
import javafx.scene.Scene;
import javafx.scene.control.Label;
import javafx.scene.control.ProgressBar;
import javafx.scene.layout.VBox;
import javafx.util.Duration;

import java.io.IOException;
import java.util.HashMap;
import java.util.Map;

/**
 * Controller principal da interface do Maria.
 * Gerencia a sidebar de navegação, a área de conteúdo dinâmica, o painel
 * de chat permanente, a alternância de tema e o monitoramento em tempo real dos recursos do sistema.
 */
public class MainController {

    @FXML private VBox conteudoAtual;
    @FXML private Label labelModelo;
    @FXML private Label botaoTema;
    @FXML private Label labelStatusBar;
    @FXML private MenuItemsController menuItemsController;
    @FXML private ConversarController painelChatController;
    
    // Recursos do sistema (sidebar)
    @FXML private ProgressBar cpuBar;
    @FXML private ProgressBar ramBar;
    @FXML private ProgressBar gpuBar;
    @FXML private Label cpuLabel;
    @FXML private Label ramLabel;
    @FXML private Label gpuLabel;

    private Map<String, Node> viewsCache = new HashMap<>();
    private Scene cena;
    private boolean temaClaro = false;
    private Timeline timelineStatus;

    /** O hero (tela inicial central) é reusado como conteúdo da opção "Conversar". */
    private Node heroNode;

    public void setCena(Scene cena) {
        this.cena = cena;
    }

    public void initialize() {
        if (menuItemsController != null) {
            menuItemsController.setMainController(this);
        }
        labelModelo.setText("qwen3.5:4b · via Ollama");
        
        // Iniciar atualização periódica dos recursos do sistema (a cada 3 segundos)
        iniciarAtualizacaoStatus();
        
        carregarAba("conversar");
    }
    
    private void iniciarAtualizacaoStatus() {
        timelineStatus = new Timeline(
            new KeyFrame(Duration.seconds(3), e -> atualizarStatusSistema())
        );
        timelineStatus.setCycleCount(Animation.INDEFINITE);
        timelineStatus.play();

        // Primeira atualização com pequeno delay para aguardar inicialização da Bridge
        PauseTransition delayInicial = new PauseTransition(Duration.seconds(1));
        delayInicial.setOnFinished(e -> atualizarStatusSistema());
        delayInicial.play();
    }
    
    private void atualizarStatusSistema() {
        try {
            com.tristar.maria.bridge.BridgeManager.getInstance()
                .enviar("status", null)
                .thenAccept(resposta -> {
                    if ("ok".equals(resposta.getStatus())) {
                        Object dadosObj = resposta.getDados();
                        if (dadosObj instanceof Map) {
                            @SuppressWarnings("unchecked")
                            Map<String, Object> dados = (Map<String, Object>) dadosObj;
                            
                            Platform.runLater(() -> {
                                Double cpu = getDoubleOrNull(dados.get("cpu"));
                                Double ram = getDoubleOrNull(dados.get("ram"));
                                Double gpu = getDoubleOrNull(dados.get("gpu"));
                                String modelo = getStringOrNull(dados.get("modelo"));
                                
                                if (cpu != null && cpuBar != null) {
                                    cpuBar.setProgress(Math.min(Math.max(cpu / 100.0, 0.0), 1.0));
                                    if (cpuLabel != null) cpuLabel.setText(String.format("%.0f%%", cpu));
                                }
                                if (ram != null && ramBar != null) {
                                    ramBar.setProgress(Math.min(Math.max(ram / 100.0, 0.0), 1.0));
                                    if (ramLabel != null) ramLabel.setText(String.format("%.0f%%", ram));
                                }
                                if (gpu != null && gpuBar != null) {
                                    gpuBar.setProgress(Math.min(Math.max(gpu / 100.0, 0.0), 1.0));
                                    if (gpuLabel != null) gpuLabel.setText(String.format("%.0f%%", gpu));
                                }
                                if (modelo != null && labelModelo != null) {
                                    labelModelo.setText(modelo + " · via Ollama");
                                }
                            });
                        }
                    }
                })
                .exceptionally(erro -> {
                    // Silencioso se bridge ainda estiver iniciando
                    return null;
                });
        } catch (Exception e) {
            // Bridge não inicializada
        }
    }
    
    private Double getDoubleOrNull(Object obj) {
        if (obj instanceof Number) {
            return ((Number) obj).doubleValue();
        }
        return null;
    }
    
    private String getStringOrNull(Object obj) {
        if (obj instanceof String) {
            return (String) obj;
        }
        return null;
    }

    public void carregarAba(String nomeAba) {
        if ("conversar".equals(nomeAba)) {
            conteudoAba(hero());
            if (menuItemsController != null) {
                menuItemsController.destacar("conversar");
            }
            return;
        }
        try {
            conteudoAba(carregarView(nomeAba));
        } catch (IOException e) {
            Label erro = new Label("Erro ao carregar aba '" + nomeAba + "': " + e.getMessage());
            erro.setStyle("-fx-text-fill: #e05d8a;");
            conteudoAba(erro);
        }
        if (menuItemsController != null) {
            menuItemsController.destacar(nomeAba);
        }
    }

    private void conteudoAba(Node conteudo) {
        conteudoAtual.getChildren().clear();
        conteudoAtual.getChildren().add(conteudo);
    }

    private Node hero() {
        if (heroNode == null) {
            try {
                FXMLLoader loader = new FXMLLoader(getClass().getResource("/com/tristar/maria/hero-view.fxml"));
                heroNode = loader.load();
                Object ctrl = loader.getController();
                if (ctrl instanceof HeroController) {
                    ((HeroController) ctrl).setMainController(this);
                }
            } catch (IOException e) {
                heroNode = new Label("Erro ao carregar tela inicial: " + e.getMessage());
            }
        }
        return heroNode;
    }

    private Node carregarView(String nomeAba) throws IOException {
        if (viewsCache.containsKey(nomeAba)) {
            return viewsCache.get(nomeAba);
        }
        String fxmlPath = "/com/tristar/maria/" + nomeAba + "-view.fxml";
        FXMLLoader loader = new FXMLLoader(getClass().getResource(fxmlPath));
        Node view = loader.load();
        viewsCache.put(nomeAba, view);
        return view;
    }

    /** Ação rápida do hero preenche o campo de mensagem do chat. */
    public void acaoRapida(String prompt) {
        if (painelChatController != null) {
            painelChatController.definirMensagem(prompt);
        }
    }

    @FXML
    private void alternarTema() {
        if (cena == null) {
            return;
        }
        cena.getStylesheets().clear();
        String css = temaClaro
                ? "/com/tristar/maria/theme-dark.css"
                : "/com/tristar/maria/theme-light.css";
        cena.getStylesheets().add(getClass().getResource(css).toExternalForm());
        temaClaro = !temaClaro;
        botaoTema.setText(temaClaro ? "☾" : "☀");
    }

    public void setStatusBar(String texto) {
        if (labelStatusBar != null) {
            labelStatusBar.setText(texto);
        }
    }
}
