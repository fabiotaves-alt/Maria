# 🚀 Plano de Ação Imediato — Próximos 7 Dias

## Objetivo da Semana

Criar um **protótipo funcional Tauri + React** que demonstre:
1. UI moderna replicando o conceito (aura rosa, glassmorphism)
2. Comunicação funcional com backend Python existente
3. Aba "Conversar" operacional (enviar mensagem → receber resposta)

**Entregável:** Vídeo de 2 minutos mostrando o protótipo rodando + código no GitHub.

---

## 📅 Dia 1: Setup do Ambiente Tauri

### Manhã (9h-12h)

**Tarefa 1.1:** Instalar dependências do sistema

```bash
# Windows (PowerShell como Admin)
winget install Microsoft.VisualStudio.2022.Community
winget install Rustlang.Rustup
winget install NodeJS.NodeJS LTS

# Linux (Ubuntu/Debian)
sudo apt update
sudo apt install -y build-essential curl wget libssl-dev pkg-config \
    libgtk-3-dev libwebkit2gtk-4.0-dev libappindicator3-dev librsvg2-dev
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

**Tarefa 1.2:** Criar projeto Tauri

```bash
cd /workspace
npm create tauri-app@latest frontend-tauri -- --template react-ts
cd frontend-tauri
npm install
```

**Tarefa 1.3:** Instalar dependências adicionais

```bash
npm install @tauri-apps/api@next
npm install axios zustand lucide-react framer-motion
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

### Tarde (14h-18h)

**Tarefa 1.4:** Configurar Tailwind CSS

Editar `frontend-tauri/tailwind.config.js`:

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        'maria-pink': '#ff6b9d',
        'maria-dark': '#1a1a2e',
        'maria-darker': '#0f0f1a',
        'maria-glass': 'rgba(255, 255, 255, 0.08)',
        'maria-glass-hover': 'rgba(255, 255, 255, 0.12)',
      },
      boxShadow: {
        'aura-pink': '0 0 30px rgba(255, 107, 157, 0.4)',
        'aura-pink-strong': '0 0 50px rgba(255, 107, 157, 0.6)',
      },
      backdropBlur: {
        'xs': '2px',
      },
    },
  },
  plugins: [],
};
```

**Tarefa 1.5:** Criar estilos globais

Editar `frontend-tauri/src/styles/globals.css`:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

body {
  @apply bg-maria-dark text-white;
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
}

.glass-panel {
  @apply bg-maria-glass backdrop-blur-md border border-white/10 rounded-xl;
}

.glass-button {
  @apply bg-maria-glass hover:bg-maria-glass-hover 
         border border-white/10 rounded-lg
         transition-all duration-200;
}

.aura-animation {
  animation: pulse-aura 3s ease-in-out infinite;
}

@keyframes pulse-aura {
  0%, 100% {
    box-shadow: 0 0 20px rgba(255, 107, 157, 0.3);
  }
  50% {
    box-shadow: 0 0 40px rgba(255, 107, 157, 0.5);
  }
}
```

**Critério de Aceite do Dia 1:**
- [ ] `npm run tauri dev` abre janela com "Hello Tauri"
- [ ] Tailwind CSS funcionando (testar com `<div className="bg-maria-pink">`)

---

## 📅 Dia 2: Backend HTTP no Python

### Manhã (9h-12h)

**Tarefa 2.1:** Adicionar Flask ao backend Python

Editar `/workspace/backend/main.py` — adicionar imports no topo:

```python
# Adicionar após os imports existentes
from flask import Flask, request, jsonify
from flask_cors import CORS
import threading
```

**Tarefa 2.2:** Criar servidor HTTP embutido

Adicionar ao final de `main.py` (antes do `if __name__ == "__main__"`):

```python
# ═════════════════════════════════════════════════════════════
# Modo bridge HTTP (integração Tauri ↔ Python)
# ═════════════════════════════════════════════════════════════

app_flask = Flask(__name__)
CORS(app_flask)  # Permitir requisições do frontend Tauri

@app_flask.route('/chat', methods=['POST'])
def chat_http():
    """Endpoint HTTP para chat."""
    try:
        data = request.json
        mensagem = data.get('mensagem', '')
        
        if not mensagem:
            return jsonify({
                "id": "http",
                "status": "erro",
                "mensagemErro": "Mensagem vazia"
            }), 400
        
        # Reutilizar lógica do modo bridge stdin/stdout
        controller = MariaController(modelo=args.modelo if 'args' in locals() else None)
        controller.inicializar()
        
        stream = controller.enviar_mensagem(mensagem)
        texto_final = ""
        for chunk, tool_chunk in stream:
            if chunk is not None:
                texto_final += chunk
            controller.processar_chunk(chunk, tool_chunk)
        
        controller.finalizar_mensagem()
        controller.finalizar()
        
        return jsonify({
            "id": "http",
            "status": "ok",
            "dados": texto_final
        })
        
    except Exception as e:
        logger.error(f"Erro no endpoint HTTP /chat: {e}")
        return jsonify({
            "id": "http",
            "status": "erro",
            "mensagemErro": str(e)
        }), 500

@app_flask.route('/status', methods=['GET'])
def status_http():
    """Endpoint HTTP para status do sistema."""
    return jsonify(_get_system_status())

@app_flask.route('/ping', methods=['GET'])
def ping_http():
    """Health check."""
    return jsonify({"status": "ok", "dados": "pong"})

def rodar_servidor_http(porta=8081):
    """Inicia servidor Flask em thread separada."""
    def run():
        app_flask.run(host='127.0.0.1', port=porta, debug=False, use_reloader=False)
    
    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    logger.info(f"Servidor HTTP iniciado em http://127.0.0.1:{porta}")
```

**Tarefa 2.3:** Modificar ponto de entrada

Editar a função `main()` em `main.py`:

```python
def main():
    parser = argparse.ArgumentParser(description="MARIA - Assistente de IA de Escritório")
    parser.add_argument(
        "-m", "--modelo",
        dest="modelo",
        default=None,
        help="Nome do modelo Ollama a usar nesta execução"
    )
    parser.add_argument(
        "--bridge",
        action="store_true",
        help="Executa em modo bridge (JSON por linha no stdin/stdout)"
    )
    parser.add_argument(
        "--bridge-http",
        action="store_true",
        help="Executa em modo bridge HTTP (REST API na porta 8081)"
    )
    args = parser.parse_args()

    # Verificar dependências
    try:
        import requests  # noqa: F401
        import flask  # noqa: F401
        import flask_cors  # noqa: F401
    except ImportError as e:
        print(f"\n[ERRO] Biblioteca faltando: {e}")
        print("Instale com: pip install flask flask-cors\n")
        sys.exit(1)

    # Modo bridge HTTP (frontend Tauri)
    if args.bridge_http:
        rodar_servidor_http(porta=8081)
        # Manter processo vivo
        import time
        while True:
            time.sleep(1)
        return

    # Modo bridge stdin/stdout (frontend JavaFX - legado)
    if args.bridge:
        _modo_bridge(modelo=args.modelo)
        return

    # Modo terminal (padrão)
    controller = MariaController(modelo=args.modelo)
    interface = InterfaceTerminal(controller, imagem_banner="maria_opening.png")
    interface.iniciar()
```

### Tarde (14h-18h)

**Tarefa 2.4:** Atualizar requirements.txt

Adicionar ao `/workspace/requirements.txt`:

```txt
flask>=3.0.0
flask-cors>=4.0.0
```

**Tarefa 2.5:** Testar endpoints manualmente

```bash
# No diretório raiz do workspace
cd backend

# Iniciar servidor HTTP
python main.py --bridge-http

# Em outro terminal, testar ping
curl http://localhost:8081/ping

# Testar status
curl http://localhost:8081/status

# Testar chat (se Ollama estiver rodando)
curl -X POST http://localhost:8081/chat \
  -H "Content-Type: application/json" \
  -d '{"mensagem": "Olá, MARIA!"}'
```

**Critério de Aceite do Dia 2:**
- [ ] `python main.py --bridge-http` inicia sem erros
- [ ] `curl localhost:8081/ping` retorna `{"status": "ok", "dados": "pong"}`
- [ ] `curl localhost:8081/chat` retorna resposta do LLM

---

## 📅 Dia 3: Componentes React Básicos

### Manhã (9h-12h)

**Tarefa 3.1:** Criar estrutura de páginas

```bash
cd /workspace/frontend-tauri
mkdir -p src/pages src/components src/hooks src/stores
```

**Tarefa 3.2:** Criar hook `useChat`

Criar `src/hooks/useChat.ts`:

```typescript
import { useState } from 'react';

interface Mensagem {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

interface UseChatReturn {
  mensagens: Mensagem[];
  carregando: boolean;
  erro: string | null;
  enviarMensagem: (texto: string) => Promise<void>;
  limparConversa: () => void;
}

export function useChat(): UseChatReturn {
  const [mensagens, setMensagens] = useState<Mensagem[]>([]);
  const [carregando, setCarregando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  const enviarMensagem = async (texto: string) => {
    setCarregando(true);
    setErro(null);
    setMensagens(prev => [...prev, { role: 'user', content: texto }]);

    try {
      const response = await fetch('http://localhost:8081/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mensagem: texto }),
      });

      const data = await response.json();

      if (data.status === 'ok') {
        setMensagens(prev => [...prev, { role: 'assistant', content: data.dados }]);
      } else {
        throw new Error(data.mensagemErro || 'Erro desconhecido');
      }
    } catch (error) {
      const mensagemErro = error instanceof Error ? error.message : 'Erro ao enviar mensagem';
      setErro(mensagemErro);
      setMensagens(prev => [...prev, { role: 'system', content: `Erro: ${mensagemErro}` }]);
    } finally {
      setCarregando(false);
    }
  };

  const limparConversa = () => {
    setMensagens([]);
    setErro(null);
  };

  return { mensagens, carregando, erro, enviarMensagem, limparConversa };
}
```

### Tarde (14h-18h)

**Tarefa 3.3:** Criar componente Sidebar

Criar `src/components/Sidebar.tsx`:

```typescript
import { MessageSquare, FolderOpen, Brain, Settings, Mic, FileText, BarChart3, Eye } from 'lucide-react';

interface SidebarProps {
  abaAtiva: string;
  setAbaAtiva: (aba: string) => void;
}

const menuItems = [
  { id: 'conversar', icon: MessageSquare, label: 'Conversar' },
  { id: 'arquivos', icon: FolderOpen, label: 'Arquivos' },
  { id: 'memoria', icon: Brain, label: 'Memória' },
  { id: 'analise', icon: BarChart3, label: 'Análise Dados' },
  { id: 'voz', icon: Mic, label: 'Comando de Voz' },
  { id: 'visao', icon: Eye, label: 'Visão Computacional' },
  { id: 'automacao', icon: FileText, label: 'Automações' },
  { id: 'config', icon: Settings, label: 'Configurações' },
];

export function Sidebar({ abaAtiva, setAbaAtiva }: SidebarProps) {
  return (
    <aside className="w-64 bg-maria-darker border-r border-white/10 flex flex-col">
      {/* Logo */}
      <div className="p-6 border-b border-white/10">
        <h1 className="text-2xl font-bold bg-gradient-to-r from-maria-pink to-purple-400 bg-clip-text text-transparent">
          MARIA
        </h1>
        <p className="text-xs text-gray-400 mt-1">Assistente de IA Local</p>
      </div>

      {/* Menu */}
      <nav className="flex-1 p-4 space-y-2">
        {menuItems.map((item) => {
          const Icon = item.icon;
          const ativo = abaAtiva === item.id;
          
          return (
            <button
              key={item.id}
              onClick={() => setAbaAtiva(item.id)}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${
                ativo
                  ? 'bg-maria-pink text-white shadow-aura-pink'
                  : 'text-gray-400 hover:text-white hover:bg-maria-glass'
              }`}
            >
              <Icon size={20} />
              <span className="font-medium">{item.label}</span>
            </button>
          );
        })}
      </nav>

      {/* Status */}
      <div className="p-4 border-t border-white/10">
        <div className="glass-panel p-3">
          <div className="flex items-center gap-2 mb-2">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            <span className="text-xs text-gray-400">Backend Conectado</span>
          </div>
          <p className="text-xs text-gray-500">v4.0.0-alpha</p>
        </div>
      </div>
    </aside>
  );
}
```

**Critério de Aceite do Dia 3:**
- [ ] Hook `useChat` importa sem erros TypeScript
- [ ] Sidebar renderiza com 8 itens de menu
- [ ] Clique nos itens muda estado `abaAtiva`

---

## 📅 Dia 4: Página Conversar Completa

### Manhã (9h-12h)

**Tarefa 4.1:** Criar página Conversar

Criar `src/pages/ConversarPage.tsx`:

```typescript
import { useState, useRef, useEffect } from 'react';
import { Send, Sparkles } from 'lucide-react';
import { useChat } from '../hooks/useChat';

export function ConversarPage() {
  const { mensagens, carregando, enviarMensagem, limparConversa } = useChat();
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [mensagens]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim() || carregando) return;
    
    await enviarMensagem(inputValue);
    setInputValue('');
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <header className="p-6 border-b border-white/10 flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-white">Conversar</h2>
          <p className="text-gray-400 text-sm mt-1">
            Converse com MARIA sobre qualquer assunto
          </p>
        </div>
        <button
          onClick={limparConversa}
          className="glass-button px-4 py-2 text-sm text-gray-400 hover:text-white"
        >
          Limpar Conversa
        </button>
      </header>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {mensagens.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-gray-500">
            <Sparkles size={64} className="mb-4 opacity-50" />
            <p className="text-lg">Comece uma conversa com MARIA</p>
            <p className="text-sm mt-2">
              Pergunte sobre arquivos, planilhas, ou peça ajuda com tarefas
            </p>
          </div>
        )}

        {mensagens.map((msg, index) => (
          <div
            key={index}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                msg.role === 'user'
                  ? 'bg-maria-pink text-white'
                  : msg.role === 'system'
                  ? 'bg-red-500/20 border border-red-500/50 text-red-200'
                  : 'glass-panel text-white'
              }`}
            >
              <p className="whitespace-pre-wrap">{msg.content}</p>
            </div>
          </div>
        ))}

        {carregando && (
          <div className="flex justify-start">
            <div className="glass-panel rounded-2xl px-4 py-3">
              <div className="flex gap-2">
                <div className="w-2 h-2 bg-maria-pink rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-maria-pink rounded-full animate-bounce delay-100"></div>
                <div className="w-2 h-2 bg-maria-pink rounded-full animate-bounce delay-200"></div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="p-6 border-t border-white/10">
        <div className="flex gap-4 max-w-4xl mx-auto">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="Digite sua mensagem..."
            className="flex-1 glass-panel px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-maria-pink"
            disabled={carregando}
          />
          <button
            type="submit"
            disabled={carregando || !inputValue.trim()}
            className="glass-panel px-6 py-3 bg-maria-pink hover:bg-maria-pink/80 disabled:opacity-50 disabled:cursor-not-allowed transition-all aura-animation"
          >
            <Send size={20} />
          </button>
        </div>
      </form>
    </div>
  );
}
```

### Tarde (14h-18h)

**Tarefa 4.2:** Atualizar App.tsx principal

Editar `src/App.tsx`:

```typescript
import { useState } from 'react';
import { Sidebar } from './components/Sidebar';
import { ConversarPage } from './pages/ConversarPage';

function App() {
  const [abaAtiva, setAbaAtiva] = useState('conversar');

  const renderizarAba = () => {
    switch (abaAtiva) {
      case 'conversar':
        return <ConversarPage />;
      default:
        return (
          <div className="flex items-center justify-center h-full text-gray-500">
            <p>Em desenvolvimento: {abaAtiva}</p>
          </div>
        );
    }
  };

  return (
    <div className="flex h-screen bg-gradient-to-br from-maria-dark to-maria-darker">
      <Sidebar abaAtiva={abaAtiva} setAbaAtiva={setAbaAtiva} />
      <main className="flex-1 overflow-hidden">
        {renderizarAba()}
      </main>
    </div>
  );
}

export default App;
```

**Critério de Aceite do Dia 4:**
- [ ] Página Conversar renderiza com header, lista de mensagens e input
- [ ] Enviar mensagem chama backend e mostra resposta
- [ ] Loading state mostra animação de 3 pontos

---

## 📅 Dia 5: Polimento Visual e Animações

### Manhã (9h-12h)

**Tarefa 5.1:** Adicionar avatar estático

Criar `src/components/AvatarMaria.tsx`:

```typescript
import { Sparkles } from 'lucide-react';

interface AvatarMariaProps {
  estado?: 'neutro' | 'pensando' | 'falando';
}

export function AvatarMaria({ estado = 'neutro' }: AvatarMariaProps) {
  return (
    <div className="relative w-32 h-32 mx-auto mb-6">
      {/* Aura externa */}
      <div
        className={`absolute inset-0 rounded-full blur-xl transition-all duration-500 ${
          estado === 'pensando'
            ? 'bg-maria-pink/50 animate-pulse'
            : estado === 'falando'
            ? 'bg-maria-pink/70 animate-pulse-slow'
            : 'bg-maria-pink/30'
        }`}
      ></div>

      {/* Círculo principal */}
      <div className="relative w-full h-full rounded-full bg-gradient-to-br from-maria-pink to-purple-600 flex items-center justify-center shadow-aura-pink">
        <Sparkles size={64} className="text-white/90" />
      </div>

      {/* Indicador de estado */}
      {estado === 'pensando' && (
        <div className="absolute -bottom-2 left-1/2 transform -translate-x-1/2">
          <div className="flex gap-1">
            <div className="w-1.5 h-1.5 bg-white rounded-full animate-bounce"></div>
            <div className="w-1.5 h-1.5 bg-white rounded-full animate-bounce delay-100"></div>
            <div className="w-1.5 h-1.5 bg-white rounded-full animate-bounce delay-200"></div>
          </div>
        </div>
      )}
    </div>
  );
}
```

**Tarefa 5.2:** Adicionar avatar na página Conversar

Editar `ConversarPage.tsx` — adicionar no topo da mensagem vazia:

```typescript
import { AvatarMaria } from '../components/AvatarMaria';

// Dentro do JSX, quando mensagens.length === 0:
<AvatarMaria estado={carregando ? 'pensando' : 'neutro'} />
```

### Tarde (14h-18h)

**Tarefa 5.3:** Testar em múltiplas resoluções

```bash
# No frontend-tauri
npm run tauri dev

# Testar redimensionamento da janela
# Testar em 1280x720, 1920x1080, 2560x1440
```

**Tarefa 5.4:** Gravar vídeo de demonstração

Roteiro do vídeo (2 minutos):

```
0:00-0:15 → Tela inicial do protótipo (sidebar + avatar)
0:15-0:30 → Digitar "Olá, MARIA! Qual seu nome?"
0:30-0:45 → Mostrar resposta da MARIA aparecendo
0:45-1:00 → Demonstrar UI responsiva (redimensionar janela)
1:00-1:20 → Mostrar código no VS Code (estrutura de pastas)
1:20-1:40 → Explicar arquitetura (Tauri + React + Python)
1:40-2:00 → Call to action: "Próximos passos: instalador one-click"
```

**Critério de Aceite do Dia 5:**
- [ ] Avatar renderiza com aura animada
- [ ] UI funciona em 3 resoluções diferentes
- [ ] Vídeo de 2 minutos gravado e editado

---

## 📅 Dia 6: Documentação e README

### Manhã (9h-12h)

**Tarefa 6.1:** Criar README do frontend-tauri

Criar `frontend-tauri/README.md`:

```markdown
# MARIA Frontend — Tauri + React

Frontend moderno da MARIA construído com Tauri v2, React 18 e TypeScript.

## 🚀 Desenvolvimento

### Pré-requisitos

- Node.js 18+
- Rust 1.70+
- Python 3.11+ (backend)

### Instalação

```bash
npm install
```

### Rodar em desenvolvimento

```bash
# Terminal 1: Iniciar backend Python
cd ../backend
python main.py --bridge-http

# Terminal 2: Iniciar frontend Tauri
npm run tauri dev
```

### Build para produção

```bash
npm run tauri build
```

## 🏗️ Arquitetura

```
src/
├── components/     # Componentes reutilizáveis
│   ├── AvatarMaria.tsx
│   └── Sidebar.tsx
├── pages/          # Páginas principais (8 abas)
│   └── ConversarPage.tsx
├── hooks/          # Hooks customizados
│   └── useChat.ts
└── styles/         # Estilos globais
    └── globals.css
```

## 🎨 Design System

- **Cor Primária:** `#ff6b9d` (Maria Pink)
- **Fundo:** Gradiente `#1a1a2e` → `#0f0f1a`
- **Glassmorphism:** `rgba(255, 255, 255, 0.08)` com backdrop-blur
- **Aura:** Box-shadow animado `0 0 30px rgba(255, 107, 157, 0.4)`

## 📦 Dependências Principais

- `@tauri-apps/api` — IPC com Rust
- `react` + `react-dom` — UI framework
- `tailwindcss` — Utilitários CSS
- `zustand` — Estado global (futuro)
- `framer-motion` — Animações (futuro)
```

**Tarefa 6.2:** Atualizar documentação principal

Adicionar seção em `/workspace/README.md`:

```markdown
## 🆕 Frontend Tauri (v4.0 Alpha)

Novo frontend moderno em desenvolvimento:

```bash
cd frontend-tauri
npm run tauri dev
```

Veja mais em [frontend-tauri/README.md](frontend-tauri/README.md)
```

### Tarde (14h-18h)

**Tarefa 6.3:** Preparar repositório GitHub

```bash
cd /workspace

# Inicializar git se não existir
git init

# Adicionar todos os arquivos
git add .

# Commit inicial
git commit -m "feat: protótipo Tauri v4.0 alpha

- Frontend React + TypeScript + Tailwind
- Backend Python com HTTP bridge
- Aba Conversar funcional
- Avatar com aura animada

Responde ao relatório do investidor (risco: UI legada JavaFX)"

# Push para GitHub (se houver remote)
git push origin main
```

**Critério de Aceite do Dia 6:**
- [ ] README completo com instruções de instalação
- [ ] Código versionado no Git
- [ ] Repositório GitHub atualizado

---

## 📅 Dia 7: Validação com Investidor

### Manhã (9h-12h)

**Tarefa 7.1:** Preparar pitch deck atualizado

Slides essenciais (Google Slides / Canva):

```
Slide 1: Capa
- "MARIA v4.0 — Resposta ao Relatório do Investidor"
- Data, equipe

Slide 2: O Que Ouvimos
- "Você identificou 5 riscos críticos"
- Lista: UI legada, stack declining, modelo fraco, etc.

Slide 3: Nossa Resposta
- "Transformamos cada risco em vantagem"
- Matriz Antes vs Depois

Slide 4: Demonstração (embed do vídeo)
- Screenshot do protótipo
- Link para vídeo de 2 minutos

Slide 5: Roadmap de 17 Semanas
- Timeline visual com 5 fases
- Milestones claros

Slide 6: Pedido de Investimento
- R$ 500K para 18 meses
- Tranches condicionais a milestones
- Valuation: R$ 1.5M pré-money

Slide 7: Call to Action
- "Próxima reunião: apresentar benchmark 3B vs 8B em 30 dias"
- Contatos
```

### Tarde (14h-18h)

**Tarefa 7.2:** Enviar para investidor

Email template:

```
Assunto: MARIA v4.0 — Protótipo Tauri Pronto para Review

Olá [Nome do Investidor],

Conforme discutido no relatório de análise de risco, identificamos 5 pontos 
críticos que precisavam de atenção imediata.

Nos últimos 7 dias, construímos um protótipo funcional que responde 
diretamente ao principal risco identificado: o gap entre o conceito visual 
e a implementação JavaFX atual.

🎯 Entregáveis desta semana:

1. Protótipo Tauri + React funcional (vídeo em anexo, 2 min)
2. Backend Python com HTTP bridge (código no GitHub)
3. Roadmap detalhado de 17 semanas (documento em anexo)
4. Análise de viabilidade técnica completa (documento em anexo)

📊 Resultado:

- Risco "UI de 2010": ELIMINADO
- Risco "Stack legada": EM MITIGAÇÃO (migração em andamento)
- Nota estimada pós-migração: 8.5/10 (vs 6.5 atual)

🚀 Próximos passos (30 dias):

1. Implementar roteamento de modelos 3B ↔ 8B
2. Benchmark comparativo com 20 tarefas reais
3. Instalador MSI one-click alpha

Gostaria de agendar uma call de 30 minutos na próxima semana para:
- Demonstrar o protótipo ao vivo
- Discutir termos de investimento atualizados
- Alinhar expectativas para os próximos milestones

Qual horário funciona melhor para você?

Abraços,
[Seu Nome]
Desenvolvedor Principal — MARIA
```

**Critério de Aceite do Dia 7:**
- [ ] Pitch deck enviado
- [ ] Reunião agendada com investidor
- [ ] Feedback coletado e documentado

---

## ✅ Checklist Final da Semana

| Dia | Tarefa Principal | Status |
|-----|------------------|--------|
| 1 | Setup Tauri + Tailwind | ⬜ |
| 2 | Backend HTTP Python | ⬜ |
| 3 | Hook useChat + Sidebar | ⬜ |
| 4 | Página Conversar completa | ⬜ |
| 5 | Avatar + animações + vídeo | ⬜ |
| 6 | README + Git + docs | ⬜ |
| 7 | Pitch deck + envio investidor | ⬜ |

**Meta da Semana:** Ter código rodando, vídeo gravado e reunião agendada.

---

## 🎯 Métricas de Sucesso

**Técnicas:**
- [ ] `npm run tauri dev` abre sem erros
- [ ] Chat envia/recebe mensagens em <3s
- [ ] UI responsiva em 3 resoluções

**Comerciais:**
- [ ] Investidor assiste vídeo de demo
- [ ] Reunião de follow-up agendada
- [ ] Interesse em continuar negociação expresso

**Pessoais:**
- [ ] Equipe motivada com progresso visível
- [ ] Confiança renovada após crítica construtiva
- [ ] Clareza sobre próximos passos

---

**Documento criado:** 2026-08-28  
**Autor:** Equipe de Desenvolvimento MARIA  
**Versão:** 1.0 (Plano de Ação Semanal)
