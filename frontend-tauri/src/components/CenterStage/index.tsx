import { motion } from 'framer-motion';
import { AuraBackground } from './AuraBackground';
import { FeatureCards } from './FeatureCard';
import { ActionBar } from './ActionBar';
import mariaAvatar from '../../assets/maria-avatar.svg';
import mariaLogo from '../../assets/maria-logo.svg';
import { useTheme } from '../../hooks/useTheme';

export function CenterStage() {
  const { theme } = useTheme();
  
  return (
    <main className="flex-1 relative flex flex-col items-center justify-center p-8 overflow-hidden">
      {/* Background com aura */}
      <AuraBackground />

      {/* Container principal com layout de 2 colunas */}
      <div className="flex items-center gap-12 z-10 max-w-5xl">
        {/* Coluna esquerda: Logo + subtítulo + feature cards */}
        <div className="flex flex-col gap-6">
          {/* Logo e subtítulo */}
          <div className="text-left">
            <img 
              src={mariaLogo} 
              alt="MARIA" 
              className="h-16 w-auto mb-4"
              style={{ 
                filter: theme === 'light' ? 'brightness(0)' : 'brightness(2)',
              }}
            />
            <p 
              className="text-lg"
              style={{ color: 'var(--maria-text-muted)' }}
            >
              Sua assistente de IA pessoal e privada.
            </p>
          </div>

          {/* Feature Cards - empilhados verticalmente */}
          <FeatureCards />
        </div>

        {/* Coluna direita: Avatar com aura */}
        <motion.div
          className="relative"
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5 }}
        >
          {/* Glow/aura atrás do avatar */}
          <div
            className="absolute inset-0 rounded-[24px]"
            style={{
              background: `radial-gradient(circle, ${theme === 'light' ? 'rgba(232,90,138,0.2)' : 'rgba(255,107,157,0.2)'} 0%, transparent 70%)`,
              filter: 'blur(60px)',
            }}
          />
          
          {/* Container do avatar */}
          <motion.div
            className="relative w-[320px] h-[420px] glass flex items-center justify-center overflow-hidden"
            style={{ borderRadius: '24px' }}
            animate={{ scale: [1, 1.02, 1] }}
            transition={{ 
              duration: 6, 
              ease: 'easeInOut', 
              repeat: Infinity 
            }}
          >
            {/* Imagem real do avatar */}
            <img 
              src={mariaAvatar} 
              alt="MARIA Avatar" 
              className="w-full h-full object-cover"
              style={{
                filter: theme === 'light' ? 'brightness(1.1)' : 'brightness(0.95)',
              }}
            />
            
            {/* Borda sutil com glow */}
            <div
              className="absolute inset-0 rounded-[24px] pointer-events-none"
              style={{
                boxShadow: `0 0 100px ${theme === 'light' ? 'rgba(232,90,138,0.15)' : 'rgba(255,107,157,0.15)'}, inset 0 0 30px rgba(255,255,255,0.05)`,
                border: `1px solid ${theme === 'light' ? 'rgba(232,90,138,0.1)' : 'rgba(255,255,255,0.1)'}`,
              }}
            />
          </motion.div>
        </motion.div>
      </div>

      {/* Action Bar - abaixo do conteúdo principal */}
      <ActionBar />

      {/* Footer */}
      <p 
        className="mt-8 text-sm italic z-10"
        style={{ color: 'var(--maria-muted)' }}
      >
        MARIA está pronta para ajudar você.
      </p>
    </main>
  );
}
