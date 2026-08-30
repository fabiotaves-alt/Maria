import { FileSearch, TrendingUp, PenLine, AudioWaveform, type LucideIcon } from 'lucide-react';
import { motion } from 'framer-motion';

interface ActionButtonProps {
  icon: LucideIcon;
  label: string;
  onClick?: () => void;
}

function ActionButton({ icon: Icon, label, onClick }: ActionButtonProps) {
  return (
    <motion.button
      onClick={onClick}
      className="bg-white/10 border border-white/20 backdrop-blur-lg rounded-2xl p-4 flex flex-col items-center gap-2 min-w-[100px] cursor-pointer transition-all duration-200 hover:-translate-y-1 hover:bg-pink-500/20"
      whileHover={{
        scale: 1.02,
        boxShadow: '0 8px 30px rgba(232, 90, 138, 0.2)',
      }}
      whileTap={{ scale: 0.98 }}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
    >
      <div
        className="w-12 h-12 rounded-full flex items-center justify-center"
        style={{ background: 'rgba(255,255,255,0.1)' }}
      >
        <Icon size={24} className="text-white" />
      </div>
      <span className="text-xs font-medium text-center text-white">
        {label}
      </span>
    </motion.button>
  );
}

export function ActionBar() {
  const actions = [
    { icon: FileSearch, label: 'Analisar Documento' },
    { icon: TrendingUp, label: 'Analisar Dados' },
    { icon: PenLine, label: 'Gerar Texto' },
    { icon: AudioWaveform, label: 'Responder com Voz' },
  ];

  return (
    <div className="grid grid-cols-4 gap-3 mt-8">
      {actions.map((action, index) => (
        <ActionButton key={index} {...action} />
      ))}
    </div>
  );
}
