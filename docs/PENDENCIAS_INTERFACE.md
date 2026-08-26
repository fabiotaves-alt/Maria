# Pendências de Interface — MARIA (v2.13.0)

**Data:** 2026-08-24
**Escopo:** redesign da interface JavaFX espelhando os mockups (3 colunas + barras).

---

## 1. Elementos mockados (que aguardam implementação futura)

| Elemento | Onde aparece | Situação atual |
|----------|-------------|----------------|
| **Recursos do sistema (CPU/RAM/GPU)** | Sidebar → card "RECURSOS DO SISTEMA" | Valores fixos de exemplo (42/61/18%). Barras reais podem usar `com.sun.management.OperatingSystemMXBean` (CPU/RAM) — GPU não é exposta de forma portátil pelo JDK |
| **MODO LOCAL / MODELO** | Topbar (pill) e sidebar | Fixos e estáticos: "● MODO LOCAL", "Llama 3.1 8B · via Ollama (mockado)". Ideal: novo comando bridge `status` no backend para popular com dados reais |
| **Ações rápidas (hero)** | Hero central → 4 botões | Ao clicar, preenchem o campo de mensagem do chat com um prompt pré-definido (ex.: "Analisar Documento"). Funcionalidade real (enviar o arquivo/navegação) fica para fases futuras |
| **Anexar (📎)** | Input do chat | Desabilitado visualmente (`mouseTransparent`, opacidade 0.4) — upload de arquivos é futuro |
| **Voz (🎤)** | Input do chat | Desabilitado — integração com Whisper.cpp é recurso futuro |
| **Dropdown "⋯" do chat** | Header do painel de chat | Sem ação configurada ainda |
| **Minimizar/Maximizar/Fechar customizados** | Topbar | Mantidas as decorações nativas da janela (não customizamos o `Stage`) nesta fase |

## 2. Como inserir a foto da Maria (avatar)

O avatar da tela inicial usa um **placeholder** (círculo gradiente rosa + letra "M") via CSS `.avatar-hero`.

Para usar a foto/ilustração real:

1. Coloque a imagem em:
   `frontend/src/main/resources/com/tristar/maria/images/avatar.png`
2. No `hero-view.fxml`, troque o `<Label ... styleClass="avatar avatar-hero">` por um `<ImageView>` circular referenciando a imagem em `@../images/avatar.png`, mantendo `styleClass="avatar-hero"`.
3. O avatar das **bolhas de chat** (canto esquerdo das mensagens da Maria) também poderá usar a mesma imagem — hoje é um `Label "M"` no `ConversarController`.

> O código Java do `ConversarController` pode ser ampliado para carregar a imagem via `getClass().getResource(...)` se ela existir, caindo no placeholder caso contrário.

## 3. Próximas evoluções sugeridas

- Comando bridge `status` para popular MODO LOCAL + MODELO + recursos reais.
- Ação "Analisar Documento" real: abrir seletor de arquivo e enviar pelo chat/ferramentas do backend.
- Alternância de tema já funcional (☀/☾ no topbar) — persistir a preferência.
- Navegabilidade entre as 8 abas já funcional (hero + painel de chat permanente).