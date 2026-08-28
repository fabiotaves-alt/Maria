import { useState, useRef, useEffect } from 'react';
import { ChevronDown, MoreHorizontal } from 'lucide-react';
import { motion } from 'framer-motion';
import type { Message } from '../../types';
import { MessageBubble } from './MessageBubble';
import { ChatInput } from './ChatInput';

const mockMessages: Message[] = [
  {
    id: '1',
    role: 'assistant',
    content: 'Olá! Sou a MARIA, sua assistente de IA pessoal. Como posso ajudar você hoje?',
    timestamp: '10:30',
  },
  {
    id: '2',
    role: 'user',
    content: 'Preciso analisar alguns documentos financeiros.',
    timestamp: '10:32',
  },
  {
    id: '3',
    role: 'assistant',
    content: 'Claro! Posso ajudar você com isso. Por favor, envie os documentos que deseja analisar.\n\nPosso:\n• Extrair informações de PDFs e imagens\n• Analisar planilhas e dados estruturados\n• Gerar resumos e insights\n• Identificar padrões e tendências\n\nComo prefere proceder?',
    timestamp: '10:32',
  },
];

export function ChatPanel() {
  const [messages, setMessages] = useState<Message[]>(mockMessages);
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async (content: string) => {
    const newMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content,
      timestamp: new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages(prev => [...prev, newMessage]);
    setLoading(true);

    // Simulação de resposta - será substituído pela integração real
    setTimeout(() => {
      const response: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Entendi! Vou processar sua solicitação. Como todos os dados são processados localmente, suas informações permanecem seguras e privadas.\n\nO que mais posso fazer por você?',
        timestamp: new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages(prev => [...prev, response]);
      setLoading(false);
    }, 1500);
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
        
        <p className="text-xs text-center mt-3" style={{ color: 'var(--maria-muted)' }}>
          MARIA processa tudo localmente • Seus dados nunca saem do seu computador
        </p>
      </div>
    </aside>
  );
}
