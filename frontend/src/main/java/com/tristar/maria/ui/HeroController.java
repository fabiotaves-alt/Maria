package com.tristar.maria.ui;

import javafx.fxml.FXML;
import javafx.scene.image.ImageView;
import javafx.scene.shape.Circle;

/**
 * Controller do hero (tela inicial central).
 * As ações rápidas preenchem o campo de mensagem do painel de chat.
 */
public class HeroController {

    private MainController mainController;

    @FXML
    private Circle avatarGlow;

    @FXML
    private ImageView avatarImage;


    public void setMainController(MainController mainController) {
        this.mainController = mainController;
    }

    @FXML
    public void initialize() {

        // Recorte circular real do avatar (ImageView não aceita border-radius)
        if (avatarImage != null) {
            Circle recorte = new Circle(90, 90, 90);
            avatarImage.setClip(recorte);
        }
    }

    @FXML
    private void acaoAnalisarDocumento() {
        acao("Analise este documento que estou enviando.");
    }

    @FXML
    private void acaoAnalisarDados() {
        acao("Analise os dados e resuma as principais métricas.");
    }

    @FXML
    private void acaoGerarTexto() {
        acao("Escreva um texto sobre o assunto que eu informar.");
    }

    @FXML
    private void acaoResponderVoz() {
        acao("Responda por voz (recurso em desenvolvimento).");
    }

    private void acao(String prompt) {
        if (mainController != null) {
            mainController.acaoRapida(prompt);
        }
    }
}