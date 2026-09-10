import { invoke } from '@tauri-apps/api/core';
import type { ChatResponse, ChatBackendResponse, ConfirmacaoPendente } from '../types';

export type { ChatResponse, ConfirmacaoPendente };

export interface SystemStatus {
  cpu: number;
  ram: number;
  gpu: number;
  modelo: string;
  versao?: string;
  online?: boolean;
}

/**
 * Normaliza a resposta do backend (string pura ou envelope objeto)
 * para o contrato ChatResponse consumido pelo ChatPanel.
 *
 * O backend devolve string pura para respostas textuais simples e
 * objeto JSON para respostas com confirmacao_pendente.
 */
export function normalizarResposta(raw: string): ChatResponse {
  let parsed: unknown;
  try {
    parsed = JSON.parse(raw);
  } catch {
    // não é JSON — string pura, devolve intacta
    return {
      resposta: raw,
      modelo_usado: 'qwen2.5-omni-3b',
      tempo_processamento: 0,
    };
  }

  if (
    parsed &&
    typeof parsed === 'object' &&
    typeof (parsed as ChatBackendResponse).mensagem === 'string'
  ) {
    const envelope = parsed as ChatBackendResponse;
    return {
      resposta: envelope.mensagem,
      modelo_usado: 'qwen2.5-omni-3b',
      tempo_processamento: 0,
      confirmacao_pendente: envelope.confirmacao_pendente,
    };
  }

  // JSON válido mas sem o envelope esperado — nunca vazar o JSON bruto na UI
  return {
    resposta: '',
    modelo_usado: 'qwen2.5-omni-3b',
    tempo_processamento: 0,
  };
}

/**
 * Envia mensagem ao backend (chat normal ou resposta de confirmação 'sim'/'não').
 * O backend decide internamente o ramo com base em tem_acao_pendente().
 */
export async function sendMessage(text: string): Promise<ChatResponse> {
  const raw = await invoke<string>('send_message', { message: text });
  return normalizarResposta(raw);
}

/**
 * Obtém o status atual do sistema (CPU, RAM, GPU, modelo ativo).
 */
export async function getSystemStatus(): Promise<SystemStatus> {
  try {
    const status = await invoke<Record<string, unknown>>('get_status');
    return {
      cpu: Number(status.cpu) || 0,
      ram: Number(status.ram) || 0,
      gpu: Number(status.gpu) || 0,
      modelo: String(status.modelo || status.model || 'qwen2.5-omni-3b'),
      versao: status.versao ? String(status.versao) : undefined,
      online: true,
    };
  } catch {
    return { cpu: 0, ram: 0, gpu: 0, modelo: 'qwen2.5-omni-3b', online: false };
  }
}

/**
 * Ping para verificar se o backend está responsivo.
 */
export async function pingBackend(): Promise<boolean> {
  try {
    const result = await invoke<string>('ping');
    return result === 'pong';
  } catch {
    return false;
  }
}

/**
 * Carrega o histórico de conversas do banco de dados (via Rust/rusqlite).
 */
export async function getChatHistory(conversationId = 1): Promise<unknown[]> {
  try {
    return await invoke<unknown[]>('get_chat_history', { conversationId });
  } catch {
    return [];
  }
}
