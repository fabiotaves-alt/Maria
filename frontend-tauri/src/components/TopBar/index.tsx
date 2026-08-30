import { Sun, Moon, Minus, Square, X } from 'lucide-react';
import { useTheme } from '../../hooks/useTheme';
import mariaLogo from '../../assets/maria-logo.png';
import { Window } from '@tauri-apps/api/window';

export function TopBar() {
  const { theme, toggleTheme } = useTheme();

  const handleMinimize = async () => {
    try {
      const appWindow = await Window.getCurrent();
      await appWindow.minimize();
    } catch (error) {
      console.error('Falha ao minimizar a janela:', error);
    }
  };

  const handleMaximize = async () => {
    try {
      const appWindow = await Window.getCurrent();
      await appWindow.toggleMaximize();
    } catch (error) {
      console.error('Falha ao maximizar a janela:', error);
    }
  };

  const handleClose = async () => {
    try {
      const appWindow = await Window.getCurrent();
      await appWindow.close();
    } catch (error) {
      console.error('Falha ao fechar a janela:', error);
    }
  };
  
  return (
    <header 
      className="h-12 flex items-center justify-between px-4 border-b"
      style={{
        borderColor: 'var(--maria-card-border)',
        background: 'var(--maria-card)',
      }}
      data-tauri-drag-region
    >
      {/* Logo */}
      <div className="flex items-center gap-3">
        <img 
          src={mariaLogo} 
          alt="MARIA" 
          className="h-8 w-auto"
          style={{ 
            filter: theme === 'light' ? 'brightness(0)' : 'brightness(2)',
          }}
        />
      </div>

      {/* Badge MODO LOCAL */}
      <div className="flex items-center gap-2 px-4 py-1.5 rounded-full" style={{ background: 'var(--maria-hover)' }}>
        <div className="w-2 h-2 rounded-full bg-green-400 animate-dot-pulse" />
        <span className="text-xs font-semibold" style={{ color: 'var(--maria-text)' }}>MODO LOCAL</span>
      </div>

      {/* Controles */}
      <div className="flex items-center gap-2">
        <button
          onClick={toggleTheme}
          className="p-2 rounded-full hover:opacity-80 transition-opacity"
          style={{ color: 'var(--maria-pink)' }}
        >
          {theme === 'light' ? <Moon size={18} /> : <Sun size={18} />}
        </button>
        <button 
          onClick={handleMinimize}
          className="p-2 rounded-full hover:opacity-80 transition-opacity" 
          style={{ color: 'var(--maria-pink)' }}
        >
          <Minus size={18} />
        </button>
        <button 
          onClick={handleMaximize}
          className="p-2 rounded-full hover:opacity-80 transition-opacity" 
          style={{ color: 'var(--maria-pink)' }}
        >
          <Square size={18} />
        </button>
        <button 
          onClick={handleClose}
          className="p-2 rounded-full hover:bg-red-500 hover:text-white transition-all" 
          style={{ color: 'var(--maria-pink)' }}
        >
          <X size={18} />
        </button>
      </div>
    </header>
  );
}
