# Princípios de Engenharia de Software — Guia de Referência

**Versão:** 1.0
**Data:** 2026-09-08
**Escopo:** Documento genérico e reutilizável, sem acoplamento a nenhum projeto específico. Serve como referência para avaliação de qualquer decisão de design ou implementação.

---

## Como usar este documento

Para cada nova classe, módulo ou funcionalidade, pergunte:

> *"Isso é simples? (KISS) É realmente necessário agora? (YAGNI) Eu já escrevi isso em outro lugar? (DRY) Isso pertence a essa camada? (SoC) Uma subclasse/implementação minha quebraria o contrato da abstração? (LSP)"*

Estes princípios **competem entre si** com frequência (ex.: OCP pede abstração, YAGNI pede não abstrair antes da hora). Quando entram em tensão, a decisão deve ser resolvida com **dado empírico** (frequência de mudança, tamanho real do problema), não por preferência estética. Isso é explicitado em cada seção onde a tensão é relevante.

---

## 1. Princípios Fundamentais de Simplicidade

### 1.1 KISS — Keep It Simple, Stupid

A solução mais simples que resolve o problema é, na maioria dos casos, a melhor: mais fácil de ler, modificar e depurar, com menos superfície para bugs.

> Origem histórica: o termo é atribuído a Kelly Johnson, engenheiro-chefe da Lockheed Skunk Works, no contexto de engenharia de sistemas aeronáuticos (décadas de 1960); popularizado depois em engenharia de software.

### 1.2 YAGNI — You Aren't Gonna Need It

Não implemente funcionalidade especulativa. Só construa o que resolve uma necessidade real e presente.

> Origem: cunhado no contexto de Extreme Programming (XP) por Ron Jeffries, junto com Kent Beck e Ward Cunningham, nos anos 1990.

**YAGNI não é preguiça — é uma aposta calculada:** o custo de construir algo cedo demais (manutenção de código não usado, abstração errada que precisa ser desfeita) tende a ser maior do que o custo de adicionar depois, quando a necessidade real é conhecida.

---

## 2. DRY — Don't Repeat Yourself

> "Every piece of knowledge must have a single, unambiguous, authoritative representation within a system."
> — HUNT, A.; THOMAS, D. *The Pragmatic Programmer*. Addison-Wesley, 1999.

Se a mesma regra de negócio, string ou lógica está duplicada em múltiplos lugares, qualquer mudança futura corre o risco de atualizar um lugar e esquecer o outro — a causa mais comum de bugs de inconsistência silenciosa.

**Cuidado com o excesso de DRY:** duplicação acidental de duas coisas que *parecem* iguais hoje mas representam conceitos diferentes do domínio, quando forçada a compartilhar uma única implementação, pode criar acoplamento indevido. DRY é sobre conhecimento único, não sobre eliminar toda repetição textual.

---

## 3. SoC — Separation of Concerns

Divida o sistema em seções distintas, cada uma resolvendo uma preocupação específica (interface, regra de negócio, persistência, etc.), evitando que um único módulo misture responsabilidades de naturezas diferentes.

> Origem: o termo é atribuído a Edsger W. Dijkstra, no ensaio "On the role of scientific thought" (1974).

Este princípio é a base conceitual de arquiteturas em camadas (N-tier, Hexagonal, Clean Architecture).

---

## 4. Princípios SOLID (Relevantes ao Dia a Dia)

Dos cinco princípios SOLID, quatro têm aplicação direta e frequente no trabalho cotidiano:

### 4.1 S — SRP (Single Responsibility Principle)

Uma classe/módulo deve ter apenas um motivo para mudar.

> MARTIN, R. C. *Agile Software Development: Principles, Patterns, and Practices*. Prentice Hall, 2002. (Formalização atribuída a Robert C. Martin, com origem conceitual em ideias de Tom DeMarco e David Parnas sobre coesão de módulos.)

**Nuance importante:** SRP não é sobre "fazer uma classe pequena" — é sobre eixos de mudança. Uma classe pode orquestrar múltiplas dependências abstratas (satisfazendo DIP) e ainda assim violar SRP, se ela é o único ponto que muda por múltiplos motivos independentes (ex.: muda porque a regra de confirmação mudou, muda porque o formato de sessão mudou, muda porque uma nova ferramenta foi adicionada). DIP e SRP são eixos ortogonais — corrigir um não corrige automaticamente o outro.

### 4.2 O — OCP (Open/Closed Principle)

Entidades de software devem estar abertas para extensão, mas fechadas para modificação.

> MEYER, B. *Object-Oriented Software Construction*. Prentice Hall, 1988 (origem do princípio); popularizado por MARTIN, R. C.

**Tensão com YAGNI:** abstrair uma extensão futura (ex.: um Registry Pattern para permitir novos itens sem tocar em código existente) tem custo de complexidade imediata. A decisão de aplicar OCP antecipadamente deve ser justificada por evidência de que a mudança é frequente ou iminente — não por precaução genérica. Quando a frequência de mudança é desconhecida ou baixa, prefira a solução simples (`if/elif`, por exemplo) até que dados mostrem o contrário.

### 4.3 L — LSP (Liskov Substitution Principle)

Objetos de um supertipo devem poder ser substituídos por objetos de qualquer um de seus subtipos sem alterar a corretude do programa — não apenas a assinatura dos métodos deve bater, mas o **contrato comportamental** (pré-condições não podem ser fortalecidas, pós-condições não podem ser enfraquecidas, invariantes devem ser preservadas).

> LISKOV, B. *Data Abstraction and Hierarchy*. Palestra convidada, OOPSLA, 1987. Formalização posterior: LISKOV, B.; WING, J. M. *A Behavioral Notion of Subtyping*. ACM Transactions on Programming Languages and Systems (TOPLAS), 1994.

**Por que importa na prática, além da herança clássica:** o princípio se aplica igualmente a tipagem estrutural (ex.: `typing.Protocol` em Python, interfaces implícitas). Qualquer implementação concreta de uma abstração deve ser verdadeiramente intercambiável — inclusive quanto a exceções levantadas, efeitos colaterais e tempo de execução esperado, não só quanto à assinatura de método. Um mock de teste que "engana" o tipo mas se comporta de forma incompatível com a implementação real é uma violação sutil e comum de LSP — e é fonte frequente de testes que passam mas não protegem contra regressão real.

### 4.4 D — DIP (Dependency Inversion Principle)

Módulos de alto nível não devem depender de módulos de baixo nível; ambos devem depender de abstrações. Abstrações não devem depender de detalhes; detalhes devem depender de abstrações.

> MARTIN, R. C. *Agile Software Development: Principles, Patterns, and Practices*. Prentice Hall, 2002.

Este é o princípio que fundamenta injeção de dependência e, na prática de tipagem estrutural moderna (Python `typing.Protocol`, interfaces em TypeScript/Rust `trait`), permite trocar uma implementação concreta sem alterar quem a consome.

> Nota: um quinto princípio SOLID, **I — Interface Segregation Principle** (nenhum cliente deveria ser forçado a depender de métodos que não usa; MARTIN, R. C., mesma obra acima), não é detalhado aqui por ter aplicação menos frequente no dia a dia fora de bibliotecas com APIs públicas amplas, mas continua válido como critério de revisão ao desenhar uma interface/Protocol muito grande.

---

## 5. Práticas Pragmáticas do Dia a Dia

### 5.1 Lei de Demeter (Princípio do Menor Conhecimento)

Um objeto não deve conhecer os detalhes internos de outros objetos — "não fale com estranhos".

> HOLLAND, I. *The Law of Demeter*. Northeastern University, 1987 (formulada como parte do projeto Demeter, com Karl Lieberherr).

Código que encadeia acessos através de múltiplos objetos internos (`objeto.parte.subparte.detalhe`) cria acoplamento estrutural: uma mudança em qualquer nível intermediário quebra o consumidor. Prefira expor um método de fachada (`objeto.obterDetalhe()`) que encapsule o caminho interno.

### 5.2 EAFP vs. LBYL

Dois estilos de tratamento de pré-condições, comuns especialmente em Python:

- **LBYL — Look Before You Leap:** checar a condição antes de agir (`if condição: agir()`).
- **EAFP — Easier to Ask Forgiveness than Permission:** tentar agir e tratar a exceção se falhar (`try: agir() except ErroEsperado: ...`).

EAFP é geralmente preferido em Python por dois motivos: (a) evita condições de corrida do tipo TOCTOU (*time-of-check to time-of-use*, ex.: checar existência de um arquivo/pasta e, entre a checagem e a ação, outro processo alterar o estado); (b) é considerado mais idiomático na linguagem. LBYL continua apropriado quando a checagem é barata e o custo de uma exceção (ex.: I/O, rede) é alto.

### 5.3 Regra do Escoteiro (Boy Scout Rule)

"Deixe o código mais limpo do que você o encontrou." Ao tocar em um arquivo para corrigir algo, aproveite para eliminar pequenos débitos técnicos locais (nomenclatura ruim, comentário obsoleto, código morto) — sem expandir o escopo da mudança para uma reforma completa não solicitada.

> Popularizado por MARTIN, R. C. em *Clean Code: A Handbook of Agile Software Craftsmanship*. Prentice Hall, 2008 (prefácio, atribuído à tradição de escotismo).

### 5.4 Otimização Prematura

> "We should forget about small efficiencies, say about 97% of the time: premature optimization is the root of all evil."
> — KNUTH, D. E. *Structured Programming with go to Statements*. ACM Computing Surveys, 1974.

Não otimize desempenho ou uso de recursos antes de medir e comprovar, com dados reais, que aquele trecho específico é de fato um gargalo. Otimizar sem medição tende a: (a) resolver o problema errado, (b) adicionar complexidade sem benefício mensurável, (c) tornar o código mais difícil de entender exatamente no ponto que menos precisava.

---

## 6. Síntese — Checklist Rápido

| Pergunta | Princípio |
|---|---|
| Existe uma solução mais simples que resolve o mesmo problema? | KISS |
| Esta funcionalidade é necessária agora, com um caso de uso real, ou é especulativa? | YAGNI |
| Esta lógica/conhecimento já existe em outro lugar do sistema? | DRY |
| Este módulo está misturando preocupações de naturezas diferentes? | SoC |
| Esta classe muda por mais de um motivo independente? | SRP |
| Adicionar uma nova variação exige modificar código existente, e isso é um problema real hoje? | OCP |
| Uma implementação alternativa desta abstração seria realmente substituível sem quebrar quem a usa? | LSP |
| Este código depende de uma implementação concreta quando poderia depender de uma abstração? | DIP |
| Este código acessa detalhes internos de um objeto através de outro objeto? | Lei de Demeter |
| Estou checando uma condição que pode mudar entre a checagem e o uso? | EAFP vs. LBYL |
| Estou tocando neste arquivo mesmo assim — vale limpar um pequeno débito local? | Escoteiro |
| Tenho dado medido mostrando que isto é um gargalo real? | Otimização Prematura |

---

## 7. Referências

- BECK, K.; JEFFRIES, R.; CUNNINGHAM, W. Princípios de Extreme Programming (YAGNI). 1990s.
- DIJKSTRA, E. W. *On the role of scientific thought*. 1974.
- HOLLAND, I. *The Law of Demeter*. Northeastern University, 1987.
- HUNT, A.; THOMAS, D. *The Pragmatic Programmer*. Addison-Wesley, 1999.
- KNUTH, D. E. *Structured Programming with go to Statements*. ACM Computing Surveys, 6(4), 1974.
- LISKOV, B. *Data Abstraction and Hierarchy*. OOPSLA, 1987.
- LISKOV, B.; WING, J. M. *A Behavioral Notion of Subtyping*. ACM TOPLAS, 1994.
- MARTIN, R. C. *Agile Software Development: Principles, Patterns, and Practices*. Prentice Hall, 2002.
- MARTIN, R. C. *Clean Code: A Handbook of Agile Software Craftsmanship*. Prentice Hall, 2008.
- MEYER, B. *Object-Oriented Software Construction*. Prentice Hall, 1988.
