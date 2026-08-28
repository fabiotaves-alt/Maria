import { motion } from 'framer-motion';
import { AuraBackground } from './AuraBackground';
import { FeatureCards } from './FeatureCard';
import { ActionBar } from './ActionBar';

export function CenterStage() {
  return (
    <main className="flex-1 relative flex flex-col items-center justify-center p-8 overflow-hidden">
      {/* Background com aura */}
      <AuraBackground />

      {/* Header */}
      <div className="text-center mb-8 z-10">
        <h1 
          className="text-5xl font-light tracking-[0.15em] mb-2"
          style={{ color: 'var(--maria-text)' }}
        >
          MARIA
        </h1>
        <p 
          className="text-base"
          style={{ color: 'var(--maria-muted)' }}
        >
          Sua assistente de IA pessoal e privada.
        </p>
      </div>

      {/* Avatar Central */}
      <motion.div
        className="relative mb-8 z-10"
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5 }}
      >
        {/* Glow/aura atrás do avatar */}
        <div
          className="absolute inset-0 rounded-[24px]"
          style={{
            background: 'radial-gradient(circle, rgba(232,90,138,0.15) 0%, transparent 70%)',
            filter: 'blur(60px)',
          }}
        />
        
        {/* Container do avatar */}
        <motion.div
          className="relative w-[350px] h-[450px] glass flex items-center justify-center overflow-hidden"
          style={{ borderRadius: '24px' }}
          animate={{ scale: [1, 1.02, 1] }}
          transition={{ 
            duration: 6, 
            ease: 'easeInOut', 
            repeat: Infinity 
          }}
        >
          {/* Placeholder para o avatar - será substituído por imagem real
              TEMA CLARO: Avatar com blusa de tricô bege clara
              TEMA ESCURO: Avatar com camisa preta de botões
          */}
          <div 
            className="w-full h-full flex items-center justify-center"
            style={{
              background: 'linear-gradient(135deg, rgba(232,90,138,0.1) 0%, rgba(232,90,138,0.05) 100%)',
            }}
          >
            <div className="text-center">
              <div 
                className="w-32 h-32 mx-auto mb-4 rounded-full flex items-center justify-center text-6xl font-light"
                style={{ 
                  background: 'rgba(232, 90, 138, 0.1)',
                  color: 'var(--maria-pink)',
                }}
              >
                M
              </div>
              <p className="text-sm" style={{ color: 'var(--maria-muted)' }}>
                Avatar da MARIA
              </p>
              <p className="text-xs mt-2" style={{ color: 'var(--maria-muted)' }}>
                (será substituído por imagem)
              </p>
            </div>
          </div>
          
          {/* Borda sutil com glow */}
          <div
            className="absolute inset-0 rounded-[24px] pointer-events-none"
            style={{
              boxShadow: '0 0 100px rgba(232,90,138,0.15), inset 0 0 30px rgba(232,90,138,0.05)',
              border: '1px solid rgba(232,90,138,0.1)',
            }}
          />
        </motion.div>
      </motion.div>

      {/* Feature Cards */}
      <FeatureCards />

      {/* Action Bar */}
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
