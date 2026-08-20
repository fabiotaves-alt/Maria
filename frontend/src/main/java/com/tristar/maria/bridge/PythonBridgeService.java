package com.tristar.maria.bridge;

import com.fasterxml.jackson.databind.ObjectMapper;

import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicLong;

/**
 * Gerencia o processo Python do backend do Maria: inicia via ProcessBuilder,
 * envia requisições e associa respostas pelo campo "id" (protocolo JSON por linha).
 */
public class PythonBridgeService {

    private Process processo;
    private BufferedWriter escritor;
    private BufferedReader leitor;
    private Thread threadLeitura;

    private final ObjectMapper mapper = new ObjectMapper();
    private final AtomicLong contadorId = new AtomicLong(0);
    private final ConcurrentHashMap<String, CompletableFuture<Resposta>> pendentes = new ConcurrentHashMap<>();

    /**
     * Inicia o processo Python.
     * @throws IOException se o executável Python ou o script não forem encontrados.
     */
    public void iniciar(String caminhoPython, String caminhoScriptMain) throws IOException {
        ProcessBuilder pb = new ProcessBuilder(caminhoPython, caminhoScriptMain);
        pb.redirectErrorStream(false);
        processo = pb.start();

        escritor = new BufferedWriter(new OutputStreamWriter(processo.getOutputStream(), StandardCharsets.UTF_8));
        leitor = new BufferedReader(new InputStreamReader(processo.getInputStream(), StandardCharsets.UTF_8));

        threadLeitura = new Thread(this::loopLeitura, "python-bridge-reader");
        threadLeitura.setDaemon(true);
        threadLeitura.start();
    }

    private void loopLeitura() {
        try {
            String linha;
            while ((linha = leitor.readLine()) != null) {
                Resposta resposta = mapper.readValue(linha, Resposta.class);
                CompletableFuture<Resposta> future = pendentes.remove(resposta.getId());
                if (future != null) {
                    future.complete(resposta);
                }
            }
        } catch (IOException e) {
            // Stream fechado (processo encerrado/crash) — reportar a quem estiver aguardando.
            pendentes.values().forEach(f -> f.completeExceptionally(e));
            pendentes.clear();
        }
    }

    /**
     * Envia um comando ao backend Python e retorna um future com a resposta.
     * @throws IOException se a escrita no stdin do processo falhar.
     */
    public CompletableFuture<Resposta> enviar(String comando, Object payload) throws IOException {
        String id = String.valueOf(contadorId.incrementAndGet());
        Requisicao req = new Requisicao(id, comando, payload);
        CompletableFuture<Resposta> future = new CompletableFuture<>();
        pendentes.put(id, future);

        String json = mapper.writeValueAsString(req);
        synchronized (escritor) {
            escritor.write(json);
            escritor.newLine();
            escritor.flush();
        }
        return future;
    }

    /** Encerra o processo Python, se estiver em execução. */
    public void encerrar() {
        if (processo != null && processo.isAlive()) {
            processo.destroy();
        }
    }
}