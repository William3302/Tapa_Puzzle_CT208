# Tapa Puzzle Solver — CT208

Resolvedor automático para o quebra-cabeça lógico **Tapa**, escrito em Python puro (sem dependências externas). O projeto lê tabuleiros em formato texto/CSV, resolve cada um combinando um motor de dedução lógica com busca por backtracking, valida a solução encontrada de forma independente contra as regras do jogo e, opcionalmente, compara o resultado com um gabarito de referência.

## O que é o Tapa

Tapa é um quebra-cabeça de lógica jogado em uma grade. Algumas células contêm **dicas numéricas** e as demais devem ser preenchidas como **pretas** ou **brancas**, respeitando três regras:

1. **Dica como vizinhança**: o número (ou conjunto de números) em uma célula de dica descreve o tamanho dos blocos contíguos de células pretas entre as até 8 células que a rodeiam (incluindo diagonais). Por exemplo, a dica `(2, 3)` significa que, ao redor daquela célula, existe um bloco de 2 células pretas seguidas e outro de 3, separados por pelo menos uma célula branca.
   - A dica `0` indica que **nenhuma** célula vizinha pode ser preta.
   - A dica `?` indica que existe pelo menos uma restrição, mas o valor é desconhecido — a célula fica branca, porém sem contagem exigida.
   - Células de dica nunca podem ser pretas.
2. **Sem blocos 2x2**: não pode existir nenhum quadrado 2x2 totalmente preto no tabuleiro.
3. **Conectividade**: todas as células pretas do tabuleiro devem formar um único grupo conectado (vizinhança ortogonal — cima, baixo, esquerda, direita).

## Visão geral das técnicas (explicado de forma simples)

O solver combina três ideias complementares. Nenhuma delas sozinha resolveria o Tapa de forma confiável e rápida — é a combinação que funciona:

| Técnica | O que é, em termos simples |
|---|---|
| **Propagação de restrições (motor determinístico)** | Um conjunto de regras que só preenche uma célula quando a resposta é **100% certa** pela lógica das dicas vizinhas — nunca "chuta". Roda em loop até não conseguir mais deduzir nada sozinho. |
| **Busca por backtracking** | Quando a lógica pura empaca (sobra mais de uma possibilidade), o programa "aposta" numa célula, continua resolvendo, e se chegar a uma contradição, **desfaz a aposta** e tenta a cor contrária. É basicamente tentativa e erro organizado, com memória do que já foi tentado. |
| **Heurística de escolha de célula** | Antes de apostar, o solver escolhe a célula desconhecida com **mais vizinhos já definidos** — apostar numa célula "rodeada de informação" tende a gerar contradições (ou confirmações) mais rápido do que apostar numa célula isolada. |
| **Podas (pruning)** | Testes rápidos que **abandonam um caminho de busca sem precisar terminar de explorá-lo**, porque já é possível provar que ele nunca vai dar em solução válida. Cada poda nova reduz a quantidade de "apostas" que o backtracking precisa fazer. |
| **Validação independente** | Depois que o solver "acha" que terminou, uma função separada (`validar_regras_tapa`) reconfere a resposta do zero, sem reaproveitar nenhum estado interno do solver — como um segundo juiz que não confia no primeiro. |

## Como o código funciona

Todo o código está em [`index.py`](index.py), centrado na classe `TapaSolver`:

- **`_parse_input`**: lê o tabuleiro em texto (linhas separadas por `\n`, colunas por `,`) e monta a grade interna. Células vazias tornam-se `UNKNOWN` (a resolver); células com números ou `?` tornam-se `WHITE` fixas e alimentam o dicionário `clues`.

- **`apply_deterministic_engine`** — o motor de propagação. Roda em loop até não haver mais mudanças possíveis (`mudou = False` em todo o corpo). A cada rodada:
  1. **Regra do bloco 2x2**: se 3 das 4 células de um quadrado já são pretas e a 4ª é desconhecida, ela é forçada a branca; se as 4 já são pretas, o estado é logicamente impossível.
  2. **Contagem básica por dica**: se pretas confirmadas + desconhecidas = exatamente o total exigido, todas as desconhecidas tornam-se pretas; se o total já foi atingido só com as pretas confirmadas, as desconhecidas restantes tornam-se brancas.
  3. **Blocos irreconciliáveis**: os vizinhos de uma dica são agrupados em "arcos" separados por uma célula branca confirmada (um branco nunca volta a ser preto, então arcos diferentes nunca vão se fundir). Se já existem mais arcos com pelo menos uma preta do que a dica permite blocos, é impossível.
  4. **Bloco fechado**: um grupo de pretas cujas duas pontas no anel de vizinhos já são brancas confirmadas não pode mais crescer nem encolher — seu tamanho é definitivo e precisa bater exatamente com algum valor da dica (não apenas ser menor ou igual ao maior valor).
  5. **Fechamento saturado (dinâmico)**: nenhum bloco aberto pode crescer além do maior valor da dica que **ainda não foi satisfeito** por um bloco já fechado. Um segmento que atinge esse tamanho tem as pontas forçadas a branco, mesmo que o total geral da dica ainda não tenha sido alcançado.
  6. **Ponte de conectividade obrigatória**: se uma célula desconhecida é a **única rota possível** entre duas células pretas já confirmadas (mesmo supondo que todas as outras desconhecidas virem pretas), ela é forçada a preta — sem ela, a conectividade final seria impossível.

- **`is_viable_connectivity`** — poda usada durante a busca: verifica se as pretas confirmadas ainda *podem*, em tese, formar um único grupo conectado, tratando as desconhecidas como pretas em potencial. Se não, o ramo de busca é abandonado imediatamente.

- **`solve`** — a busca por backtracking propriamente dita:
  1. Aplica o motor determinístico; se ele encontrar uma contradição, desiste do ramo.
  2. Confere a poda de conectividade.
  3. Se o tabuleiro já estiver completo e válido, retorna sucesso.
  4. Senão, escolhe a célula desconhecida com mais vizinhos já definidos, tenta `BLACK`; se a recursão falhar, desfaz (`backup_grid`) e tenta `WHITE`; se as duas falharem, desfaz e retorna fracasso para a chamada anterior.

- **`is_solved` / `is_clue_satisfied`** — confirmam que não há mais células desconhecidas, que a conectividade está correta e que cada dica está satisfeita, usando o estado interno do solver (usado só para decidir quando parar a busca).

- **`validar_regras_tapa`** — validação **independente** e estrita da matriz final, sem reaproveitar nada do estado do solver. É a fonte de verdade usada para conferir se a solução realmente respeita todas as regras, incluindo os casos em que o solver poderia ter um bug silencioso.

- **`resolver_e_verificar`** — resolve um único arquivo de problema, salva a solução em `solucoes_geradas/<nome>_output_gerado.txt`, valida contra as regras e, se existir um gabarito (`<nome>_sol.txt`) na mesma pasta, compara os dois.

- **`testar_dataset_em_lote`** — roda `resolver_e_verificar` para todos os problemas de uma pasta e imprime um relatório de benchmark: taxa de acerto, tempo total, nós de busca visitados e desempenho por tamanho de tabuleiro.

### Formato do arquivo de entrada

Cada tabuleiro é um arquivo de texto com uma linha por linha da grade e colunas separadas por vírgula:

```
3,,,,,,,,1
,,,,24,,,,
,22,113,,,,,,0
,,,,,,22,,2
```

- Célula vazia → a resolver (preta ou branca).
- Número(s) → dica (ex.: `113` é interpretado como a tupla `(1, 1, 3)` — três blocos pretos ao redor, de tamanhos 1, 1 e 3).
- `0` → dica "nenhuma célula preta ao redor".
- `?` → dica desconhecida (sem contagem exigida).

O gabarito (opcional), quando presente, é um arquivo `<nome>_sol.txt` com uma linha de `0`/`1` por linha do tabuleiro (`1` = preta, `0` = branca) — o mesmo formato em que o solver salva suas próprias soluções.

## Evolução do projeto

O projeto cresceu em etapas bem distintas, cada uma resolvendo uma limitação específica da etapa anterior:

1. **Implementação inicial** (`9c6c4bf`, `2b55ca1`) — primeira versão da classe `TapaSolver`: parsing simples, motor determinístico básico, poda de conectividade e busca por backtracking já presentes desde o começo.
2. **Parsing mais simples e saída de solução** (`098ab54`) — o formato de entrada passou de dicas separadas por vírgula dentro da célula (`"2,4"`) para dígitos concatenados (`"24"` → `(2, 4)`), e o solver passou a salvar a solução encontrada em arquivo.
3. **Dataset inicial e documentação** (`ef74903`, `ae94bcf`) — criação da pasta `dataset_tapa/` e primeiras instruções de uso.
4. **Correção de bugs de robustez e validação independente** (`5094125`) — o parser passou a ignorar linhas vazias residuais e a extrair só os caracteres numéricos de cada célula (em vez de assumir que todo caractere era um dígito válido), evitando quebras com arquivos de entrada um pouco "sujos". Essa mesma mudança introduziu `validar_regras_tapa` como verificador independente, já que antes só se confiava no próprio estado final do solver.
5. **Dataset completo e benchmark em lote** (`61b202b`) — todos os 174 tabuleiros originais e seus gabaritos, e relatório de benchmark por tamanho de tabuleiro em `testar_dataset_em_lote`.
6. **Primeira regra de poda proativa** (`f15e365`) — adicionado o "fechamento de bloco saturado": sem ela, o solver descobria por tentativa e erro que um bloco já do tamanho máximo não podia crescer mais; com ela, isso é deduzido direto. Resultado medido no dataset original: **-29% de nós de busca** (293.228 → 207.830), sem tocar na lógica de backtracking.
7. **Ampliação do dataset com puzzles externos** (`be33244`) — importação de 385 tabuleiros do dataset público [`bluecoconut/pencil-puzzle-bench`](https://huggingface.co/datasets/bluecoconut/pencil-puzzle-bench) (Hugging Face, MIT). Os puzzles originais estavam codificados em URLs no formato puz.link/pzprjs; foram decodificados, convertidos para o CSV do projeto, resolvidos pelo próprio `TapaSolver` e validados com `validar_regras_tapa` antes de entrar no repositório (ver [`dataset_tapa/README.md`](dataset_tapa/README.md)).
8. **Motor determinístico mais forte e recuperação de puzzles difíceis** (`8158738`) — quatro regras novas de poda (itens 3 a 6 da lista do motor, acima), todas **sem alterar a heurística de escolha de célula** do backtracking. Isso permitiu recuperar 212 dos 268 tabuleiros do dataset externo que antes excediam o tempo limite.

## Benchmarks

Medido com o motor atual, nos 771 tabuleiros do dataset completo (174 originais + 597 do `pencil-puzzle-bench`):

| | Nós de busca | Tempo de parede |
|---|---|---|
| Antes das 4 regras de poda mais recentes | 2.396.783 | 1092,1s |
| Depois | 114.822 | 208,6s |
| Redução | **-95,2%** | **-80,9%** |

Corretude: **771/771 tabuleiros logicamente válidos** (confirmado por `validar_regras_tapa`, de forma independente do solver).

### Limitação conhecida

Dos 653 puzzles do dataset externo, **56 ainda não são resolvidos** mesmo com o motor atual e um limite de 120s por tabuleiro — em geral tabuleiros grandes e esparsos (17×17 até 44×44, incluindo um de 10×100). Isso não é falta de tempo: um teste sem limite nenhum mostrou que até um tabuleiro pequeno (9×9) pode travar por quase uma hora, porque a busca por backtracking em Python, sem aprendizado de conflito, tem risco real de explosão combinatória em instâncias específicas, independente do tamanho do tabuleiro.

Mais regras de poda escritas à mão (como propagação cruzada entre dicas vizinhas) ainda ajudariam um pouco, mas o ganho marginal cai a cada regra nova. O salto que resolveria esses casos de forma confiável seria trocar a arquitetura de busca por um solver CP-SAT/SAT (ex.: Google OR-Tools), que modela as regras do Tapa como restrições booleanas e usa aprendizado de conflito — uma mudança estrutural, não incremental, que não foi implementada neste projeto.

## Instalação

Requer apenas **Python 3** (nenhuma biblioteca externa é usada).

```bash
git clone https://github.com/William3302/Tapa_Puzzle_CT208.git
cd Tapa_Puzzle_CT208
```

## Como usar

**Resolver todo o dataset em lote** (lê tudo em `dataset_tapa/`, grava as soluções em `solucoes_geradas/` e imprime um relatório final de benchmark):

```bash
python3 index.py
```

**Resolver um único tabuleiro:**

```bash
python3 index.py dataset_tapa/007z1.txt
```

Saída esperada para um problema resolvido com sucesso:

```
Resolvendo: 007z1.txt
011111110
110100100
...
[!] A matriz da solução foi salva com sucesso no arquivo: 'solucoes_geradas/007z1_output_gerado.txt'
 -> [VALIDADO] Matriz gerada bate com todas as regras do Tapa (Busca levou 286 nós em 0.138s).
 -> [GABARITO] Solução gerada é idêntica ao gabarito '007z1_sol.txt'.
```

## Estrutura do projeto

```
Tapa_Puzzle_CT208/
├── index.py              # Solver, validador e CLI
├── dataset_tapa/         # Tabuleiros de entrada (<id>.txt), gabaritos (<id>_sol.txt) e README da origem dos dados
├── solucoes_geradas/     # Soluções geradas pelo solver (criado/atualizado a cada execução)
├── LICENSE
└── README.md
```

## Licença

Distribuído sob a licença MIT — veja [LICENSE](LICENSE).
