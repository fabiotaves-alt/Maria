package com.tristar.maria.bridge;

import java.io.IOException;

/**
 * Ponto único de acesso ao PythonBridgeService, compartilhado entre
 * App.java e os controllers das abas (ex.: ConversarController).
 */
public class BridgeManager {

    private static PythonBridgeService instancia;

    private BridgeManager() {
    }

    public static synchronized PythonBridgeService iniciar(String caminhoPython, String caminhoScriptMain) throws IOException {
        if (instancia == null) {
            instancia = new PythonBridgeService();
            instancia.iniciar(caminhoPython, caminhoScriptMain);
        }
        return instancia;
    }

    public static PythonBridgeService getInstance() {
        if (instancia == null) {
            throw new IllegalStateException(
                "BridgeManager não foi iniciado. Chame BridgeManager.iniciar(...) no start() do App antes de usar getInstance()."
            );
        }
        return instancia;
    }

    public static synchronized void encerrar() {
        if (instancia != null) {
            instancia.encerrar();
            instancia = null;
        }
    }
}
