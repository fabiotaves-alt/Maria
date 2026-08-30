import { motion } from 'framer-motion';
import type { Message } from '../../types';
import mariaAvatar from '../../assets/maria-avatar.png';

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
      {!isUser && (
        <img 
          src={mariaAvatar} 
          alt="MARIA" 
          className="w-8 h-8 rounded-full object-cover mr-2 self-end mb-1 border border-pink-500/20"
        />
      )}
      <div
        className={`px-4 py-3 max-w-[80%] ${
          isUser 
            ? 'bg-pink-500 text-white rounded-2xl rounded-br-none ml-auto' 
            : 'bg-white/10 backdrop-blur-md text-white rounded-2xl rounded-bl-none mr-auto'
        }`}
      >
        {/* Conteúdo da mensagem */}
        <div
          className="text-sm whitespace-pre-wrap"
        >
          {message.content}
        </div>

        {/* Timestamp */}
        <div
          className="text-[10px] mt-2 text-right opacity-70"
        >
          {message.timestamp}
        </div>
      </div>
    </motion.div>
  );
}
