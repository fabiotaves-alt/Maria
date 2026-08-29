# Pendências de Interface — MARIA (v2.14.0)

**Data:** 2026-08-27
**Escopo:** desmockagem da interface JavaFX — funcionalidades reais integradas ao backend Python.

---

## 1. ✅ Elementos implementados na fase de desmockagem (v2.14.0)

| Elemento | Onde aparece | Situação atual |
|----------|-------------|----------------|
| **Recursos do sistema (CPU/RAM/GPU)** | Sidebar → card "RECURSOS DO SISTEMA" | ✅ **Dados reais** via comando `status` do backend (psutil). Atualização a cada 5 segundos. Barras de progresso e labels dinâmicos. |
| **MODO LOCAL / MODELO** | Topbar (labelModelo) | ✅ **Dinâmico**: Backend retorna modelo real (`qwen3.5:4b`) no comando `status`. Texto atualizado automaticamente. |
| **Ações rápidas (hero)** | Hero central → 4 botões | ✅ **Funcionais**: Preenchem campo de mensagem com prompts contextuais prontos para envio. |
| **Anexar (📎)** | Input do chat | ✅ **Habilitado**: FileChooser abre, arquivo enviado via `upload_arquivo`, confirmação exibida no chat. |
| **Voz (🎤)** | Input do chat | ✅ **Habilitado**: Gravação via `javax.sound.sampled`, envio para `transcrever_audio`, texto transcrito preenchido no campo. |
| **Dropdown "⋯" do chat** | Header do painel de chat | ✅ **Funcional**: Opções "Limpar Conversa" e "Exportar Conversa (.txt)" implementadas. |

---

## 2. ⚠️ Pendências restantes

| Elemento | Onde aparece | Situação atual | Próximo passo |
|----------|-------------|----------------|---------------|
| **Avatar nas bolhas de chat** | Mensagens da Maria | Placeholder "M" mantido | Carregar `avatar.png` dinamicamente se existir, fallback para "M" |
| **Whisper.cpp** | Transcrição de voz | Requer instalação manual do binário | Documentar instalação ou empacotar binário |
| **GPU NVIDIA** | Sidebar (GPU bar) | Exibe 0% se sem pynvml | Opcional: detectar GPU AMD/Intel via outras libs |

---

## 3. Como inserir a foto da Maria (avatar nas bolhas)

O avatar da tela inicial já usa imagem real (`maria-avatar.png`). Para aplicar também nas **bolhas de chat**:

1. Certifique-se que a imagem existe em:
   `frontend/src/main/resources/com/tristar/maria/images/avatar.png`
2. No `ConversarController.java`, modificar o método `adicionarBalaoMaria()`:
   - Substituir `Label avatar = new Label("M");` por um `ImageView` carregando a imagem via `getClass().getResource(...)`
   - Manter fallback para "M" se a imagem não existir

---

## 4. Próximas evoluções sugeridas (pós-v2.14.0)

- Persistir preferência de tema (claro/escuro) entre sessões.
- Empacotar whisper.cpp com o instalador da MARIA.
- Adicionar suporte a mais formatos de áudio (MP3, OGG) via conversão.
- Implementar notificações nativas ao receber resposta longa.
- Histórico de conversas salvas com carregamento via dropdown.
