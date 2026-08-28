import { Sun, Moon, Minus, Square, X } from 'lucide-react';
import { motion } from 'framer-motion';
import { useTheme } from '../hooks/useTheme';

export function TopBar() {
  const { theme, toggleTheme } = useTheme();

  return (
    <header className="h-12 flex items-center justify-between px-4 border-b" style={{ 
      borderColor: 'var(--maria-card-border)',
      background: 'var(--maria-card)'
    }}>
      {/* Logo */}
      <div className="flex items-center gap-3">
        <span className="text-xl font-light tracking-[0.15em]" style={{ color: 'var(--maria-text)' }}>
          MARIA
        </span>
        <div className="w-2 h-2 rounded-full" style={{ backgroundColor: 'var(--maria-pink)' }} />
      </div>

      {/* Badge Modo Local */}
      <div className="flex items-center gap-2 px-4 py-1.5 rounded-full" style={{ 
        background: 'rgba(255,255,255,0.1)',
        backdropFilter: 'blur(10px)'
      }}>
        <div className="w-2 h-2 rounded-full bg-green-400 animate-dot-pulse" />
        <span className="text-xs font-semibold tracking-wide" style={{ color: 'var(--maria-pink)' }}>
          MODO LOCAL
        </span>
      </div>

      {/* Controles */}
      <div className="flex items-center gap-2">
        <button
          onClick={toggleTheme}
          className="p-2 rounded-lg hover:opacity-80 transition-opacity"
          style={{ color: 'var(--maria-muted)' }}
        >
          {theme === 'light' ? <Moon size={18} /> : <Sun size={18} />}
        </button>
        
        {/* Controles da janela Tauri */}
        <div className="flex items-center gap-1 ml-4">
          <button className="p-2 hover:bg-gray-200 dark:hover:bg-white/10 rounded transition-colors">
            <Minus size={18} style={{ color: 'var(--maria-muted)' }} />
          </button>
          <button className="p-2 hover:bg-gray-200 dark:hover:bg-white/10 rounded transition-colors">
            <Square size={16} style={{ color: 'var(--maria-muted)' }} />
          </button>
          <button className="p-2 hover:bg-red-500 hover:text-white rounded transition-colors">
            <X size={18} style={{ color: 'var(--maria-muted)' }} />
          </button>
        </div>
      </div>
    </header>
  );
}
