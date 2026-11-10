# Tapa Puzzle Solver — CT208

Resolvedor automático para o quebra-cabeça lógico **Tapa**, escrito em Python puro (sem dependências externas). O projeto lê tabuleiros em formato texto/CSV, resolve cada um aplicando um motor de dedução lógica combinado com busca por backtracking, valida a solução encontrada contra as regras do jogo e, opcionalmente, compara o resultado com um gabarito de referência.

## O que é o Tapa

Tapa é um quebra-cabeça de lógica jogado em uma grade. Algumas células contêm **dicas numéricas** e as demais devem ser preenchidas como **pretas** ou **brancas**, respeitando três regras:

1. **Dica como vizinhança**: o número (ou conjunto de números) em uma célula de dica descreve o tamanho dos blocos contíguos de células pretas entre as até 8 células que a rodeiam (incluindo diagonais). Por exemplo, a dica `(2, 3)` significa que, ao redor daquela célula, existe um bloco de 2 células pretas seguidas e outro de 3, separados por pelo menos uma célula branca.
   - A dica `0` indica que **nenhuma** célula vizinha pode ser preta.
   - A dica `?` indica que existe pelo menos uma restrição, mas o valor é desconhecido — a célula fica branca, porém sem contagem exigida.
   - Células de dica nunca podem ser pretas.
2. **Sem blocos 2x2**: não pode existir nenhum quadrado 2x2 totalmente preto no tabuleiro.
3. **Conectividade**: todas as células pretas do tabuleiro devem formar um único grupo conectado (vizinhança ortogonal — cima, baixo, esquerda, direita).

## Como o solver funciona

O código está todo em [`index.py`](index.py), na classe `TapaSolver` e funções auxiliares:

- **`_parse_input`**: lê o tabuleiro em texto (linhas separadas por `\n`, colunas separadas por `,`) e monta a grade interna. Células vazias tornam-se `UNKNOWN` (desconhecidas, a resolver); células com números ou `?` tornam-se `WHITE` (fixas) e alimentam o dicionário `clues`.
- **`apply_deterministic_engine`**: motor de dedução que roda em loop até não haver mais mudanças possíveis. A cada iteração:
  - Verifica blocos 2x2: se 3 das 4 células já são pretas e a 4ª é desconhecida, ela é forçada a branca (evitar o bloco proibido); se as 4 já são pretas, o estado é inválido.
  - Para cada dica, calcula quantas células pretas/desconhecidas existem na vizinhança e deduz: se a soma de pretas + desconhecidas é exatamente o total exigido, todas as desconhecidas tornam-se pretas; se o total exigido já foi atingido só com as pretas confirmadas, as desconhecidas restantes tornam-se brancas.
- **`is_viable_connectivity`**: poda de busca — verifica se as células pretas confirmadas ainda podem, em tese, formar um único grupo conectado (considerando células desconhecidas como pretas em potencial). Se não, o ramo de busca é abandonado.
- **`solve`**: busca por backtracking. Depois de aplicar o motor dedutivo, escolhe a célula desconhecida com mais vizinhos já definidos (heurística para reduzir ramificação), tenta `BLACK` e, se falhar, tenta `WHITE`, desfazendo o estado (`backup_grid`) a cada tentativa.
- **`is_solved`** / **`is_clue_satisfied`**: confirmam que não há mais células desconhecidas, que a conectividade está correta e que cada dica está satisfeita.
- **`validar_regras_tapa`**: validação independente e estrita da matriz final (não reaproveita o estado do solver), usada como fonte de verdade para conferir se a solução gerada realmente respeita todas as regras.
- **`resolver_e_verificar`**: resolve um único arquivo de problema, salva a solução em `solucoes_geradas/<nome>_output_gerado.txt`, valida contra as regras e, se existir um gabarito (`<nome>_sol.txt` ou `<nome>_sol.csv`) na mesma pasta do problema, compara os dois.
- **`testar_dataset_em_lote`**: roda `resolver_e_verificar` para todos os problemas de uma pasta e imprime um relatório de benchmark (taxa de acerto, tempo total, nós de busca visitados, desempenho por tamanho de tabuleiro).

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
- `?` → dica desconhecida.

O gabarito (opcional), quando presente, é um arquivo `<nome>_sol.txt` com uma linha de `0`/`1` por linha do tabuleiro (`1` = preta, `0` = branca) — é o mesmo formato em que o solver salva suas próprias soluções.

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
├── dataset_tapa/         # Tabuleiros de entrada (<id>.txt) e gabaritos (<id>_sol.txt)
├── solucoes_geradas/     # Soluções geradas pelo solver (criado/atualizado a cada execução)
├── LICENSE
└── README.md
```

## Licença

Distribuído sob a licença MIT — veja [LICENSE](LICENSE).
