package com.nyc.maria.ui;

import javafx.fxml.FXML;
import javafx.scene.control.ListView;
import javafx.scene.control.TextField;

public class MemoriaController {
    @FXML private ListView<String> listaFatos;
    @FXML private TextField campoNovoFato;

    public void initialize() {
        listaFatos.getItems().add("(Nenhum fato memorizado - Fase 0)");
    }

    @FXML
    private void adicionarFato() {
        String fato = campoNovoFato.getText().trim();
        if (!fato.isEmpty()) {
            listaFatos.getItems().add(fato);
            campoNovoFato.clear();
        }
    }
}
