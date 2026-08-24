package com.tristar.maria.ui;

import javafx.fxml.FXML;
import javafx.scene.layout.VBox;
import javafx.scene.control.Button;

/**
 * Controller para o menu lateral de navegação.
 * Gerencia os botões das 8 abas do Maria.
 */
public class MenuItemsController {

    @FXML private Button btnConversar;
    @FXML private Button btnArquivos;
    @FXML private Button btnAnaliseDados;
    @FXML private Button btnVisao;
    @FXML private Button btnVoz;
    @FXML private Button btnMemoria;
    @FXML private Button btnAutomacoes;
    @FXML private Button btnConfiguracoes;

    private MainController mainController;

    public void setMainController(MainController mainController) {
        this.mainController = mainController;
    }

    @FXML
    private void abrirConversar() {
        if (mainController != null) mainController.carregarAba("conversar");
    }

    @FXML
    private void abrirArquivos() {
        if (mainController != null) mainController.carregarAba("arquivos");
    }

    @FXML
    private void abrirAnaliseDados() {
        if (mainController != null) mainController.carregarAba("analise-dados");
    }

    @FXML
    private void abrirVisao() {
        if (mainController != null) mainController.carregarAba("visao");
    }

    @FXML
    private void abrirVoz() {
        if (mainController != null) mainController.carregarAba("voz");
    }

    @FXML
    private void abrirMemoria() {
        if (mainController != null) mainController.carregarAba("memoria");
    }

    @FXML
    private void abrirAutomacoes() {
        if (mainController != null) mainController.carregarAba("automacoes");
    }

    @FXML
    private void abrirConfiguracoes() {
        if (mainController != null) mainController.carregarAba("configuracoes");
    }
}
