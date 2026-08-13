# Guia de Planejamento — Próxima Fase MARIA

**Organização:** Fase 0 (correções triviais, executar agora) → Fase 1 (métricas do benchmark, prioridade de desenvolvimento) → Fase 2 (modelo/RAG/fine-tuning, já validado em guia anterior, incorporado aqui) → Fase 3 (itens que precisam de definição antes de qualquer especificação).

**Fora de escopo deste guia:** o indicador de espera/UX de streaming e a correção do prompt de benchmark (`Etapas 1-3` de parsing/idioma/keywords) seguem pendentes de decisão em threads anteriores e não são tratados aqui.

---

## Fase 0 — Correções triviais, executar agora

### 0.1 Bug do leitor de arquivos (`listar_arquivos`)

**Problema observado:**
```
maria@assistente:~$ você pode verificar os arquivos que você tem acesso no momento?
ERROR - Erro ao executar ferramenta de leitura: A pasta 'arquivos_gerados' não existe ou não é um diretório.
```

**Causa raiz confirmada por rastreamento do código:** em `core/file_utils.py`, `listar_arquivos(pasta="")` chama `resolver_caminho_permitido(pasta or pastas_permitidas[0])`. Quando `pasta` está vazia, isso passa o **próprio caminho da pasta permitida** (ex.: `"arquivos_gerados"`, valor relativo por padrão em `core/config.py`) como se fosse um subcaminho a resolver *dentro* de cada pasta permitida. Como `resolver_caminho_permitido` junta esse valor a cada entrada de `pastas_permitidas`, o resultado é um caminho duplicado (`arquivos_gerados/arquivos_gerados`), que nunca existe — daí o erro "não existe" mesmo em instalações onde a pasta padrão nunca foi criada (nenhum arquivo gerado ainda). O bug não aparece nos testes existentes porque `tests/test_maria.py` sempre define `PASTAS_PERMITIDAS` como um caminho **absoluto** de diretório temporário, o que evita a duplicação (ela só ocorre com caminhos relativos, o cenário real da aplicação).

**Arquivo:** `core/file_utils.py`

**Instruções:**

1. Localize:
   ```python
   def listar_arquivos(pasta: str = "") -> list[dict]:
       """Lista nome e tamanho (KB) dos arquivos de uma pasta permitida.

       Raises:
           ValueError: pasta inexistente, não é diretório, ou fora das pastas permitidas.
           PermissionError: sem permissão de leitura na pasta.
       """
       pastas_permitidas = _pastas_permitidas()
       base = resolver_caminho_permitido(pasta or pastas_permitidas[0])
       if not base.is_dir():
           raise ValueError(f"A pasta '{base.name}' não existe ou não é um diretório.")
   ```

2. Substitua por:
   ```python
   def listar_arquivos(pasta: str = "") -> list[dict]:
       """Lista nome e tamanho (KB) dos arquivos de uma pasta permitida.

       Quando `pasta` não é informada, usa a primeira pasta permitida como
       padrão e a cria automaticamente se ainda não existir (equivalente a
       "nenhum arquivo ainda", não um erro).

       Raises:
           ValueError: pasta explicitamente informada não existe, não é
               diretório, ou está fora das pastas permitidas.
           PermissionError: sem permissão de leitura/criação na pasta.
       """
       pastas_permitidas = _pastas_permitidas()

       if pasta:
           base = resolver_caminho_permitido(pasta)
       else:
           base = Path(pastas_permitidas[0]).resolve()
           os.makedirs(base, exist_ok=True)

       if not base.is_dir():
           raise ValueError(f"A pasta '{base.name}' não existe ou não é um diretório.")
   ```

   Não são necessários novos imports (`os` e `Path` já estão importados no topo do arquivo).

**Novo teste** — adicionar em `tests/test_maria.py`, na classe `TestAcessoLeitura`:
```python
    def test_listar_pasta_padrao_ausente_nao_gera_caminho_duplicado(self):
        """Testa que listar_arquivos() sem pasta explícita não duplica o
        caminho e cria a pasta padrão automaticamente se ainda não existir."""
        pasta_inexistente = os.path.join(self.temp_dir.name, "ainda_nao_criada")
        os.environ["PASTAS_PERMITIDAS"] = pasta_inexistente

        self.assertFalse(os.path.isdir(pasta_inexistente))

        itens = listar_arquivos()

        self.assertEqual(itens, [])
        self.assertTrue(os.path.isdir(pasta_inexistente))
```

**Critérios de aceite:**
- [ ] `listar_arquivos()` sem argumento, apontando para uma pasta permitida relativa que ainda não existe, retorna `[]` em vez de levantar `ValueError`.
- [ ] `listar_arquivos("subpasta_que_nao_existe")` (nome explícito) continua levantando `ValueError` normalmente — comportamento inalterado.
- [ ] Novo teste `test_listar_pasta_padrao_ausente_nao_gera_caminho_duplicado` passa.
- [ ] `python -m unittest tests.test_maria -v` sem regressão.
- [ ] `python -m py_compile core/file_utils.py tests/test_maria.py` sem erros.

---

### 0.2 Seleção de modelo via linha de comando (`python main.py -m "modelo"`)

**Arquivo:** `main.py`

**Instruções:**

1. No topo do arquivo, adicione o import:
   ```python
   import argparse
   ```

2. Localize o construtor de `MariaController`:
   ```python
   class MariaController:
       """
       Encapsula toda a lógica de negócio da MARIA:
       conexão com Ollama, sessão de chat, ferramentas e persistência.
       """

       def __init__(self):
           self.cliente: OllamaClient | None = None
           self.sessao: ChatSession | None = None
           self.nome_sessao: str = ""
           self._tool_call_final = None
           self._resposta_textual = ""
   ```
   Substitua por:
   ```python
   class MariaController:
       """
       Encapsula toda a lógica de negócio da MARIA:
       conexão com Ollama, sessão de chat, ferramentas e persistência.
       """

       def __init__(self, modelo: str | None = None):
           self.cliente: OllamaClient | None = None
           self.sessao: ChatSession | None = None
           self.nome_sessao: str = ""
           self._tool_call_final = None
           self._resposta_textual = ""
           self.modelo = modelo
   ```

3. Localize `inicializar`:
   ```python
       def inicializar(self):
           """Cria cliente, sessão e define nome do arquivo de persistência."""
           self.cliente = OllamaClient()
   ```
   Substitua por:
   ```python
       def inicializar(self):
           """Cria cliente, sessão e define nome do arquivo de persistência."""
           self.cliente = OllamaClient(model=self.modelo) if self.modelo else OllamaClient()
   ```

4. Localize `main()`:
   ```python
   def main():
       # Verificar dependências
       try:
           import requests  # noqa: F401
       except ImportError:
           print("\n[ERRO] A biblioteca 'requests' não está instalada.")
           print("Instale com: pip install requests\n")
           sys.exit(1)

       # Criar controller e interface
       controller = MariaController()
       interface = InterfaceTerminal(controller, imagem_banner="maria_opening.png")

       # Delegar totalmente para a interface
       interface.iniciar()
   ```
   Substitua por:
   ```python
   def main():
       parser = argparse.ArgumentParser(description="MARIA - Assistente de IA de Escritório")
       parser.add_argument(
           "-m", "--modelo",
           dest="modelo",
           default=None,
           help="Nome do modelo Ollama a usar nesta execução (ex: qwen3:8b). "
                "Se omitido, usa OLLAMA_MODEL do ambiente/config.py."
       )
       args = parser.parse_args()

       # Verificar dependências
       try:
           import requests  # noqa: F401
       except ImportError:
           print("\n[ERRO] A biblioteca 'requests' não está instalada.")
           print("Instale com: pip install requests\n")
           sys.exit(1)

       # Criar controller e interface
       controller = MariaController(modelo=args.modelo)
       interface = InterfaceTerminal(controller, imagem_banner="maria_opening.png")

       # Delegar totalmente para a interface
       interface.iniciar()
   ```

Erros de modelo inexistente/Ollama fora do ar continuam tratados pelo caminho já existente (`OllamaClientError` propagada até `InterfaceTerminal.iniciar()`, que já captura e exibe `[ERRO] Falha ao inicializar: ...`); nenhum tratamento de exceção novo é necessário.

**Novos testes** — adicionar em `tests/test_maria.py`:
```python
class TestSelecaoModeloCLI(unittest.TestCase):
    """Testes para a seleção de modelo via argumento -m/--modelo (main.py)."""

    def test_controller_usa_modelo_informado(self):
        from main import MariaController
        controller = MariaController(modelo="qwen3:8b")
        controller.inicializar()
        self.assertEqual(controller.cliente.model, "qwen3:8b")

    def test_controller_usa_modelo_padrao_quando_nao_informado(self):
        from main import MariaController
        from core.config import OLLAMA_MODEL
        controller = MariaController()
        controller.inicializar()
        self.assertEqual(controller.cliente.model, OLLAMA_MODEL)
```

**Critérios de aceite:**
- [ ] `python main.py -m "qwen3:8b"` inicia a MARIA usando `qwen3:8b`, sem exigir variável de ambiente.
- [ ] `python main.py` (sem flag) mantém o comportamento atual (`OLLAMA_MODEL` do ambiente/`config.py`).
- [ ] Novos testes de `TestSelecaoModeloCLI` passam.
- [ ] `python -m unittest tests.test_maria -v` sem regressão.
- [ ] `python -m py_compile main.py tests/test_maria.py` sem erros.

---

### 0.3 Warmup do modelo na inicialização interativa

**Contexto:** o benchmark já faz warmup (`_warmup_model` em `benchmark/run_benchmark.py`), mas o app interativo (`main.py`/`ui_terminal.py`) não — a primeira mensagem real do usuário paga o custo de carregar o modelo em memória. Interpretação assumida para "warmup com algo leve": uma única mensagem curta, sem ferramentas, sem streaming — mesmo padrão já usado no warmup do benchmark. Ajuste esta suposição se a intenção era outra.

**Arquivo:** `main.py`

**Instruções:**

1. Adicione um novo método em `MariaController`, próximo de `inicializar`/`finalizar`:
   ```python
       def aquecer_modelo(self) -> None:
           """
           Envia uma mensagem mínima ao modelo para forçar o carregamento em
           memória antes da primeira interação real do usuário. Best-effort:
           falhas aqui não interrompem a aplicação, pois o mesmo erro será
           reportado de forma amigável na primeira mensagem real, se persistir.
           """
           try:
               self.cliente.enviar_mensagem(
                   mensagens=[{"role": "user", "content": "Responda apenas com a palavra ok."}],
                   tools=None,
                   stream=False,
               )
           except Exception as error:
               logger.warning(f"Aquecimento do modelo falhou (não crítico): {error}")
   ```

**Arquivo:** `ui_terminal.py`

2. Localize, em `InterfaceTerminal.iniciar`:
   ```python
           # Exibir banner
           exibir_banner(imagem=self.imagem_banner)
           print("\nOlá! Eu sou a MARIA, sua assistente de escritório.")
           print("Rodando 100% localmente no seu computador, sem internet.\n")
           print("Como posso ajudar você hoje?")
   ```
   Substitua por:
   ```python
           # Exibir banner
           exibir_banner(imagem=self.imagem_banner)
           print("\nOlá! Eu sou a MARIA, sua assistente de escritório.")
           print("Rodando 100% localmente no seu computador, sem internet.\n")

           print("Aquecendo o modelo, aguarde um instante...")
           self.controller.aquecer_modelo()

           print("Como posso ajudar você hoje?")
   ```

**Novos testes** — adicionar em `tests/test_maria.py`:
```python
class TestAquecimentoModelo(unittest.TestCase):
    """Testes para o warmup do modelo na inicialização interativa (main.py)."""

    def test_aquecer_modelo_chama_enviar_mensagem(self):
        from main import MariaController
        controller = MariaController()
        controller.inicializar()
        controller.cliente.enviar_mensagem = MagicMock(return_value="ok")

        controller.aquecer_modelo()

        controller.cliente.enviar_mensagem.assert_called_once()

    def test_aquecer_modelo_nao_propaga_excecao(self):
        from main import MariaController
        from core.ollama_client import OllamaClientError
        controller = MariaController()
        controller.inicializar()
        controller.cliente.enviar_mensagem = MagicMock(side_effect=OllamaClientError("falha"))

        controller.aquecer_modelo()  # não deve levantar exceção
```

**Critérios de aceite:**
- [ ] `MariaController.aquecer_modelo()` existe e nunca propaga exceção.
- [ ] `ui_terminal.py` chama `aquecer_modelo()` após o banner e antes do primeiro prompt.
- [ ] Novos testes de `TestAquecimentoModelo` passam.
- [ ] `python -m unittest tests.test_maria -v` sem regressão.
- [ ] `python -m py_compile main.py ui_terminal.py tests/test_maria.py` sem erros.

---

## Fase 1 — Benchmark: expansão de métricas (prioridade de desenvolvimento)

Fundamentação: BFCL (Yan et al., *Berkeley Function-Calling Leaderboard*, 2024/2025) avalia acurácia de argumentos via correspondência estrutural, não apenas o nome da função chamada, e inclui detecção de "abstenção" (não chamar ferramenta quando nenhuma é apropriada); τ-bench (Yao et al., 2024) e τ²-bench (Barres et al., 2025) medem conclusão de tarefa ponta a ponta e rastreamento de estado em múltiplos turnos; API-Bank (Li et al., 2023a) mede acurácia de chamadas de API separadamente da qualidade da resposta pós-chamada; fontes de prática de 2026 (Spheron Blog, *AI Agent Tool Calling Benchmarks*, jun/2026; Morph LLM, *AI Agent Evaluation*, jun/2026) reforçam medir custo de prefill/schema separadamente da decodificação, e observar métricas de trajetória (nº de passos vs. mínimo necessário, loops, recuperação de erro) além do resultado final.

### 1.1 Achado estrutural: o benchmark não exercita o encadeamento real de leitura

`benchmark/runners/maria_runner.py` chama `chat_com_tools_stream`/`chat_com_tools_stream_com_metricas` diretamente. O encadeamento automático de ferramentas de leitura (`listar_arquivos`/`resumir_documento` sem pedir confirmação, até `MAX_PASSOS_LEITURA` vezes) só existe em `main.py` (`MariaController._gerar_resposta_com_encadeamento`) e **nunca é exercitado pelo benchmark**. Isso significa que tarefas como a 23 ("Edição inexistente B"), que na aplicação real poderiam se beneficiar do encadeamento (ex.: `listar_arquivos` seguido de uma resposta final do modelo), são avaliadas no benchmark apenas pela primeira tool call, sem o comportamento real de produção.

**Recomendação (não especificar código agora — requer decisão de arquitetura):** extrair a lógica de encadeamento de `main.py` para um módulo compartilhado (ex.: `core/tool_chaining.py`), usado tanto por `MariaController` quanto por `MariaRunner`. Antes de implementar, decidir: o `MariaRunner` deve respeitar o mesmo `BENCHMARK_TASK_TIMEOUT` durante o encadeamento (múltiplas chamadas ao modelo dentro do timeout de uma única tarefa)? Isso afeta o critério de "TimeoutError" já existente no benchmark.

### 1.2 Acurácia de argumentos (não só nome da ferramenta)

**Problema:** `benchmark/runners/maria_runner.py` calcula `tool_correct` comparando apenas `detected_name == task.expected_tool`. Os argumentos (`raw_tool_args`) são registrados no log, mas nunca comparados contra um valor esperado — uma tarefa passa mesmo se o modelo chamar a ferramenta certa com dados errados.

**Arquivos:** `benchmark/tasks/task_schema.py`, `benchmark/runners/maria_runner.py`, `benchmark/tasks/tasks_core.py`

**Instruções:**

1. Em `benchmark/tasks/task_schema.py`, adicione um campo ao final do dataclass `MariaTask` (posição segura, não quebra nenhuma instanciação existente por posição):
   ```python
   @dataclass
   class MariaTask:
       id: int
       name: str
       description: str
       user_message: str
       expected_tool: str | None = None
       expected_keywords: list[str] = field(default_factory=list)
       confirm_sequence: list[str] = field(default_factory=list)
       expected_final_message: str | None = None
       context: list[dict] = field(default_factory=list)
       category: MariaTaskCategory = MariaTaskCategory.CONVERSA
       expected_args_subset: dict | None = None
   ```

2. No mesmo arquivo, adicione um campo ao final de `MariaTaskResult`:
   ```python
       args_correct: bool = True
   ```
   (será usado também no passo 1.3 — adicione `ttft_ms: float | None = None` na mesma edição, ver Instrução 3 da seção 1.3.)

3. Em `benchmark/runners/maria_runner.py`, adicione um método estático à classe `MariaRunner`:
   ```python
       @staticmethod
       def _argumentos_compativeis(obtidos: dict, esperados: dict | None) -> bool:
           """Verifica se os argumentos obtidos contêm, com valores iguais,
           todas as chaves declaradas em `esperados` (comparação de
           subconjunto — campos extras nos argumentos obtidos, como
           'descricao', não invalidam o resultado). Retorna True quando
           `esperados` é None (tarefa não define critério de argumento)."""
           if esperados is None:
               return True
           if not isinstance(obtidos, dict):
               return False
           return all(
               chave in obtidos and obtidos[chave] == valor
               for chave, valor in esperados.items()
           )
   ```

4. Ainda em `MariaRunner.run()`, localize onde `MariaTaskResult` é construído e adicione o campo `args_correct`:
   ```python
           detected_name = tool_call_final.get("name") if tool_call_final else None
           tool_correct = (
               detected_name == task.expected_tool
               if task.expected_tool is not None
               else detected_name is None
           )
           args_correct = self._argumentos_compativeis(
               (tool_call_final or {}).get("arguments", {}), task.expected_args_subset
           )
   ```
   E inclua `args_correct=args_correct,` na chamada de `MariaTaskResult(...)`.

5. Popule `expected_args_subset` em pelo menos um exemplo por categoria de escrita, como padrão a estender às demais tarefas de `criar_planilha`/`criar_documento`/`editar_planilha` em `tasks_core.py`:
   ```python
   MariaTask(3, "Planilha básica", "Planilha de gastos com duas colunas",
             "Crie uma planilha de gastos com colunas Data e Valor.",
             "criar_planilha", ["planilha"], ["sim"], category=MariaTaskCategory.CRIAR_PLANILHA,
             expected_args_subset={"nome_arquivo": "gastos", "colunas": ["Data", "Valor"]}),
   ```
   O `nome_arquivo` esperado é o nome **antes** do sufixo de unicidade (`gerar_nome_unico`), pois `raw_tool_args` registra os argumentos da tool call, não o nome final do arquivo salvo — sempre confira o `raw_tool_args` de execuções anteriores antes de fixar o valor esperado.

**Critérios de aceite:**
- [ ] `MariaTask` e `MariaTaskResult` aceitam os novos campos sem quebrar nenhuma instanciação existente.
- [ ] `_argumentos_compativeis` cobre: sem critério (`None` → `True`), subconjunto correto (`True`), divergência (`False`).
- [ ] Pelo menos uma tarefa de cada categoria de escrita (`criar_planilha`, `criar_documento`, `editar_planilha`) com `expected_args_subset` definido.
- [ ] Novos testes unitários para `_argumentos_compativeis` (ver bloco abaixo) passam.

**Novos testes** — adicionar em `tests/test_maria.py`:
```python
class TestAcuraciaDeArgumentos(unittest.TestCase):
    """Testes para a comparação de argumentos do benchmark (MariaRunner)."""

    def test_argumentos_compativeis_sem_criterio_retorna_true(self):
        from benchmark.runners.maria_runner import MariaRunner
        self.assertTrue(MariaRunner._argumentos_compativeis({"a": 1}, None))

    def test_argumentos_compativeis_subconjunto_correto(self):
        from benchmark.runners.maria_runner import MariaRunner
        obtidos = {"nome_arquivo": "gastos", "colunas": ["Data", "Valor"], "descricao": "extra"}
        esperados = {"nome_arquivo": "gastos", "colunas": ["Data", "Valor"]}
        self.assertTrue(MariaRunner._argumentos_compativeis(obtidos, esperados))

    def test_argumentos_incompativeis_detecta_divergencia(self):
        from benchmark.runners.maria_runner import MariaRunner
        obtidos = {"nome_arquivo": "gastos_errado", "colunas": ["Data", "Valor"]}
        esperados = {"nome_arquivo": "gastos", "colunas": ["Data", "Valor"]}
        self.assertFalse(MariaRunner._argumentos_compativeis(obtidos, esperados))
```

### 1.3 TTFT separado da velocidade de decodificação (corrige `tokens_por_segundo`)

**Problema confirmado nos próprios dados do projeto:** em `benchmark/results/run_20260811_231930/log.json`, task 8 (3ª execução) registra `"tokens_gerados": 400, "tokens_por_segundo": 2560819.4...` — fisicamente implausível em CPU. Causa: `chat_com_tools_stream_com_metricas` divide `eval_count` pela duração **total** da requisição; quando a resposta chega em um único chunk (ou a medição captura uma janela quase nula), a divisão explode. A prática do setor (Spheron Blog, 2026) trata custo de prefill/schema e velocidade de decodificação como fases distintas — aqui isso se traduz em capturar o TTFT (tempo até o primeiro token) separadamente e só calcular tokens/s sobre a fase de decodificação propriamente dita, com um piso mínimo de duração para considerar a medição confiável.

**Arquivo:** `core/ollama_client.py`

**Instruções:**

1. Localize a assinatura e o corpo de `chat_com_tools_stream_com_metricas`:
   ```python
       def chat_com_tools_stream_com_metricas(
           self,
           mensagem_usuario: str,
           historico: list[dict[str, str]] | None = None,
           tools: list[dict] | None = None,
       ) -> tuple[str, dict | None, int, float]:
           """Envia uma mensagem em streaming e retorna texto, tool call e métricas de tokens."""
   ```
   Substitua a assinatura e o docstring por:
   ```python
       def chat_com_tools_stream_com_metricas(
           self,
           mensagem_usuario: str,
           historico: list[dict[str, str]] | None = None,
           tools: list[dict] | None = None,
       ) -> tuple[str, dict | None, int, float, float | None]:
           """Envia uma mensagem em streaming e retorna texto, tool call e
           métricas de tokens, incluindo TTFT (tempo até o primeiro token)
           separado da velocidade de decodificação."""
   ```

2. Localize:
   ```python
           response = self._make_request(payload, stream=True)
           tool_call_final = None
           partes_texto: list[str] = []
           eval_count = 0
           inicio = time.monotonic()

           try:
               for line in response.iter_lines():
                   if not line:
                       continue

                   try:
                       data = json.loads(line.decode("utf-8"))
                   except json.JSONDecodeError:
                       continue

                   message = data.get("message", {})
                   content = message.get("content", "")
                   if content:
                       partes_texto.append(content)

                   if data.get("done") is True:
                       eval_count = int(data.get("eval_count") or 0)
   ```
   Substitua por:
   ```python
           response = self._make_request(payload, stream=True)
           tool_call_final = None
           partes_texto: list[str] = []
           eval_count = 0
           inicio = time.monotonic()
           t_primeiro_token: float | None = None

           try:
               for line in response.iter_lines():
                   if not line:
                       continue

                   try:
                       data = json.loads(line.decode("utf-8"))
                   except json.JSONDecodeError:
                       continue

                   message = data.get("message", {})
                   content = message.get("content", "")
                   if content:
                       if t_primeiro_token is None:
                           t_primeiro_token = time.monotonic()
                       partes_texto.append(content)

                   if data.get("done") is True:
                       eval_count = int(data.get("eval_count") or 0)
   ```

3. Localize o final do método:
   ```python
           duracao = max(time.monotonic() - inicio, 1e-9)
           tokens_por_segundo = (eval_count / duracao) if eval_count else 0.0
           return "".join(partes_texto), tool_call_final, eval_count, tokens_por_segundo
   ```
   Substitua por:
   ```python
           fim = time.monotonic()
           ttft_ms = ((t_primeiro_token - inicio) * 1000) if t_primeiro_token is not None else None

           LIMIAR_MIN_DECODE_S = 0.01  # abaixo disso, a medição não é confiável
           duracao_decode = (fim - t_primeiro_token) if t_primeiro_token is not None else (fim - inicio)

           if eval_count and duracao_decode >= LIMIAR_MIN_DECODE_S:
               tokens_por_segundo = eval_count / duracao_decode
           else:
               tokens_por_segundo = 0.0

           return "".join(partes_texto), tool_call_final, eval_count, tokens_por_segundo, ttft_ms
   ```

**Arquivo:** `benchmark/runners/maria_runner.py`

4. Localize `_enviar_com_retry`:
   ```python
                   metodo_metricas = getattr(self.cliente, "chat_com_tools_stream_com_metricas", None)
                   if callable(metodo_metricas):
                       resposta_textual, tool_call_final, tokens_gerados, tokens_por_segundo = (
                           metodo_metricas(
                               mensagem_usuario=task.user_message,
                               historico=historico,
                               tools=TOOLS_SCHEMA,
                           )
                       )
                       return resposta_textual, tool_call_final, tokens_gerados, tokens_por_segundo

                   resposta_textual = ""
                   tool_call_final = None
                   for chunk, tool_chunk in self.cliente.chat_com_tools_stream(
                       mensagem_usuario=task.user_message,
                       historico=historico,
                       tools=TOOLS_SCHEMA,
                   ):
                       if chunk is not None:
                           resposta_textual += chunk
                       if tool_chunk is not None:
                           tool_call_final = tool_chunk
                   return resposta_textual, tool_call_final, 0, 0.0
   ```
   Substitua por:
   ```python
                   metodo_metricas = getattr(self.cliente, "chat_com_tools_stream_com_metricas", None)
                   if callable(metodo_metricas):
                       resposta_textual, tool_call_final, tokens_gerados, tokens_por_segundo, ttft_ms = (
                           metodo_metricas(
                               mensagem_usuario=task.user_message,
                               historico=historico,
                               tools=TOOLS_SCHEMA,
                           )
                       )
                       return resposta_textual, tool_call_final, tokens_gerados, tokens_por_segundo, ttft_ms

                   resposta_textual = ""
                   tool_call_final = None
                   for chunk, tool_chunk in self.cliente.chat_com_tools_stream(
                       mensagem_usuario=task.user_message,
                       historico=historico,
                       tools=TOOLS_SCHEMA,
                   ):
                       if chunk is not None:
                           resposta_textual += chunk
                       if tool_chunk is not None:
                           tool_call_final = tool_chunk
                   return resposta_textual, tool_call_final, 0, 0.0, None
   ```

5. Localize, em `run()`:
   ```python
           try:
               resposta_textual, tool_call_final, tokens_gerados, tokens_por_segundo = self._enviar_com_retry(sessao, task)
   ```
   Substitua por:
   ```python
           try:
               resposta_textual, tool_call_final, tokens_gerados, tokens_por_segundo, ttft_ms = self._enviar_com_retry(sessao, task)
   ```

6. Na construção final de `MariaTaskResult(...)` dentro de `run()`, adicione `ttft_ms=ttft_ms,`.

   Atenção: nos blocos `except` de `run()` que capturam erro antes de `_enviar_com_retry` retornar (`PermissionError, OSError, ValueError, TimeoutError`, `OllamaClientError`, `Exception`), `ttft_ms` pode não estar definido. Adicione `ttft_ms = None` junto às demais inicializações no topo de `run()` (ao lado de `tokens_gerados = 0` e `tokens_por_segundo = 0.0`), para garantir que a variável sempre exista antes do `finally`/retorno.

**Arquivo:** `benchmark/tasks/task_schema.py`

7. Em `MariaTaskResult`, adicione (junto ao campo `args_correct` do item 1.2):
   ```python
       ttft_ms: float | None = None
   ```

**Arquivo:** `benchmark/analysis/metrics.py`

8. Localize o dataclass `MariaBenchmarkMetrics` e adicione campos ao final:
   ```python
       args_accuracy: float = 1.0
       avg_ttft_ms: float | None = None
       p50_latency_ms: float = 0.0
       p90_latency_ms: float = 0.0
   ```

9. Localize:
   ```python
   def calculate_maria_metrics(results: list[MariaTaskResult]) -> MariaBenchmarkMetrics:
       total = len(results)
       if not total:
           return MariaBenchmarkMetrics(0, 0, 0, 0, 0, 0, {}, 0.0, 0.0)
   ```
   Substitua por (também corrige um desalinhamento posicional pré-existente nesse retorno, em que `by_category` recebia `0.0` em vez de `{}` quando a lista de resultados está vazia):
   ```python
   def calculate_maria_metrics(results: list[MariaTaskResult]) -> MariaBenchmarkMetrics:
       total = len(results)
       if not total:
           return MariaBenchmarkMetrics(
               total_tasks=0,
               tool_accuracy=0.0,
               confirmation_success_rate=0.0,
               keyword_match_rate=0.0,
               runtime_success_rate=0.0,
               avg_latency_ms=0.0,
               error_distribution={},
               by_category={},
           )
   ```

10. Localize:
    ```python
        avg_tokens_por_segundo = (
            sum(result.tokens_por_segundo for result in results) / total
            if total else 0.0
        )

        return MariaBenchmarkMetrics(
    ```
    Substitua por:
    ```python
        tokens_medidos = [r.tokens_por_segundo for r in results if r.tokens_por_segundo > 0]
        avg_tokens_por_segundo = sum(tokens_medidos) / len(tokens_medidos) if tokens_medidos else 0.0

        ttft_medidos = [r.ttft_ms for r in results if r.ttft_ms is not None]
        avg_ttft_ms = sum(ttft_medidos) / len(ttft_medidos) if ttft_medidos else None

        latencias = sorted(r.latency_ms for r in results)
        p50_latency_ms = statistics.median(latencias)
        p90_latency_ms = (
            statistics.quantiles(latencias, n=10)[8] if len(latencias) >= 2 else latencias[0]
        )

        return MariaBenchmarkMetrics(
    ```

11. Dentro da mesma chamada de `MariaBenchmarkMetrics(...)`, adicione:
    ```python
            args_accuracy=sum(result.args_correct for result in results) / total,
            avg_ttft_ms=avg_ttft_ms,
            p50_latency_ms=p50_latency_ms,
            p90_latency_ms=p90_latency_ms,
    ```

12. Em `aggregate_by_task`, localize:
    ```python
        tokens_por_segundo = [r.tokens_por_segundo for r in resultados]
        tokens_gerados = [r.tokens_gerados for r in resultados]
    ```
    Substitua por:
    ```python
        tokens_medidos = [r.tokens_por_segundo for r in resultados if r.tokens_por_segundo > 0]
        tokens_gerados = [r.tokens_gerados for r in resultados]
    ```
    E localize:
    ```python
            avg_tokens_por_segundo=sum(tokens_por_segundo) / n,
    ```
    Substitua por:
    ```python
            avg_tokens_por_segundo=sum(tokens_medidos) / len(tokens_medidos) if tokens_medidos else 0.0,
    ```

**Arquivo:** `benchmark/analysis/report.py`

13. Localize:
    ```python
    | Taxa de conformidade de idioma | {metrics.language_compliance_rate * 100:.1f}% |
    | Tokens por segundo (média) | {metrics.avg_tokens_por_segundo:.1f} tok/s |
    | Latência média | {metrics.avg_latency_ms:.1f} ms |
    ```
    Substitua por:
    ```python
    | Taxa de conformidade de idioma | {metrics.language_compliance_rate * 100:.1f}% |
    | Acurácia de argumentos | {metrics.args_accuracy * 100:.1f}% |
    | Tokens por segundo (média) | {metrics.avg_tokens_por_segundo:.1f} tok/s |
    | TTFT médio (1º token) | {f"{metrics.avg_ttft_ms:.1f} ms" if metrics.avg_ttft_ms is not None else "N/D"} |
    | Latência p50 | {metrics.p50_latency_ms:.1f} ms |
    | Latência p90 | {metrics.p90_latency_ms:.1f} ms |
    | Latência média | {metrics.avg_latency_ms:.1f} ms |
    ```

**Arquivo:** `benchmark/compare_runs.py`

14. Localize `METRIC_LABELS` e adicione (sem incluir `avg_ttft_ms`, pois pode ser `None` e a rotina atual de comparação não trata esse caso — tratar `None` fica para uma iteração futura, se necessário):
    ```python
    METRIC_LABELS = {
        "tool_accuracy": "Tool accuracy",
        "confirmation_success_rate": "Confirmation success rate",
        "keyword_match_rate": "Keyword match rate",
        "runtime_success_rate": "Runtime success rate",
        "avg_latency_ms": "Average latency (ms)",
        "args_accuracy": "Args accuracy",
        "p50_latency_ms": "P50 latency (ms)",
        "p90_latency_ms": "P90 latency (ms)",
    }
    ```

**Novos testes** — adicionar/alterar em `tests/test_maria.py`:

Atualize `test_chat_com_tools_stream_com_metricas_acumula_tokens`:
```python
    def test_chat_com_tools_stream_com_metricas_acumula_tokens(self):
        class FakeResponse:
            def __init__(self, payloads):
                self.payloads = payloads

            def iter_lines(self):
                for payload in self.payloads:
                    time.sleep(0.03)
                    yield payload

        client = OllamaClient(timeout=10)
        client._make_request = lambda payload, stream=False: FakeResponse([
            json.dumps({"message": {"content": "Olá "}}).encode("utf-8"),
            json.dumps({"message": {"content": "mundo"}, "done": True, "eval_count": 15}).encode("utf-8"),
        ])

        texto, tool_call, tokens_gerados, tokens_por_segundo, ttft_ms = client.chat_com_tools_stream_com_metricas(
            "teste",
            historico=None,
            tools=None,
        )

        self.assertEqual(texto, "Olá mundo")
        self.assertEqual(tokens_gerados, 15)
        self.assertGreater(tokens_por_segundo, 0)
        self.assertIsNotNone(ttft_ms)
        self.assertGreaterEqual(ttft_ms, 0)
        self.assertIsNone(tool_call)
```
(Adicione `import time` no topo de `tests/test_maria.py` caso ainda não esteja importado.)

Novo teste, na mesma classe:
```python
    def test_chat_com_tools_stream_com_metricas_guarda_contra_duracao_irreal(self):
        """Reproduz o padrão observado em produção (eval_count alto, duração
        quase nula) e garante que tokens_por_segundo não retorna um valor
        fisicamente implausível."""
        class FakeResponse:
            def __init__(self, payloads):
                self.payloads = payloads

            def iter_lines(self):
                yield from self.payloads

        client = OllamaClient(timeout=10)
        client._make_request = lambda payload, stream=False: FakeResponse([
            json.dumps({
                "message": {"content": "resposta completa em um único chunk"},
                "done": True,
                "eval_count": 400,
            }).encode("utf-8"),
        ])

        _, _, tokens_gerados, tokens_por_segundo, ttft_ms = client.chat_com_tools_stream_com_metricas(
            "teste", historico=None, tools=None,
        )

        self.assertEqual(tokens_gerados, 400)
        self.assertEqual(tokens_por_segundo, 0.0)
        self.assertIsNotNone(ttft_ms)
```

**Critérios de aceite:**
- [ ] `chat_com_tools_stream_com_metricas` retorna 5 valores; todos os chamadores atualizados (`maria_runner.py`, testes).
- [ ] O padrão exato observado em produção (eval_count alto, duração ~0) não gera mais `tokens_por_segundo` acima de um valor fisicamente plausível — novo teste de guarda passa.
- [ ] `MariaBenchmarkMetrics` expõe `args_accuracy`, `avg_ttft_ms`, `p50_latency_ms`, `p90_latency_ms`; caso de lista vazia não quebra mais o tipo de `by_category`.
- [ ] `report.md` exibe as novas linhas.
- [ ] `python -m unittest tests.test_maria -v` sem regressão.
- [ ] `python -m py_compile core/ollama_client.py benchmark/runners/maria_runner.py benchmark/tasks/task_schema.py benchmark/analysis/metrics.py benchmark/analysis/report.py benchmark/compare_runs.py tests/test_maria.py` sem erros.

### 1.4 Percentis de latência (p50/p90)

Já incorporado nas instruções 8–11 da seção 1.3 (mesmo dataclass/função). Nenhuma ação adicional.

---

## Fase 2 — Modelo, RAG e Fine-tuning

*(Conteúdo do guia `guia-otimizacao-maria-rag-modelo-finetuning.md`, já validado e entregue anteriormente, incorporado aqui sem alterações de conteúdo.)*

### Resumo das decisões

| Item | Decisão | Ação |
|---|---|---|
| RAG vetorial (embeddings + banco vetorial) | Não implementar agora | Registrado como decisão (2.1) |
| Troca de modelo (`qwen2.5:7b` → `qwen3:8b`) | Testar via benchmark A/B | Executar agora (2.2) — pode usar a flag `-m` da Fase 0.2 em vez de variável de ambiente, se a Fase 0 já estiver aplicada |
| Fine-tuning (QLoRA do modelo atual) | Próxima etapa, condicionada aos resultados de 2.2 | Plano registrado, não executar agora (2.3) |

### 2.1 RAG vetorial: decisão de não implementar agora

**Justificativa:** a MARIA já implementa retrieval sob demanda via `core/tools_schema.py` (`listar_arquivos`, `resumir_documento`) e `core/file_utils.py`, sem modelo de embeddings residente nem banco vetorial — um padrão consistente com retrieval agêntico (Yao et al., *ReAct*, ICLR 2023) e mais simples que RAG clássico (Lewis et al., *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks*, NeurIPS 2020).

Introduzir um índice vetorial agora adicionaria uma dependência nova sem um problema real que a justifique: o volume de arquivos e o limite de leitura já existente (`MAX_CHARS_LEITURA = 6000`, `core/config.py`) ainda não configuram um gargalo demonstrado no benchmark atual.

**Condição de reavaliação:** reabrir esta decisão somente se surgir uso real de dezenas/centenas de documentos simultâneos, com evidência de que a MARIA falha em localizar informação relevante usando as ferramentas atuais. Nenhuma ação de código.

### 2.2 Teste A/B: `qwen2.5:7b` vs `qwen3:8b`

**Contexto:** `core/config.py` já lê o modelo via variável de ambiente (`OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")`), e `core/ollama_client.py` usa esse valor como default de `OllamaClient.__init__`. Isso permite testar outro modelo sem alterar código, apenas definindo a variável de ambiente antes de rodar o benchmark (ou, se a Fase 0.2 já foi aplicada, usando `-m` diretamente na CLI interativa para validação exploratória — o benchmark em si continua controlado por variável de ambiente, pois `benchmark/run_benchmark.py` não expõe flag de modelo).

Levantamentos independentes de 2026 (Local AI Master, *Best Local LLMs for Tool & Function Calling*, jun/2026; PromptQuorum, *Best Local Models for Tool Calling in 2026*, jun/2026) indicam a família Qwen3 como a mais estável para tool calling local em 2026, com menor taxa de chamadas de ferramenta descartadas/JSON inválido — superando, na prática atual, modelos especializados de 2024 como o Llama-3-Groq-8B-Tool-Use (89,06% no BFCL; MarkTechPost, jul/2024 — referência histórica, não mais estado da arte). As mesmas fontes de 2026 confirmam que `qwen2.5:7b` (modelo atual da MARIA) "ainda funciona bem para tool calling" — este teste é uma tentativa de melhoria incremental, não a correção de um modelo inadequado.

Tamanho de download do `qwen3:8b`: ~5,2 GB (Webscraft, *Best Ollama Model for Tool Calling Agent 2026*, jun/2026) — confirme espaço em disco antes de baixar.

**Risco a verificar antes do teste:** o Qwen3 suporta modo de "thinking" (raciocínio em bloco oculto antes da resposta/tool call), conforme as mesmas fontes de 2026. Em CPU, isso pode aumentar significativamente a latência e distorcer a comparação com o `qwen2.5:7b` (que não tem esse modo). Antes de rodar o benchmark, consulte a documentação atual do Ollama (`docs.ollama.com`) para verificar se há, na versão instalada, um parâmetro de controle desse modo, e mantenha-o desativado para uma comparação justa. Registre no relatório final se essa configuração pôde ou não ser controlada.

**Instruções:**

1. Verifique espaço em disco disponível (mínimo ~6 GB livres).
2. Baixe o modelo: `ollama pull qwen3:8b`
3. Confirme instalação: `ollama list`
4. Garanta um run de baseline recente com `qwen2.5:7b` (25 tarefas × `BENCHMARK_REPETICOES`). Se não houver, gere um: `python -m benchmark.run_benchmark --tasks 25`. Anote o diretório como `BASELINE_DIR`.
5. Defina a variável de ambiente e rode o mesmo conjunto, sem alterar código:
   - Windows (cmd): `set OLLAMA_MODEL=qwen3:8b` então `python -m benchmark.run_benchmark --tasks 25`
   - Linux/macOS: `OLLAMA_MODEL=qwen3:8b python -m benchmark.run_benchmark --tasks 25`
   Anote o diretório como `QWEN3_DIR`.
6. Compare: `python -m benchmark.compare_runs --before BASELINE_DIR --after QWEN3_DIR` (gera `comparison.md` em `QWEN3_DIR`).
7. Restaure a variável de ambiente para não afetar o uso normal da MARIA fora do benchmark.

**Critérios de decisão** (avaliar após o passo 6) — adotar `qwen3:8b` como novo padrão em `core/config.py` **somente se todos** forem verdadeiros no `comparison.md`:
- `tool_accuracy` igual ou superior ao baseline;
- `confirmation_success_rate` igual ou superior ao baseline;
- `avg_latency_ms` não superior ao baseline em mais de 15%;
- Nenhuma nova falha de idioma introduzida.

Se qualquer critério falhar, manter `qwen2.5:7b` e registrar o resultado — nenhuma reversão de código é necessária, pois nenhuma alteração foi feita.

**Se aprovado**, única alteração de código autorizada nesta etapa — arquivo `core/config.py`:
```python
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:8b")
```

**Critérios de aceite:**
- [ ] `ollama list` mostra `qwen3:8b` instalado.
- [ ] Existe `BASELINE_DIR` e `QWEN3_DIR`, cada um com `log.json` e `report.md` de 25 tarefas.
- [ ] `comparison.md` gerado e revisado contra os 4 critérios de decisão.
- [ ] Decisão registrada por escrito com os números do `comparison.md` como evidência.
- [ ] Se adotado: `core/config.py` alterado apenas na linha do default de `OLLAMA_MODEL`; `python -m py_compile core/config.py` sem erros.

### 2.3 Fine-tuning: plano para próxima etapa (não executar agora)

**Por que não agora:** QLoRA (Dettmers et al., *QLoRA: Efficient Finetuning of Quantized LLMs*, NeurIPS 2023) depende de quantização NF4 via `bitsandbytes`, um stack desenhado e otimizado para GPU CUDA; não há suporte nativo eficiente para esse fluxo em CPU no ecossistema padrão usado pelo Ollama/Hugging Face. Treinar localmente na máquina atual (CPU-only) não é viável em tempo prático — condição de infraestrutura, não de prioridade.

**Quando executar:** após a Etapa 2.2 (teste de modelo) e após confirmar, via novo benchmark, que as correções de schema/idioma já feitas não foram suficientes para eliminar as falhas recorrentes observadas nos benchmarks anteriores.

**Plano (embasado nos próprios dados da MARIA):**

1. **Dataset semente a partir do `log.json` real do benchmark**, não de dados sintéticos externos: cada execução já registra `task_id`, mensagem do usuário, `raw_tool_args` e `final_message`. Casos de falha já documentados (campo obrigatório vazio, resposta parcialmente em inglês, tool call vazada como texto) entram como exemplos negativos corrigidos manualmente. Para ampliar o conjunto, usar o próprio modelo para gerar variações a partir dos casos reais, com curadoria manual antes de treinar — auto-instrução (Wang et al., *Self-Instruct: Aligning Language Models with Self-Generated Instructions*, ACL 2023).
2. **Ajuste, não modelo novo:** LoRA (Hu et al., *LoRA: Low-Rank Adaptation of Large Language Models*, ICLR 2022) sobre o modelo vencedor da Etapa 2.2, via QLoRA em GPU externa (Colab/Kaggle, não na máquina local).
3. **Exportação e validação:** converter o adapter para GGUF, criar modelo local via `ollama create`, e rodar o mesmo `benchmark/run_benchmark.py` contra o modelo ajustado, comparando com `benchmark/compare_runs.py` como na Etapa 2.2.

**Critérios de aceite (quando iniciada):**
- [ ] Dataset construído exclusivamente a partir de execuções reais da MARIA, com origem de cada exemplo rastreável.
- [ ] Treinamento realizado fora da máquina local (Colab/Kaggle/GPU externa) — nenhuma tentativa de QLoRA em CPU local.
- [ ] Resultado validado via `benchmark/compare_runs.py` contra o baseline vencedor da Etapa 2.2, mesmos critérios de decisão.

---

## Fase 3 — Itens que precisam de definição antes de qualquer especificação

Estes itens do levantamento não são triviais nem têm escopo claro o suficiente para gerar instruções executáveis agora. Cada um precisa de decisões antes da próxima iteração deste guia.

### 3.1 Memória entre sessões / preferências / "castelo mental"

Hoje `core/session_storage.py` persiste o histórico bruto por sessão, e `MariaController.finalizar()` é um no-op chamado apenas no caminho feliz de `sair`/`exit` — não há consolidação de aprendizados entre sessões, nem gatilho para encerramentos abruptos (`Ctrl+C`/EOF).

Perguntas a responder antes de especificar:
- O que deve ser extraído entre sessões: preferências de estilo, fatos sobre o usuário, resumos de decisões — ou os três?
- Formato de armazenamento: novo módulo dedicado (padrão de `session_storage.py`) ou extensão do que já existe?
- Quando a consolidação dispara: só em `sair`/`exit`, ou também em `Ctrl+C`/EOF (hoje `finalizar()` não é chamado nesses casos — ver `ui_terminal.py`, tratamento de `KeyboardInterrupt`/`EOFError`)?
- Extração via nova chamada ao modelo (resumo automático) ou regras determinísticas?
- Como isso é reinjetado no `SYSTEM_PROMPT` sem inflar o prompt e piorar o TTFT (tema já tratado na Fase 1)?

### 3.2 Interface JavaFX + editor de tabelas + avatar + arrastar-e-soltar

Toda a lógica de negócio atual está em Python (`core/`), consumindo Ollama via HTTP. Uma interface JavaFX exigiria uma camada de comunicação entre os dois processos.

Perguntas a responder antes de especificar:
- Arquitetura de comunicação Python↔Java: processo Python exposto via REST local (ex.: FastAPI), sockets, ou outra abordagem?
- A UI JavaFX substitui `ui_terminal.py` ou convive com o CLI?
- Escopo mínimo viável da primeira versão: só chat + avatar, ou já inclui o editor de tabelas ao vivo?
- Existe preferência de stack já decidida, ou isso também está em aberto?

### 3.3 Tarefas pré-estabelecidas / rotinas diárias

Hoje a MARIA só roda em modo interativo (`python main.py`, loop de chat). Rotinas diárias pressupõem execução não interativa/agendada.

Perguntas a responder antes de especificar:
- Quem dispara a rotina: agendador do SO (cron/Task Scheduler) chamando a MARIA em modo não interativo, ou um processo residente próprio?
- Rotinas podem gerar arquivos automaticamente sem confirmação humana? Isso conflita com a máquina de estado de confirmação atual (`acao_pendente`), que hoje sempre espera resposta do usuário antes de escrever — precisa de uma política explícita para execução autônoma.
- É necessário um modo `--headless`/`--tarefa` antes de qualquer agendamento existir?

### 3.4 Voz (reconhecimento e síntese)

Já registrado no próprio `README.md`, seção "Próximos Passos": *"Integração de voz com Whisper.cpp permanece como recurso futuro."* — alinhado com este apontamento, confirma que já era uma prioridade reconhecida do projeto.

Perguntas a responder antes de especificar:
- Escopo: apenas STT (Whisper.cpp, já citado no projeto) ou também TTS (saída falada)?
- Qual motor de TTS local, mantendo o pilar "100% local, sem internet" do projeto?

---

## Fontes citadas

- LEWIS, P. et al. *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks*. NeurIPS, 2020.
- YAO, S. et al. *ReAct: Synergizing Reasoning and Acting in Language Models*. ICLR, 2023.
- YAO, S. et al. *τ-bench: A Benchmark for Tool-Agent-User Interaction in Real-World Domains*. 2024.
- BARRES, V. et al. *τ²-bench*. 2025.
- LIU, X. et al. *AgentBench: Evaluating LLMs as Agents*. arXiv:2308.03688, 2024.
- LI, M. et al. *API-Bank: A Benchmark for Tool-Augmented LLMs*. 2023.
- YAN, F. et al. *Berkeley Function-Calling Leaderboard (BFCL)*. 2024/2025.
- WANG, Y. et al. *Self-Instruct: Aligning Language Models with Self-Generated Instructions*. ACL, 2023.
- HU, E. J. et al. *LoRA: Low-Rank Adaptation of Large Language Models*. ICLR, 2022.
- DETTMERS, T. et al. *QLoRA: Efficient Finetuning of Quantized LLMs*. NeurIPS, 2023.
- Spheron Blog. *AI Agent Tool Calling Benchmarks on GPU Cloud: BFCL v4, tau-Bench, and Function-Call Latency Optimization*, jun/2026.
- Morph LLM. *AI Agent Evaluation (2026): Metrics, Frameworks, and Production Failures*, jun/2026.
- MarkTechPost. *Groq Releases Llama-3-Groq-70B-Tool-Use and Llama-3-Groq-8B-Tool-Use...*, jul/2024. (referência histórica de BFCL, não recomendação atual)
- Local AI Master. *Best Local LLMs for Tool & Function Calling (2026 Tested)*, jun/2026.
- PromptQuorum. *Best Local Models for Tool Calling in 2026: Benchmarks & Reliability*, jun/2026.
- Webscraft. *Best Ollama Model for Tool Calling Agent 2026: Comparison & Benchmarks*, jun/2026.