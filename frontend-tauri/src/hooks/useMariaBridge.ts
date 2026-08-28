import { invoke } from '@tauri-apps/api/core';

export interface SystemStatus {
  cpu: number;
  ram: number;
  gpu: number;
  modelo: string;
}

export interface ChatResponse {
  resposta: string;
  modelo_usado: 'qwen3b' | 'llama7b';
  tempo_processamento: number;
}

/**
 * Envia uma mensagem para o backend Python e retorna a resposta do LLM
 */
export async function sendMessage(text: string): Promise<ChatResponse> {
  try {
    const raw = await invoke<string>('send_message', { message: text });
    
    // Tenta parsear a resposta como JSON (formato padronizado do backend)
    try {
      const parsed = JSON.parse(raw);
      return {
        resposta: parsed.resposta || parsed.response || raw,
        modelo_usado: parsed.modelo_usado || 'qwen3b',
        tempo_processamento: parsed.tempo_processamento || 0,
      };
    } catch {
      // Se não for JSON, retorna como texto puro
      return {
        resposta: raw,
        modelo_usado: 'qwen3b',
        tempo_processamento: 0,
      };
    }
  } catch (error) {
    console.error('Erro ao enviar mensagem:', error);
    throw new Error(`Falha na comunicação com o backend: ${error}`);
  }
}

/**
 * Obtém o status atual do sistema (CPU, RAM, GPU, Modelo ativo)
 */
export async function getSystemStatus(): Promise<SystemStatus> {
  try {
    const status = await invoke<any>('get_status');
    return {
      cpu: status.cpu || 0,
      ram: status.ram || 0,
      gpu: status.gpu || 0,
      modelo: status.modelo || status.model || 'Qwen 2.5 3B',
    };
  } catch (error) {
    console.error('Erro ao obter status do sistema:', error);
    // Retorna valores padrão em caso de erro
    return {
      cpu: 0,
      ram: 0,
      gpu: 0,
      modelo: 'Qwen 2.5 3B',
    };
  }
}

/**
 * Ping para verificar se o backend está responsivo
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
 * Carrega o histórico de conversas do banco de dados
 */
export async function getChatHistory(conversationId?: number): Promise<any[]> {
  try {
    const messages = await invoke<any[]>('get_chat_history', { 
      conversationId: conversationId || 1 
    });
    return messages;
  } catch (error) {
    console.error('Erro ao carregar histórico:', error);
    return [];
  }
}
