import { useState, useEffect, useRef } from 'react';
import { ChevronDown, MoreHorizontal } from 'lucide-react';
import { motion } from 'framer-motion';
import type { Message } from '../../types';
import { MessageBubble } from './MessageBubble';
import { ChatInput } from './ChatInput';
import { sendMessage, getChatHistory, getSystemStatus } from '../../hooks/useMariaBridge';

const INITIAL_MESSAGES: Message[] = [
  {
    id: '1',
    role: 'assistant',
    content: 'Olá! Sou a MARIA, sua assistente de IA pessoal. Como posso ajudar você hoje?',
    timestamp: new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }),
  },
];

export function ChatPanel() {
  const [messages, setMessages] = useState<Message[]>(INITIAL_MESSAGES);
  const [loading, setLoading] = useState(false);
  const [backendOnline, setBackendOnline] = useState(false);
  const [modeloAtivo, setModeloAtivo] = useState<'qwen3b' | 'llama7b'>('qwen3b');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Carrega histórico inicial e detecta status do backend
  useEffect(() => {
    const initializeChat = async () => {
      try {
        // Tenta carregar histórico do banco
        const history = await getChatHistory(1);
        if (history && history.length > 0) {
          setMessages(history.map(msg => ({
            ...msg,
            id: msg.id.toString(),
          })));
        }
        
        // Verifica se backend está online
        const status = await getSystemStatus();
        setBackendOnline(true);
        setModeloAtivo(status.modelo.includes('7B') || status.modelo.includes('8B') ? 'llama7b' : 'qwen3b');
      } catch (error) {
        console.warn('Backend offline ou sem histórico:', error);
        setBackendOnline(false);
      }
    };

    initializeChat();
  }, []);

  const handleSendMessage = async (content: string) => {
    const newMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content,
      timestamp: new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages(prev => [...prev, newMessage]);
    setLoading(true);

    try {
      // Chama o backend real através da ponte Rust
      const response = await sendMessage(content);
      
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.resposta,
        timestamp: new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }),
      };
      
      setMessages(prev => [...prev, assistantMessage]);
      setBackendOnline(true);
      
      // Atualiza modelo ativo baseado na resposta
      if (response.modelo_usado === 'llama7b') {
        setModeloAtivo('llama7b');
      }
    } catch (error) {
      // Fallback para resposta mockada em caso de erro
      console.warn('Backend offline, usando resposta mockada:', error);
      setBackendOnline(false);
      
      setTimeout(() => {
        const fallbackResponse: Message = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: `Entendi! Vou processar sua solicitação: "${content}"\n\nComo todos os dados são processados localmente, suas informações permanecem seguras e privadas.\n\nO que mais posso fazer por você?`,
          timestamp: new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }),
        };
        setMessages(prev => [...prev, fallbackResponse]);
      }, 1000);
    } finally {
      setLoading(false);
    }
  };

  return (
    <aside className="w-[380px] flex flex-col h-full border-l" style={{ borderColor: 'var(--maria-card-border)' }}>
      {/* Header */}
      <header className="p-4 border-b flex items-center justify-between" style={{ borderColor: 'var(--maria-card-border)' }}>
        <div className="flex items-center gap-2">
          <span className="text-xs font-bold tracking-[0.08em] uppercase" style={{ color: 'var(--maria-muted)' }}>
            CONVERSA ATUAL
          </span>
          <ChevronDown size={16} style={{ color: 'var(--maria-muted)' }} />
        </div>
        <button 
          className="p-2 rounded-lg hover:opacity-80 transition-opacity"
          style={{ color: 'var(--maria-muted)' }}
        >
          <MoreHorizontal size={18} />
        </button>
      </header>

      {/* Área de mensagens */}
      <div className="flex-1 overflow-y-auto p-4">
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}
        
        {loading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex justify-start mb-4"
          >
            <div
              className="px-4 py-3 glass"
              style={{ borderRadius: '16px 16px 16px 4px' }}
            >
              <div className="flex gap-2">
                <motion.div
                  className="w-2 h-2 rounded-full"
                  style={{ backgroundColor: 'var(--maria-pink)' }}
                  animate={{ scale: [1, 1.2, 1] }}
                  transition={{ duration: 0.6, repeat: Infinity, delay: 0 }}
                />
                <motion.div
                  className="w-2 h-2 rounded-full"
                  style={{ backgroundColor: 'var(--maria-pink)' }}
                  animate={{ scale: [1, 1.2, 1] }}
                  transition={{ duration: 0.6, repeat: Infinity, delay: 0.15 }}
                />
                <motion.div
                  className="w-2 h-2 rounded-full"
                  style={{ backgroundColor: 'var(--maria-pink)' }}
                  animate={{ scale: [1, 1.2, 1] }}
                  transition={{ duration: 0.6, repeat: Infinity, delay: 0.3 }}
                />
              </div>
            </div>
          </motion.div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input area */}
      <div className="p-4 border-t" style={{ borderColor: 'var(--maria-card-border)' }}>
        <ChatInput onSend={handleSendMessage} loading={loading} />
        
        <div className="flex items-center justify-center gap-2 mt-3">
          <span 
            className="w-2 h-2 rounded-full"
            style={{ 
              backgroundColor: backendOnline ? '#4ade80' : '#ef4444',
              boxShadow: backendOnline ? '0 0 8px rgba(74, 222, 128, 0.5)' : 'none'
            }}
          />
          <p className="text-xs text-center" style={{ color: 'var(--maria-muted)' }}>
            {backendOnline ? 'MARIA online • ' : 'MARIA offline • '}
            Processamento {backendOnline ? (modeloAtivo === 'llama7b' ? 'Llama 7B' : 'Qwen 3B') : 'local'}
          </p>
        </div>
      </div>
    </aside>
  );
}
