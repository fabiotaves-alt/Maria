import { useState } from 'react';
import { Send, Paperclip, Mic } from 'lucide-react';
import { motion } from 'framer-motion';

interface ChatInputProps {
  onSend: (message: string) => void;
  loading?: boolean;
}

export function ChatInput({ onSend, loading }: ChatInputProps) {
  const [message, setMessage] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim() && !loading) {
      onSend(message.trim());
      setMessage('');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="relative">
      <div
        className="glass flex items-center gap-2 p-2"
        style={{ borderRadius: '9999px' }}
      >
        {/* Botão de anexo */}
        <button
          type="button"
          className="p-2 rounded-full hover:opacity-80 transition-opacity"
          style={{ color: 'var(--maria-muted)' }}
        >
          <Paperclip size={18} />
        </button>

        {/* Input de texto */}
        <input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Digite sua mensagem..."
          disabled={loading}
          className="flex-1 bg-transparent border-none outline-none text-sm px-2"
          style={{ 
            color: 'var(--maria-text)',
          }}
        />

        {/* Botão de microfone */}
        <button
          type="button"
          className="p-2 rounded-full hover:opacity-80 transition-opacity"
          style={{ color: 'var(--maria-muted)' }}
        >
          <Mic size={18} />
        </button>

        {/* Botão de enviar */}
        <motion.button
          type="submit"
          disabled={loading || !message.trim()}
          className="w-9 h-9 rounded-full flex items-center justify-center"
          style={{
            backgroundColor: message.trim() ? 'var(--maria-pink)' : 'rgba(255,255,255,0.1)',
            opacity: message.trim() ? 1 : 0.5,
          }}
          whileHover={{ scale: message.trim() ? 1.05 : 1 }}
          whileTap={{ scale: message.trim() ? 0.95 : 1 }}
        >
          <Send size={16} style={{ color: '#fff' }} />
        </motion.button>
      </div>
    </form>
  );
}
