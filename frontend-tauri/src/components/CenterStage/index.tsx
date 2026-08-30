import { motion } from 'framer-motion';
import { AuraBackground } from './AuraBackground';
import { FeatureCards } from './FeatureCard';
import { ActionBar } from './ActionBar';
import mariaAvatar from '../../assets/maria-avatar.png';
import mariaLogo from '../../assets/maria-logo.png';
import { useTheme } from '../../hooks/useTheme';

export function CenterStage() {
  const { theme } = useTheme();
  
  return (
    <main className="flex-1 relative flex flex-col items-center justify-center p-8 overflow-hidden">
      {/* Background com aura */}
      <AuraBackground />

      {/* Container principal com layout de 2 colunas */}
      <div className="flex flex-row items-center gap-12 z-10 max-w-6xl w-full">
        {/* Coluna esquerda: Logo + subtítulo + feature cards */}
        <div className="w-1/2 flex flex-col justify-center gap-8">
          {/* Logo e subtítulo */}
          <div className="text-left">
            <img 
              src={mariaLogo} 
              alt="MARIA" 
              className="h-20 w-auto mb-4"
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
          className="w-1/2 relative flex items-center justify-center"
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5 }}
        >
          {/* Aura tênue atrás do avatar (pulso desativado) */}
          <div
            className="absolute w-[460px] h-[460px] rounded-full bg-pink-500/10 blur-[100px]"
          />
          
          {/* Círculo tênue atrás do avatar (no lugar do retângulo) */}
          <motion.div
            className="relative w-[420px] h-[420px] flex items-center justify-center overflow-hidden rounded-full border border-pink-500/20"
            /* Animação de respiração desativada */
            // animate={{ scale: [1, 1.02, 1] }}
            // transition={{ 
            //   duration: 6, 
            //   ease: 'easeInOut', 
            //   repeat: Infinity 
            // }}
          >
            {/* Imagem real do avatar */}
            <img 
              src={mariaAvatar} 
              alt="MARIA Avatar" 
              className="w-full h-full object-cover rounded-full"
              style={{
                filter: theme === 'light' ? 'brightness(1.1)' : 'brightness(0.95)',
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
