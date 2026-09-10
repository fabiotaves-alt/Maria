import { describe, it, expect, vi } from 'vitest';
import { invoke } from '@tauri-apps/api/core';
import { pingBackend, normalizarResposta, getSystemStatus } from './useMariaBridge';

vi.mock('@tauri-apps/api/core', () => ({
  invoke: vi.fn().mockResolvedValue('pong'),
}));

describe('pingBackend', () => {
  it('retorna true quando o backend responde pong', async () => {
    const resultado = await pingBackend();
    expect(resultado).toBe(true);
  });
});

describe('normalizarResposta — defesa contra JSON bruto', () => {
  it('JSON com envelope correto extrai mensagem normalmente', () => {
    const envelope = JSON.stringify({
      mensagem: 'Posso criar a planilha?',
      confirmacao_pendente: { ferramenta: 'criar_planilha', argumentos: {} },
      cadeia_ferramentas: [],
    });
    const resultado = normalizarResposta(envelope);
    expect(resultado.resposta).toBe('Posso criar a planilha?');
  });

  it('JSON sem chave mensagem não vaza o JSON bruto na resposta', () => {
    const toolCallRaw = JSON.stringify({
      name: 'criar_planilha',
      arguments: { nome_arquivo: 'gastos', colunas: ['Data', 'Valor'] },
    });
    const resultado = normalizarResposta(toolCallRaw);
    expect(resultado.resposta).not.toContain('{');
    expect(resultado.resposta).not.toContain('criar_planilha');
  });

  it('texto simples é devolvido como resposta sem alteração', () => {
    const resultado = normalizarResposta('Olá, como posso ajudar?');
    expect(resultado.resposta).toBe('Olá, como posso ajudar?');
  });
});

describe('getSystemStatus — campo online', () => {
  it('retorna online:true quando backend responde', async () => {
    vi.mocked(invoke).mockResolvedValueOnce({
      cpu: 10,
      ram: 20,
      gpu: 0,
      modelo: 'qwen2.5-omni-3b',
    });
    const status = await getSystemStatus();
    expect(status.online).toBe(true);
  });

  it('retorna online:false quando backend está offline', async () => {
    vi.mocked(invoke).mockRejectedValueOnce(new Error('Backend offline'));
    const status = await getSystemStatus();
    expect(status.online).toBe(false);
  });
});