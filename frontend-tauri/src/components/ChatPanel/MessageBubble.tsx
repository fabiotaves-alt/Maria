import { motion } from 'framer-motion';
import type { Message } from '../../types';

interface MessageBubbleProps {
  message: Message;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user';

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}
    >
      <div
        className="glass px-4 py-3 max-w-[85%]"
        style={{
          borderRadius: isUser ? '16px 16px 4px 16px' : '16px 16px 16px 4px',
          background: isUser ? 'rgba(232, 90, 138, 0.15)' : 'var(--maria-card)',
        }}
      >
        {/* Conteúdo da mensagem */}
        <div
          className="text-sm whitespace-pre-wrap"
          style={{ color: isUser ? 'var(--maria-text)' : 'var(--maria-text)' }}
        >
          {message.content}
        </div>

        {/* Timestamp */}
        <div
          className="text-[10px] mt-2 text-right"
          style={{ color: 'var(--maria-muted)' }}
        >
          {message.timestamp}
        </div>
      </div>
    </motion.div>
  );
}
