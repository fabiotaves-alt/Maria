# 🚀 Plano de Migração MARIA v4.0 — JavaFX → Tauri

## 📋 Contexto: Resposta ao Relatório do Investidor

O investidor identificou **5 riscos críticos**:
1. **Gap de Design** — JavaFX parece "app de 2010" vs conceito SaaS premium
2. **Stack Legada** — JavaFX em declínio, difícil contratação
3. **Modelo 3B Fraco** — Insuficiente para raciocínio complexo
4. **Instalação Complexa** — Barreira de entrada alta para usuários
5. **Dependência de Hardware** — Limita TAM de empresas pequenas

**Este plano transforma cada risco em vantagem competitiva.**

---

## 🎯 Estratégia Geral: "Não Reescrever, Evoluir"

### Princípios Fundamentais

1. **Backend Python INTACTO** — Os 818 linhas de `main.py` são ouro puro:
   - 19 comandos bridge já funcionam perfeitamente
   - 86 testes pytest passando
   - LlamaClient, tool chaining, session storage tudo testado
   
2. **Frontend Tauri + React** — Substitui APENAS a camada visual:
   - JavaFX (21 controllers FXML) → React (8 componentes page)
   - CSS JavaFX → Tailwind CSS + Framer Motion
   - Ponte JSON stdin/stdout → HTTP local (localhost:8081)

3. **Arquitetura Híbrida de Modelos** — O Qwen 3.5 não é substituído, é **orquestrado**:
   - 3.5B: Interface, voz, tarefas rápidas (<2s)
   - 8B: Raciocínio complexo (relatórios, análise jurídica)
   - CodeQwen 7B: Geração de scripts Python

---

## 🏗️ Arquitetura Técnica Proposta

```
maria/
├── backend/                    ← MANTIDO (Python existente)
│   ├── main.py                 ← Modo bridge HTTP (nova porta 8081)
│   ├── core/                   ← LlamaClient, tools, etc. (INTACTO)
│   └── tests/                  ← 86 testes pytest (MANTIDOS)
│
├── frontend-tauri/             ← NOVO (substitui frontend/)
│   ├── src/                    ← React + TypeScript
│   │   ├── components/         ← Avatar, ChatInput, Sidebar, etc.
│   │   ├── pages/              ← 8 abas (Conversar, Arquivos, etc.)
│   │   ├── hooks/              ← useChat, useAudio, useFiles
│   │   ├── stores/             ← Zustand (estado global)
│   │   └── styles/             ← Tailwind + aura rosa
│   │
│   ├── src-tauri/              ← Rust (Tauri v2)
│   │   ├── commands/           ← IPC: chat, files, system
│   │   └── sidecar.rs          ← Gerencia processo Python
│   │
│   └── package.json
│
├── shared/
│   ├── schema.sql              ← Banco SQLite (MANTIDO)
│   └── maria.db                ← Database WAL (MANTIDO)
│
└── installers/                 ← NOVO
    ├── windows/                ← MSI one-click
    ├── linux/                  ← .deb + AppImage
    └── docker-compose.yml      ← Enterprise on-premise
```

---

## 📅 Roadmap de 17 Semanas (4 Meses)

### **Fase 1: v3.3 — "O Pivô Visual"** (Semanas 1-4)

**Objetivo:** Replicar pixel-perfect o design conceitual com aura rosa, glassmorphism e animações.

| Semana | Entregável | Critério de Aceite |
|--------|-----------|-------------------|
| 1 | Setup Tauri + React + Tailwind | `npm run tauri dev` abre janela com "Hello MARIA" |
| 2 | Ponte HTTP backend Python | Botão "Enviar" no React chama `POST /chat` e mostra resposta |
| 3 | Aba "Conversar" completa | Chat com histórico, streaming, avatar estático |
| 4 | Aura rosa + glassmorphism | UI idêntica ao conceito (Figma → código) |

**Risco Mitigado:** Gap de Design → Eliminado

---

### **Fase 2: v3.4 — "O Cérebro Duplo"** (Semanas 5-8)

**Objetivo:** Implementar roteamento inteligente de modelos (3B ↔ 8B).

| Semana | Entregável | Critério de Aceite |
|--------|-----------|-------------------|
| 5 | Download automático Llama 3.2 8B Q4 | Script baixa modelo do HuggingFace (~5GB) |
| 6 | Model Router em Python | Classificador decide qual modelo usar por tarefa |
| 7 | Benchmark comparativo | Relatório: 3B vs 8B em 20 tarefas reais |
| 8 | Fallback gracioso | Se RAM < 8GB, usa só 3B com aviso ao usuário |

**Risco Mitigado:** Modelo 3B fraco → Arquitetura adaptativa

---

### **Fase 3: v3.5 — "O Instalador One-Click"** (Semanas 9-12)

**Objetivo:** Empacotamento profissional para Windows/Linux/macOS.

| Semana | Entregável | Critério de Aceite |
|--------|-----------|-------------------|
| 9 | Backend Python como sidecar Tauri | Tauri inicia Python automaticamente no startup |
| 10 | Embed Python runtime + modelos | Instalador inclui Python embeddable (sem instalar Python separado) |
| 11 | MSI Windows + .deb Linux | `setup.exe` instala tudo em <5 minutos |
| 12 | Docker Compose enterprise | `docker-compose up` sobe MARIA on-premise |

**Risco Mitigado:** Instalação complexa → Plug-and-play

---

### **Fase 4: v3.6 — "A Voz da MARIA"** (Semanas 13-16)

**Objetivo:** TTS + STT locais com avatar animado sincronizado.

| Semana | Entregável | Critério de Aceite |
|--------|-----------|-------------------|
| 13 | Whisper.cpp integrado | Transcrição de áudio em tempo real (<3s delay) |
| 14 | Piper TTS (voz PT-BR) | MARIA fala com voz feminina natural |
| 15 | Avatar Live2D/Cubism | Boca sincroniza com áudio do TTS |
| 16 | Aura reativa à voz | Shaders WebGL pulsam conforme fala do usuário |

**Risco Mitigado:** Chatbot genérico → Assistente com personalidade

---

### **Fase 5: v4.0 — "Lançamento Parceiro Fundador"** (Semana 17+)

**Objetivo:** Validar mercado com 10 empresas piloto.

| Atividade | Métrica de Sucesso |
|----------|-------------------|
| Recrutar 10 escritórios (advocacia/contabilidade) | 10 NDAs assinados |
| 6 meses de uso gratuito | 60% conversão para licença paga |
| Coletar depoimentos em vídeo | 5 cases de sucesso documentados |
| Refinar roadmap baseado em feedback | Top 3 features mais pedidas implementadas |

**Risco Mitigado:** Mercado incerto → Validado com clientes reais

---

## 🔧 Detalhamento Técnico: Ponte Python ↔ Tauri

### Opção A: HTTP Local (Recomendada)

**Vantagens:**
- Backend Python quase inalterado (só muda de stdin/stdout para HTTP)
- Debug fácil (Postman, curl)
- Independente de linguagem (Rust, React, qualquer um chama)

**Implementação em `backend/main.py`:**

```python
# Adicionar ao final de main.py (após _modo_bridge)

from flask import Flask, request, jsonify
import threading

app = Flask(__name__)

@app.route('/chat', methods=['POST'])
def chat_endpoint():
    data = request.json
    # Reutilizar lógica existente do modo bridge
    resposta = processar_chat(data['mensagem'])
    return jsonify({"status": "ok", "dados": resposta})

@app.route('/status', methods=['GET'])
def status_endpoint():
    return jsonify(_get_system_status())

def rodar_servidor_http(porta=8081):
    threading.Thread(target=lambda: app.run(port=porta), daemon=True).start()

# No __main__:
if args.bridge_http:
    rodar_servidor_http()
    _modo_bridge()  # Mantém stdin/stdout para compatibilidade
```

**Chamada do React:**

```typescript
// src/hooks/useChat.ts
const enviarMensagem = async (texto: string) => {
  const response = await fetch('http://localhost:8081/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ mensagem: texto }),
  });
  const data = await response.json();
  return data.dados;
};
```

---

### Opção B: IPC Nativo Tauri (Alternativa)

**Vantagens:**
- Mais seguro (sem abrir porta de rede)
- Tipagem forte (Rust → TypeScript)
- Menor latência

**Desvantagens:**
- Requer reescrever comandos em Rust
- Debug mais complexo

**Exemplo `src-tauri/src/commands/chat.rs`:**

```rust
#[tauri::command]
async fn send_message(message: String) -> Result<String, String> {
    // Chamar backend Python via stdin/stdout ou HTTP interno
    let resposta = chamar_backend_python(&message).await?;
    Ok(resposta)
}
```

**Recomendação:** Começar com **Opção A (HTTP)** para velocidade, migrar para **Opção B (IPC)** se necessário por segurança.

---

## 💰 Estimativa de Custos de Migração

| Item | Custo (BRL) | Justificativa |
|------|------------|---------------|
| Dev React/Tauri (freelancer sênior, 4 meses) | R$ 80.000 | 16 semanas × R$ 5.000/semana |
| Designer UI/UX (Figma → código) | R$ 15.000 | 3 semanas de trabalho |
| Modelos LLM 8B + infraestrutura | R$ 0 | Open-source (HuggingFace) |
| Certificados de assinatura (Windows) | R$ 2.000 | Código assinatura Microsoft |
| Servidores de teste (Windows/Linux/Mac) | R$ 5.000 | Mini-PCs para QA multiplataforma |
| **Total** | **R$ 102.000** | |

**Comparação:** Manter JavaFX custaria R$ 60.000/ano em devs especializados escassos + perda de oportunidades de venda.

---

## 📊 Matriz de Riscos — Antes vs Depois

| Risco Original | Antes (JavaFX) | Depois (Tauri) | Status |
|---------------|----------------|----------------|--------|
| UI "de 2010" | Alta prob. / Alto impacto | Baixa — Design moderno replicado | ✅ Mitigado |
| Dificuldade contratação JavaFX | Média / Alto | Eliminada — Pool npm global | ✅ Eliminado |
| Modelo 3B fraco | Alta / Alto | Baixa — Roteamento 3B/8B | ✅ Mitigado |
| Instalação complexa | Alta / Médio | Baixa — MSI one-click | ✅ Mitigado |
| Dependência hardware | Alta / Médio | Baixa — Fallback gracioso + Maria Box | ✅ Mitigado |
| Mercado incerto | — | Validado — 10 parceiros fundadores | ✅ Validado |

**Nota Estimada Pós-Migração:** **8.5/10** (vs 6.5 atual)

---

## 🎁 Bônus: "Maria Box" — Hardware como Receita

**Ideia:** Vender mini-PC pré-configurado com MARIA instalada.

**Especificação:**
- Intel NUC 13 Pro ou similar
- 32GB RAM (roda 8B confortavelmente)
- SSD 1TB NVMe
- MARIA + modelos 3B + 8B + CodeQwen pré-instalados
- Preço: R$ 4.500 (custo) → R$ 6.999 (venda) + licença anual R$ 2.400

**Vantagem:** 
- Remove barreira de hardware para PMEs
- Receita recorrente de hardware + software
- Diferencial competitivo vs soluções cloud

---

## ✅ Checklist de Validação Pré-Investimento

Antes de pedir capital, o desenvolvedor deve entregar:

- [ ] **Protótipo Tauri funcional** (semana 4) — UI moderna rodando
- [ ] **Benchmark 3B vs 8B** (semana 8) — Dados concretos de qualidade
- [ ] **Instalador MSI alpha** (semana 12) — Qualquer leigo instala em 5 min
- [ ] **3 cartas de intenção** de escritórios interessados no programa Parceiro Fundador
- [ ] **Pitch deck atualizado** com nova nota 8.5/10 e roadmap de 17 semanas

---

## 🚀 Próximos Passos Imediatos (Esta Semana)

1. **Criar repositório `frontend-tauri`** e rodar `npm create tauri-app@latest`
2. **Testar ponte HTTP** — Modificar `main.py` para aceitar requisições HTTP
3. **Replicar 1 aba** — "Conversar" do zero em React
4. **Validar com investidor** — Mostrar protótipo em 7 dias e renegociar termos

---

## 💬 Mensagem Final ao Investidor

> "Você identificou exatamente onde dói. E agora nós sabemos exatamente onde mirar. Não estamos pedindo dinheiro para 'continuar tentando'. Estamos pedindo dinheiro para executar um plano com milestones claros, entregáveis mensuráveis e prova de mercado em 6 meses. A MARIA não é um protótipo. Ela é uma assistente que ainda não se vestiu para o trabalho. Dê-nos 4 meses e o terno dela vai estar pronto."

---

**Documento criado:** 2026-08-28  
**Autor:** Equipe de Desenvolvimento MARIA  
**Versão:** 1.0 (Plano Preliminar)
