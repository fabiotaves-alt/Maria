package com.tristar.maria.bridge;

public class Resposta {
    private String id;
    private String status;
    private Object dados;
    private String mensagemErro;

    public Resposta() {
    }

    public String getId() { return id; }
    public void setId(String id) { this.id = id; }

    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }

    public Object getDados() { return dados; }
    public void setDados(Object dados) { this.dados = dados; }

    public String getMensagemErro() { return mensagemErro; }
    public void setMensagemErro(String mensagemErro) { this.mensagemErro = mensagemErro; }
}