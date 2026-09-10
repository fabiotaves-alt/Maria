export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
}

export interface ResourceMetric {
  label: string;
  value: number;
  color?: string;
}

export interface NavItem {
  id: string;
  label: string;
  icon: string;
  active?: boolean;
}

export type Theme = 'light' | 'dark';

export interface ThemeContextType {
  theme: Theme;
  toggleTheme: () => void;
}

// Informações da ação pendente retornada pelo backend
export interface ConfirmacaoPendente {
  ferramenta: string;
  argumentos: Record<string, unknown>;
}

// Envelope estruturado quando o backend sinaliza ação pendente
export interface ChatBackendResponse {
  mensagem: string;
  confirmacao_pendente?: ConfirmacaoPendente;
  cadeia_ferramentas?: string[];
}

// Resposta normalizada para consumo interno do ChatPanel
export interface ChatResponse {
  resposta: string;
  modelo_usado: string;           // string livre; canônico: 'qwen2.5-omni-3b' | 'qwen2.5-omni-7b'
  tempo_processamento: number;
  confirmacao_pendente?: ConfirmacaoPendente;
}
