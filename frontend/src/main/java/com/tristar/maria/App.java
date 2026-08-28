package com.tristar.maria;

import com.tristar.maria.bridge.BridgeManager;
import com.tristar.maria.dao.DatabaseManager;
import com.tristar.maria.ui.MainController;
import javafx.application.Application;
import javafx.application.Platform;
import javafx.fxml.FXMLLoader;
import javafx.scene.Parent;
import javafx.scene.Scene;
import javafx.stage.Stage;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.sql.SQLException;

/**
 * MARIA — ponto de entrada JavaFX.
 *
 * Responsabilidades:
 *     - Inicializar banco de dados SQLite via DatabaseManager
 *     - Iniciar o processo Python via BridgeManager (backend/main.py --bridge)
 *     - Carregar main-view.fxml (sidebar + navegação entre as 8 abas)
 *     - Encerrar o processo Python e fechar conexão DB ao fechar a janela
 */
public class App extends Application {

    private static String detectarCaminhoPython(Path raizRepositorio) {
        boolean isWindows = System.getProperty("os.name", "").toLowerCase().contains("win");
        
        // Tentativas em ordem de prioridade
        Path[] possiveisCaminhos = isWindows ? new Path[] {
            raizRepositorio.resolve(".venv/Scripts/python.exe"),
            raizRepositorio.resolve("backend/.venv/Scripts/python.exe"),
            raizRepositorio.resolve("venv/Scripts/python.exe")
        } : new Path[] {
            raizRepositorio.resolve(".venv/bin/python"),
            raizRepositorio.resolve("backend/.venv/bin/python"),
            raizRepositorio.resolve("venv/bin/python")
        };

        for (Path p : possiveisCaminhos) {
            if (Files.exists(p)) {
                return p.toAbsolutePath().normalize().toString();
            }
        }

        // Fallback: comando python do PATH do sistema
        return isWindows ? "python" : "python3";
    }

    private static Path resolverRaizRepositorio() {
        Path atual = Paths.get("").toAbsolutePath().normalize();
        if (atual.endsWith("frontend")) {
            return atual.getParent();
        }
        return atual;
    }

    @Override
    public void start(Stage palco) throws IOException {
        palco.setTitle("MARIA — Assistente de IA Pessoal");

        // Inicializa banco de dados
        try {
            DatabaseManager dbManager = DatabaseManager.getInstance();
            dbManager.inicializarTabelas();
            System.out.println("[INFO] Banco de dados inicializado com sucesso em: " + DatabaseManager.resolverCaminhoBanco());
        } catch (SQLException e) {
            System.err.println("[ERRO] Falha ao inicializar banco de dados: " + e.getMessage());
            e.printStackTrace();
        }

        Path raizRepositorio = resolverRaizRepositorio();
        String caminhoPython = detectarCaminhoPython(raizRepositorio);
        String caminhoScript = raizRepositorio.resolve("backend/main.py").toAbsolutePath().normalize().toString();

        try {
            System.out.println("[INFO] Iniciando Bridge Python: " + caminhoPython + " -> " + caminhoScript);
            BridgeManager.iniciar(caminhoPython, caminhoScript);
        } catch (IOException e) {
            System.err.println("[ERRO] Falha ao iniciar backend Python: " + e.getMessage());
            // Não aborta a UI imediatamente para permitir diagnóstico de erro na interface
        }

        FXMLLoader loader = new FXMLLoader(getClass().getResource("/com/tristar/maria/main-view.fxml"));
        Parent raiz = loader.load();

        Scene cena = new Scene(raiz, 1280, 800);
        cena.getStylesheets().add(getClass().getResource("/com/tristar/maria/theme-dark.css").toExternalForm());
        palco.setScene(cena);

        // Conecta a cena ao controller para permitir a alternância de tema.
        Object ctrl = loader.getController();
        if (ctrl instanceof MainController) {
            ((MainController) ctrl).setCena(cena);
        }

        palco.setOnCloseRequest(e -> encerrar());
        palco.show();
    }

    private void encerrar() {
        BridgeManager.encerrar();
        DatabaseManager.getInstance().fechar();
        Platform.exit();
    }

    public static void main(String[] args) {
        launch(args);
    }
}
