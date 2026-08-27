package com.tristar.maria.ui;

import javafx.fxml.FXML;
import javafx.fxml.FXMLLoader;
import javafx.scene.Node;
import javafx.scene.Scene;
import javafx.scene.control.Label;
import javafx.scene.layout.VBox;

import java.io.IOException;
import java.util.HashMap;
import java.util.Map;

/**
 * Controller principal da interface do Maria.
 * Gerencia a sidebar de navegação, a área de conteúdo dinâmica, o painel
 * de chat permanente e a alternância de tema.
 */
public class MainController {

    @FXML private VBox conteudoAtual;
    @FXML private Label labelModelo;
    @FXML private Label botaoTema;
    @FXML private Label labelStatusBar;
    @FXML private MenuItemsController menuItemsController;
    @FXML private ConversarController painelChatController;

    private Map<String, Node> viewsCache = new HashMap<>();
    private Scene cena;
    private boolean temaClaro = false;

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
        carregarAba("conversar");
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