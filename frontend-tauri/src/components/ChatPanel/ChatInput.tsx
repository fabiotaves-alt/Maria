import { useState } from 'react';
import { Send, Mic, Paperclip } from 'lucide-react';
import { motion } from 'framer-motion';

interface ChatInputProps {
  onSend: (message: string) => void;
  loading?: boolean;
}

export function ChatInput({ onSend, loading = false }: ChatInputProps) {
  const [message, setMessage] = useState('');

  const handleSend = () => {
    if (!message.trim() || loading) return;
    onSend(message);
    setMessage('');
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div 
      className="glass p-1 flex items-end gap-1"
      style={{ borderRadius: '24px' }}
    >
      {/* Botão anexar */}
      <button 
        className="p-3 rounded-full hover:opacity-80 transition-opacity"
        style={{ color: 'var(--maria-muted)' }}
        title="Anexar arquivo"
      >
        <Paperclip size={20} />
      </button>

      {/* Input de texto */}
      <textarea
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        onKeyPress={handleKeyPress}
        placeholder="Digite sua mensagem..."
        rows={1}
        className="flex-1 bg-transparent border-none outline-none resize-none py-3 px-2 min-h-[44px] max-h-32 text-sm"
        style={{ color: 'var(--maria-text)' }}
      />

      {/* Botão microfone */}
      <button 
        className="p-3 rounded-full hover:opacity-80 transition-opacity"
        style={{ color: 'var(--maria-muted)' }}
        title="Usar voz"
      >
        <Mic size={20} />
      </button>

      {/* Botão enviar - rosa em ambos os temas com ícone branco */}
      <motion.button
        onClick={handleSend}
        disabled={loading || !message.trim()}
        whileHover={{ scale: loading ? 1 : 1.05 }}
        whileTap={{ scale: loading ? 1 : 0.95 }}
        className="w-9 h-9 rounded-full flex items-center justify-center transition-all duration-200"
        style={{
          background: loading || !message.trim() 
            ? 'var(--maria-muted)' 
            : 'var(--maria-pink)',
          color: 'white',
          opacity: loading || !message.trim() ? 0.5 : 1,
          cursor: loading || !message.trim() ? 'not-allowed' : 'pointer',
        }}
      >
        <Send size={18} />
      </motion.button>
    </div>
  );
}
