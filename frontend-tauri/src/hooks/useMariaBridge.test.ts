import { describe, it, expect, vi } from 'vitest';
import { pingBackend } from './useMariaBridge';

vi.mock('@tauri-apps/api/core', () => ({
  invoke: vi.fn().mockResolvedValue('pong'),
}));

describe('pingBackend', () => {
  it('retorna true quando o backend responde pong', async () => {
    const resultado = await pingBackend();
    expect(resultado).toBe(true);
  });
});