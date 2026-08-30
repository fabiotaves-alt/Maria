import { motion } from 'framer-motion';
import { useTheme } from '../../hooks/useTheme';

export function AuraBackground() {
  const { theme } = useTheme();
  
  return (
    <>
      {/* Aura radial gradiente atrás do conteúdo */}
      <motion.div
        className="absolute inset-0 pointer-events-none"
        style={{
          background: `radial-gradient(circle at center, ${theme === 'light' ? 'rgba(232,90,138,0.08)' : 'rgba(224,93,138,0.06)'} 0%, transparent 60%)`,
        }}
        /* Pulso da aura desativado (conceito: aura tênue e estática) */
        // animate={{
        //   opacity: [0.3, 0.6, 0.3],
        //   scale: [1, 1.1, 1],
        // }}
        // transition={{
        //   duration: 4,
        //   ease: 'easeInOut',
        //   repeat: Infinity,
        // }}
      />
      
      {/* Partículas sutis de luz */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        {[...Array(3)].map((_, i) => (
          <motion.div
            key={i}
            className="absolute w-1 h-1 rounded-full"
            style={{
              backgroundColor: theme === 'light' ? 'rgba(232,90,138,0.3)' : 'rgba(224,93,138,0.3)',
              left: `${20 + i * 30}%`,
              top: `${30 + i * 20}%`,
              opacity: 0.3,
            }}
            /* Partículas estáticas (animação desativada junto com a aura) */
            // animate={{
            //   y: [0, -30, 0],
            //   opacity: [0, 0.5, 0],
            // }}
            // transition={{
            //   duration: 3 + i,
            //   ease: 'easeInOut',
            //   repeat: Infinity,
            //   delay: i * 0.5,
            // }}
          />
        ))}
      </div>
    </>
  );
}
