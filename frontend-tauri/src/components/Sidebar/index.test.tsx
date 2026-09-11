import { describe, it, expect, vi } from 'vitest';
import { indicaModeloPesado } from './index';

vi.mock('@tauri-apps/api/core', () => ({
  invoke: vi.fn(),
}));

describe('indicaModeloPesado — indicador de modelo 7B', () => {
  it('reconhece o modelo canónico 7B (minúsculas)', () => {
    expect(indicaModeloPesado('qwen2.5-omni-7b')).toBe(true);
  });

  it('não reconhece o modelo 3B', () => {
    expect(indicaModeloPesado('qwen2.5-omni-3b')).toBe(false);
  });

  it('é case-insensitive (maiúsculas)', () => {
    expect(indicaModeloPesado('LLAMA-7B')).toBe(true);
  });
});
