import { useState, useEffect, useRef } from 'react';
import { ChevronDown, MoreHorizontal } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import type { Message } from '../../types';
import type { ConfirmacaoPendente, ChatResponse } from '../../hooks/useMariaBridge';
import { MessageBubble } from './MessageBubble';
import { ChatInput } from './ChatInput';
import { ActionCard } from './ActionCard';
import { sendMessage, getChatHistory, getSystemStatus } from '../../hooks/useMariaBridge';

const INITIAL_MESSAGES: Message[] = [
  {
    id: '1',
    role: 'assistant',
    content: 'Olá! Sou a MARIA, sua assistente de IA pessoal. Como posso ajudar você hoje?',
    timestamp: new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }),
  },
];

const SUGESTOES: string[] = [
  'Criar uma planilha de gastos',
  'Analisar um arquivo',
  'Resumir um documento',
];

interface EstadoConfirmacao {
  pendente: ConfirmacaoPendente;
  mensagem: string;
}

function novoTimestamp(): string {
  return new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
}

export function ChatPanel() {
  const [messages, setMessages] = useState<Message[]>(INITIAL_MESSAGES);
  const [loading, setLoading] = useState(false);
  const [backendOnline, setBackendOnline] = useState(false);
  const [modeloAtivo, setModeloAtivo] = useState('qwen2.5-omni-3b');
  const [confirmacao, setConfirmacao] = useState<EstadoConfirmacao | null>(null);
  const [tempoDecorrido, setTempoDecorrido] = useState(0);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const tempoDecorridoRef = useRef(0);
  const reqIdRef = useRef(0);
  const abortRef = useRef<(() => void) | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => { scrollToBottom(); }, [messages, confirmacao]);

  useEffect(() => {
    (async () => {
      try {
        const history = await getChatHistory(1);
        if (history.length > 0) {
          setMessages(history.map((m: any) => ({ ...m, id: String(m.id) })));
        }
        const status = await getSystemStatus();
        setBackendOnline(status.online !== false);
        setModeloAtivo(status.modelo);
      } catch {
        setBackendOnline(false);
      }
    })();
  }, []);

  // Cronômetro de progresso: incrementa a cada segundo enquanto loading.
  // Atualiza estado (display) e ref (leitura no catch sem stale closure).
  useEffect(() => {
    if (!loading) {
      setTempoDecorrido(0);
      tempoDecorridoRef.current = 0;
      return;
    }
    const intervalo = setInterval(() => {
      setTempoDecorrido(t => t + 1);
      tempoDecorridoRef.current += 1;
    }, 1000);
    return () => clearInterval(intervalo);
  }, [loading]);

  const appendMessage = (role: 'user' | 'assistant', content: string) => {
    setMessages(prev => [...prev, {
      id: String(Date.now()),
      role,
      content,
      timestamp: novoTimestamp(),
    }]);
  };

  const processarResposta = (resp: ChatResponse) => {
    if (resp.confirmacao_pendente) {
      // Modelo narrou + solicitou ação: exibe mensagem e abre ActionCard
      appendMessage('assistant', resp.resposta);
      setConfirmacao({ pendente: resp.confirmacao_pendente, mensagem: resp.resposta });
    } else {
      // Resposta textual simples ou resultado de ação já executada
      setConfirmacao(null);
      appendMessage('assistant', resp.resposta);
    }
  };

  const handleSendMessage = async (content: string) => {
    if (loading) return;                        // evitar duplo envio
    const meuId = ++reqIdRef.current;           // id único do pedido (guarda anti-race)
    appendMessage('user', content);
    setLoading(true);

    let foiCancelado = false;
    abortRef.current = () => { foiCancelado = true; };

    try {
      const resp = await sendMessage(content);
      if (foiCancelado || meuId !== reqIdRef.current) return;
      setBackendOnline(true);
      processarResposta(resp);
    } catch {
      if (foiCancelado || meuId !== reqIdRef.current) return;
      setBackendOnline(false);
      setConfirmacao(null);
      const msg = tempoDecorridoRef.current >= 290
        ? 'O servidor demorou demasiado a responder (timeout de 300s). Tente novamente.'
        : 'Não consegui me conectar ao backend. Verifique se o servidor está rodando.';
      appendMessage('assistant', msg);
    } finally {
      if (meuId === reqIdRef.current) {
        abortRef.current = null;
        setLoading(false);
      }
    }
  };

  // Cancelamento best-effort: interrompe a espera na UI.
  // Não cancela a geração no llama-server (limitação conhecida).
  const handleCancelarEnvio = () => {
    if (abortRef.current) {
      abortRef.current();
      abortRef.current = null;
    }
    setLoading(false);
    setConfirmacao(null);
    appendMessage('assistant', 'Geração interrompida.');
  };

  const handleConfirmar = () => {
    setConfirmacao(null);
    handleSendMessage('sim');
  };

  const handleCancelar = () => {
    setConfirmacao(null);
    handleSendMessage('não');
  };

  return (
    <aside className="w-[380px] flex flex-col h-full border-l"
           style={{ borderColor: 'var(--maria-card-border)' }}>

      {/* Header */}
      <header className="p-4 border-b flex items-center justify-between"
              style={{ borderColor: 'var(--maria-card-border)' }}>
        <div className="flex items-center gap-2">
          <span className="text-xs font-bold tracking-[0.08em] uppercase"
                style={{ color: 'var(--maria-muted)' }}>
            CONVERSA ATUAL
          </span>
          <ChevronDown size={16} style={{ color: 'var(--maria-muted)' }} />
        </div>
        <button className="p-2 rounded-lg hover:opacity-80 transition-opacity"
                style={{ color: 'var(--maria-muted)' }}>
          <MoreHorizontal size={18} />
        </button>
      </header>

      {/* Área de mensagens */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4 pt-6">
        {messages.map(msg => (
          <MessageBubble key={msg.id} message={msg} />
        ))}

        {messages.length <= 1 && !loading && (
          <div className="grid grid-cols-1 gap-2 mt-2">
            {SUGESTOES.map((sugestao) => (
              <button
                key={sugestao}
                onClick={() => handleSendMessage(sugestao)}
                className="text-left px-4 py-3 rounded-xl bg-white/5 hover:bg-white/10 border transition-colors"
                style={{ borderColor: 'var(--maria-card-border)' }}
              >
                <span className="text-sm" style={{ color: 'var(--maria-text)' }}>{sugestao}</span>
              </button>
            ))}
          </div>
        )}

        {loading && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="flex justify-start mb-4"
          >
            <div className="px-4 py-3 bg-white/10 backdrop-blur-md text-white
                            rounded-2xl rounded-bl-none max-w-[80%]">
              <div className="flex items-center gap-3">
                {/* Pontos animados (mantidos) */}
                <div className="flex gap-1">
                  {[0, 0.15, 0.3].map((delay, i) => (
                    <motion.div key={i} className="w-2 h-2 rounded-full"
                                style={{ backgroundColor: 'var(--maria-pink)' }}
                                animate={{ scale: [1, 1.2, 1] }}
                                transition={{ duration: 0.6, repeat: Infinity, delay }} />
                  ))}
                </div>

                {/* Tempo decorrido — aparece após 3s */}
                {tempoDecorrido >= 3 && (
                  <span className="text-xs" style={{ color: 'var(--maria-muted)' }}>
                    {tempoDecorrido}s
                  </span>
                )}

                {/* Aviso "a demorar" — aparece após 15s */}
                {tempoDecorrido >= 15 && (
                  <span className="text-xs" style={{ color: 'var(--maria-muted)' }}>
                    processando localmente…
                  </span>
                )}

                {/* Botão cancelar — aparece após 5s */}
                {tempoDecorrido >= 5 && (
                  <button
                    onClick={handleCancelarEnvio}
                    className="text-xs hover:opacity-100 transition-opacity ml-2"
                    style={{ color: 'var(--maria-muted)' }}
                    title="Cancelar geração"
                  >
                    ✕
                  </button>
                )}
              </div>
            </div>
          </motion.div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* ActionCard — visível entre mensagens e input quando há ação pendente */}
      <AnimatePresence>
        {confirmacao && !loading && (
          <ActionCard
            confirmacao={confirmacao.pendente}
            mensagem={confirmacao.mensagem}
            onConfirmar={handleConfirmar}
            onCancelar={handleCancelar}
            loading={loading}
          />
        )}
      </AnimatePresence>

      {/* Input */}
      <div className="p-4 border-t" style={{ borderColor: 'var(--maria-card-border)' }}>
        <ChatInput onSend={handleSendMessage} loading={loading} />
        <div className="flex items-center justify-center gap-2 mt-3">
          <span className="w-2 h-2 rounded-full" style={{
            backgroundColor: backendOnline ? 'var(--maria-green)' : '#ef4444',
            boxShadow: backendOnline ? '0 0 8px rgba(34,197,94,0.5)' : 'none',
          }} />
          <p className="text-xs text-center" style={{ color: 'var(--maria-muted)' }}>
            {backendOnline
              ? `MARIA online · ${modeloAtivo}`
              : 'MARIA offline · processamento local'}
          </p>
        </div>
      </div>
    </aside>
  );
}
