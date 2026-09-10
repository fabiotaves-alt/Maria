import { motion } from 'framer-motion';
import type { ConfirmacaoPendente } from '../../types';

interface ActionCardProps {
  confirmacao: ConfirmacaoPendente;
  mensagem: string;
  onConfirmar: () => void;
  onCancelar: () => void;
  loading?: boolean;
}

const LABEL_FERRAMENTA: Record<string, string> = {
  criar_planilha: 'Criar planilha',
  criar_documento: 'Criar documento',
  editar_planilha: 'Editar planilha',
};

export function ActionCard({
  confirmacao,
  mensagem,
  onConfirmar,
  onCancelar,
  loading,
}: ActionCardProps) {
  const labelAcao = LABEL_FERRAMENTA[confirmacao.ferramenta] ?? confirmacao.ferramenta;

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 8 }}
      transition={{ duration: 0.2 }}
      className="mx-4 mb-3 p-4 rounded-2xl border"
      style={{
        background: 'rgba(255,255,255,0.06)',
        borderColor: 'var(--maria-pink)',
        backdropFilter: 'blur(12px)',
      }}
    >
      {/* Badge da ferramenta */}
      <div className="flex items-center gap-2 mb-3">
        <span
          className="text-xs font-semibold px-2 py-0.5 rounded-full"
          style={{ background: 'var(--maria-pink)', color: '#fff' }}
        >
          {labelAcao}
        </span>
      </div>

      {/* Mensagem de confirmação vinda do backend */}
      <p
        className="text-sm mb-4 leading-relaxed whitespace-pre-line"
        style={{ color: 'var(--maria-text)' }}
      >
        {mensagem}
      </p>

      {/* Botões de ação */}
      <div className="flex gap-2">
        <button
          onClick={onConfirmar}
          disabled={loading}
          className="flex-1 py-2 rounded-xl text-sm font-semibold transition-opacity hover:opacity-90 disabled:opacity-40"
          style={{ background: 'var(--maria-pink)', color: '#fff' }}
        >
          Confirmar
        </button>
        <button
          onClick={onCancelar}
          disabled={loading}
          className="flex-1 py-2 rounded-xl text-sm font-semibold transition-opacity hover:opacity-80 disabled:opacity-40"
          style={{
            background: 'rgba(255,255,255,0.08)',
            color: 'var(--maria-muted)',
            border: '1px solid var(--maria-card-border)',
          }}
        >
          Cancelar
        </button>
      </div>
    </motion.div>
  );
}
