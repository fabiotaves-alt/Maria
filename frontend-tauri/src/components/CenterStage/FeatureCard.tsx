import { Shield, Cpu, Sparkles } from 'lucide-react';
import { motion } from 'framer-motion';

interface FeatureCardProps {
  icon: React.ComponentType<{ size: number }>;
  title: string;
  description: string;
}

function FeatureCard({ icon: Icon, title, description }: FeatureCardProps) {
  return (
    <motion.div
      className="glass p-4 flex items-start gap-3"
      style={{ borderRadius: '16px', maxWidth: '280px' }}
      whileHover={{ 
        y: -2,
        boxShadow: '0 10px 40px rgba(232, 90, 138, 0.15)',
      }}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <div 
        className="w-9 h-9 rounded-full flex items-center justify-center flex-shrink-0"
        style={{ background: 'rgba(232, 90, 138, 0.1)' }}
      >
        <Icon size={18} style={{ color: 'var(--maria-pink)' }} />
      </div>
      <div>
        <h3 className="text-sm font-semibold mb-1" style={{ color: 'var(--maria-text)' }}>
          {title}
        </h3>
        <p className="text-xs" style={{ color: 'var(--maria-muted)' }}>
          {description}
        </p>
      </div>
    </motion.div>
  );
}

export function FeatureCards() {
  const features = [
    {
      icon: Shield,
      title: 'Privacidade total',
      description: 'Seus dados ficam sempre com você.',
    },
    {
      icon: Cpu,
      title: 'Inteligência local',
      description: 'Processamento 100% no seu computador.',
    },
    {
      icon: Sparkles,
      title: 'Pronta para ajudar',
      description: 'Pergunte, analise, organize, crie.',
    },
  ];

  return (
    <div className="flex flex-col gap-3">
      {features.map((feature, index) => (
        <FeatureCard key={index} {...feature} />
      ))}
    </div>
  );
}
