package com.nyc.maria.ui;

import javafx.fxml.FXML;
import javafx.fxml.FXMLLoader;
import javafx.scene.Node;
import javafx.scene.layout.VBox;
import javafx.scene.control.Label;

import java.io.IOException;
import java.util.HashMap;
import java.util.Map;

/**
 * Controller principal da interface do Maria.
 * Gerencia a sidebar de navegação e a área de conteúdo dinâmica.
 */
public class MainController {

    @FXML private VBox conteudoAtual;

    private Map<String, Node> viewsCache = new HashMap<>();

    public void initialize() {
        // Cache vazio inicialmente; views são carregadas sob demanda
    }

    /**
     * Carrega uma aba específica na área de conteúdo.
     * @param nomeAba Nome da aba (ex: "conversar", "arquivos", etc.)
     */
    public void carregarAba(String nomeAba) {
        try {
            Node view = carregarView(nomeAba);
            conteudoAtual.getChildren().clear();
            conteudoAtual.getChildren().add(view);
        } catch (IOException e) {
            Label erroLabel = new Label("Erro ao carregar aba '" + nomeAba + "': " + e.getMessage());
            erroLabel.setStyle("-fx-text-fill: red;");
            conteudoAtual.getChildren().clear();
            conteudoAtual.getChildren().add(erroLabel);
        }
    }

    private Node carregarView(String nomeAba) throws IOException {
        if (viewsCache.containsKey(nomeAba)) {
            return viewsCache.get(nomeAba);
        }

        String fxmlPath = "/com/nyc/maria/" + nomeAba + "-view.fxml";
        FXMLLoader loader = new FXMLLoader(getClass().getResource(fxmlPath));
        Node view = loader.load();

        // Se o controller tiver método setMainController, chama-o
        Object controller = loader.getController();
        if (controller != null && controller.getClass().getMethod("setMainController", MainController.class) != null) {
            // Método existe, mas não vamos chamar aqui para evitar dependência circular
        }

        viewsCache.put(nomeAba, view);
        return view;
    }
}
