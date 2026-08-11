# Relatório do Benchmark Lia vs Python

Gerado em: 2026-08-06 13:32:46

## Resumo Executivo

❌ Python supera Lia em 24.0pp. Reavaliar projeto.

## Métricas Comparativas

| Métrica | Lia | Python | Diferença (pp) |
|---------|-----|--------|----------------|
| Parse Success | 52.0% | 98.0% | -46.0 |
| Type Check Success | 42.0% | 100.0% | -58.0 |
| Runtime Success | 42.0% | 66.0% | -24.0 |
| Output Match | 40.0% | 38.0% | +2.0 |
| Tokens Médios | 1002.8 | 350.9 | +651.9 |
| Latência Média (ms) | 11017.3 | 7486.1 | +3531.2 |

## Critérios de Decisão

| Critério | Meta | Resultado | Status |
|----------|------|-----------|--------|
| Runtime Success (Lia) | ≥ 90% | 42.0% | ❌ |
| Vantagem sobre Python | ≥ 15pp | -24.0pp | ❌ |
| Type Check (Lia) | ≥ 93% | 42.0% | ❌ |
| Output Match | ≥ 75% | 40.0% | ❌ |

## Distribuição de Erros

### Lia
| Tipo de Erro | Ocorrências |
|--------------|-------------|
| SyntaxError | 24 |
| UnboundVariableError | 4 |
| InferenceError | 1 |

### Python
| Tipo de Erro | Ocorrências |
|--------------|-------------|
| TypeError | 12 |
| NameError | 4 |
| Unknown | 1 |

## Conclusão e Próximos Passos

Com base nos resultados acima:

- **Se a vantagem for ≥ 15pp**: Avançar para implementação de ADTs + Pattern Matching (Fase 4)
- **Se a vantagem for 5-15pp**: Considerar redução de escopo para DSL de nicho
- **Se houver paridade (±5pp)**: Avaliar pivot para ferramenta de reparo
- **Se Python for superior**: Reavaliar fundamentos do projeto ou abandonar

---

*Relatório gerado automaticamente pelo benchmark harness da linguagem Lia.*
