import { useState } from 'react';
import { 
  MessageCircle, 
  FileText, 
  BarChart3, 
  Camera, 
  Mic, 
  Database, 
  Zap, 
  Settings 
} from 'lucide-react';
import { motion } from 'framer-motion';
import type { NavItem, ResourceMetric } from '../../types';

const navItems: NavItem[] = [
  { id: 'conversar', label: 'Conversar', icon: 'MessageCircle', active: true },
  { id: 'arquivos', label: 'Arquivos', icon: 'FileText' },
  { id: 'analise', label: 'Análise de Dados', icon: 'BarChart3' },
  { id: 'visao', label: 'Visão', icon: 'Camera' },
  { id: 'voz', label: 'Voz', icon: 'Mic' },
  { id: 'memoria', label: 'Memória', icon: 'Database' },
  { id: 'automacoes', label: 'Automações', icon: 'Zap' },
  { id: 'config', label: 'Configurações', icon: 'Settings' },
];

const resources: ResourceMetric[] = [
  { label: 'CPU', value: 18 },
  { label: 'RAM', value: 42 },
  { label: 'GPU', value: 11 },
];

const iconMap: Record<string, React.ComponentType<{ size: number }>> = {
  MessageCircle,
  FileText,
  BarChart3,
  Camera,
  Mic,
  Database,
  Zap,
  Settings,
};

export function Sidebar() {
  const [activeItem, setActiveItem] = useState('conversar');

  return (
    <aside className="w-[260px] flex flex-col h-full border-r" style={{ 
      borderColor: 'var(--maria-card-border)' 
    }}>
      {/* Navegação */}
      <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
        {navItems.map((item) => {
          const Icon = iconMap[item.icon];
          const isActive = item.id === activeItem;
          
          return (
            <motion.button
              key={item.id}
              onClick={() => setActiveItem(item.id)}
              className="w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200"
              style={{
                background: isActive ? 'rgba(232, 90, 138, 0.1)' : 'transparent',
                color: isActive ? 'var(--maria-pink)' : 'var(--maria-text)',
              }}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              <Icon 
                size={20} 
                style={{ color: isActive ? 'var(--maria-pink)' : 'var(--maria-muted)' }} 
              />
              <span className="text-sm font-medium">{item.label}</span>
            </motion.button>
          );
        })}
      </nav>

      {/* Divider */}
      <div className="h-px mx-4 my-2" style={{ backgroundColor: 'var(--maria-card-border)' }} />

      {/* Status */}
      <div className="p-4 mx-4 mb-4 glass" style={{ borderRadius: '12px' }}>
        <div className="flex items-center gap-2 mb-2">
          <div className="w-2 h-2 rounded-full bg-green-400 animate-dot-pulse" />
          <span className="text-[11px] font-bold tracking-wider uppercase" style={{ color: 'var(--maria-pink)' }}>
            FUNCIONANDO LOCALMENTE
          </span>
        </div>
        <p className="text-xs mb-2" style={{ color: 'var(--maria-muted)' }}>
          Seus dados não saem do seu computador.
        </p>
        <a href="#" className="text-xs underline hover:opacity-80" style={{ color: 'var(--maria-pink)' }}>
          Saiba mais
        </a>
      </div>

      {/* Recursos do Sistema */}
      <div className="px-4 pb-4">
        <h3 className="text-[10px] font-bold tracking-[0.1em] uppercase mb-3" style={{ color: 'var(--maria-muted)' }}>
          RECURSOS DO SISTEMA
        </h3>
        
        <div className="space-y-3">
          {resources.map((resource) => (
            <div key={resource.label} className="space-y-1">
              <div className="flex justify-between text-xs">
                <span style={{ color: 'var(--maria-text)' }}>{resource.label}</span>
                <span style={{ color: 'var(--maria-muted)' }}>{resource.value}%</span>
              </div>
              <div className="h-1 rounded-full" style={{ background: 'rgba(0,0,0,0.06)' }}>
                <motion.div
                  className="h-full rounded-full"
                  style={{ backgroundColor: 'var(--maria-pink)' }}
                  initial={{ width: 0 }}
                  animate={{ width: `${resource.value}%` }}
                  transition={{ duration: 0.5, ease: 'easeOut' }}
                />
              </div>
            </div>
          ))}
        </div>

        <div className="mt-4">
          <span className="text-[10px] font-bold tracking-[0.1em] uppercase" style={{ color: 'var(--maria-muted)' }}>
            MODELO
          </span>
          <p className="text-xs mt-1" style={{ color: 'var(--maria-text)' }}>
            Llama 3.1 8B (via Ollama)
          </p>
        </div>
      </div>

      {/* Footer */}
      <div className="p-4 text-center border-t" style={{ borderColor: 'var(--maria-card-border)' }}>
        <span className="text-[11px]" style={{ color: 'var(--maria-muted)' }}>
          MARIA v0.1.0
        </span>
      </div>
    </aside>
  );
}
