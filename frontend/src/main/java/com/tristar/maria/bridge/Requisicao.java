package com.tristar.maria.bridge;

public class Requisicao {
    private String id;
    private String comando;
    private Object payload;

    public Requisicao() {
    }

    public Requisicao(String id, String comando, Object payload) {
        this.id = id;
        this.comando = comando;
        this.payload = payload;
    }

    public String getId() { return id; }
    public void setId(String id) { this.id = id; }

    public String getComando() { return comando; }
    public void setComando(String comando) { this.comando = comando; }

    public Object getPayload() { return payload; }
    public void setPayload(Object payload) { this.payload = payload; }
}