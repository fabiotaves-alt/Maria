import { motion } from 'framer-motion';
import type { Message } from '../../types';

interface MessageBubbleProps {
  message: Message;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user';
  const isSystem = message.role === 'system';

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}
    >
      <div
        className="max-w-[85%] px-4 py-3"
        style={{
          borderRadius: isUser 
            ? '16px 16px 4px 16px' 
            : '16px 16px 16px 4px',
          background: isUser 
            ? 'rgba(232, 90, 138, 0.1)' 
            : isSystem 
              ? 'rgba(255, 100, 100, 0.1)'
              : 'var(--maria-card)',
          border: isSystem 
            ? '1px solid rgba(255, 100, 100, 0.2)' 
            : '1px solid var(--maria-card-border)',
          color: 'var(--maria-text)',
        }}
      >
        {!isUser && !isSystem && (
          <div className="flex items-center gap-2 mb-2">
            <div 
              className="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold"
              style={{ 
                background: 'rgba(232, 90, 138, 0.2)',
                color: 'var(--maria-pink)',
              }}
            >
              M
            </div>
            <span className="text-xs font-semibold" style={{ color: 'var(--maria-pink)' }}>
              Maria
            </span>
            <span className="text-xs" style={{ color: 'var(--maria-muted)' }}>
              {message.timestamp}
            </span>
          </div>
        )}
        
        <p className="text-sm leading-relaxed whitespace-pre-wrap">
          {message.content}
        </p>
        
        {isUser && (
          <div className="text-right mt-2">
            <span className="text-xs" style={{ color: 'var(--maria-muted)' }}>
              {message.timestamp}
            </span>
          </div>
        )}
      </div>
    </motion.div>
  );
}
