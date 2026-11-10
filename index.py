import os
import glob
import copy
import sys
import time

sys.stdout.reconfigure(encoding='utf-8')

UNKNOWN = 0
BLACK = 1
WHITE = 2

class TapaSolver:
    def __init__(self, ascii_input):
        self.grid = []
        self.clues = {}
        self.nodes_visited = 0
        self._parse_input(ascii_input)
        
    def _parse_input(self, text):
        # Remove linhas vazias residuais que podem vir do arquivo de texto
        linhas = [linha.strip() for linha in text.strip().split('\n') if linha.strip()]
        self.rows = len(linhas)
        self.cols = max(len(linha.split(',')) for linha in linhas)
        
        for r in range(self.rows):
            linha_grid = []
            colunas = linhas[r].split(',')
            for c in range(self.cols):
                celula = colunas[c].strip() if c < len(colunas) else ""
                
                if celula == '':
                    linha_grid.append(UNKNOWN)
                else:
                    linha_grid.append(WHITE)
                    if celula == '?':
                        self.clues[(r, c)] = ('?',)
                    else:
                        # Extração segura: ignora espaços e converte apenas os caracteres numéricos
                        digitos = tuple(int(x) for x in celula if x.isdigit())
                        if digitos:
                            self.clues[(r, c)] = digitos
                        else:
                            self.clues[(r, c)] = ('?',) # Fallback preventivo
            self.grid.append(linha_grid)

    def apply_deterministic_engine(self):
        mudou = True
        while mudou:
            mudou = False
            for r in range(self.rows - 1):
                for c in range(self.cols - 1):
                    bloco = [(r, c), (r+1, c), (r, c+1), (r+1, c+1)]
                    pretas = sum(1 for br, bc in bloco if self.grid[br][bc] == BLACK)
                    desconhecidas = [(br, bc) for br, bc in bloco if self.grid[br][bc] == UNKNOWN]
                    
                    if pretas == 4: return False 
                    if pretas == 3 and len(desconhecidas) == 1:
                        dr, dc = desconhecidas[0]
                        self.grid[dr][dc] = WHITE
                        mudou = True

            for (r, c), clue in self.clues.items():
                if clue == ('?',): continue
                total_exigido = sum(clue)
                max_bloco = max(clue) if total_exigido > 0 else 0
                
                vizinhos = []
                dirs = [(-1,-1), (-1,0), (-1,1), (0,1), (1,1), (1,0), (1,-1), (0,-1)]
                for dr, dc in dirs:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < self.rows and 0 <= nc < self.cols:
                        vizinhos.append((nr, nc, self.grid[nr][nc]))
                    else:
                        vizinhos.append((nr, nc, WHITE)) 

                pretas = [v for v in vizinhos if v[2] == BLACK]
                desconhecidas = [v for v in vizinhos if v[2] == UNKNOWN]
                
                if len(pretas) > total_exigido: return False
                if len(pretas) + len(desconhecidas) < total_exigido: return False
                    
                estados = [v[2] for v in vizinhos]
                blocos_confirmados = []
                contagem = 0
                for estado in estados:
                    if estado == BLACK:
                        contagem += 1
                    else:
                        if contagem > 0:
                            blocos_confirmados.append(contagem)
                            contagem = 0
                if contagem > 0:
                    if estados[0] == BLACK and blocos_confirmados:
                        blocos_confirmados[0] += contagem
                    else:
                        blocos_confirmados.append(contagem)

                if any(bloco > max_bloco for bloco in blocos_confirmados): return False

                if len(pretas) < total_exigido and (len(pretas) + len(desconhecidas) == total_exigido):
                    for vr, vc, v_estado in desconhecidas:
                        if 0 <= vr < self.rows and 0 <= vc < self.cols:
                            self.grid[vr][vc] = BLACK
                            mudou = True
                            
                if len(pretas) == total_exigido and len(desconhecidas) > 0:
                    for vr, vc, v_estado in desconhecidas:
                        if 0 <= vr < self.rows and 0 <= vc < self.cols:
                            self.grid[vr][vc] = WHITE
                            mudou = True
        return True

    def is_viable_connectivity(self):
        blacks = [(r, c) for r in range(self.rows) for c in range(self.cols) if self.grid[r][c] == BLACK]
        if not blacks: return True
        
        start = blacks[0]
        visited = set()
        stack = [start]
        
        while stack:
            r, c = stack.pop()
            if (r, c) not in visited:
                visited.add((r, c))
                for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < self.rows and 0 <= nc < self.cols:
                        if self.grid[nr][nc] in (BLACK, UNKNOWN) and (nr, nc) not in visited:
                            stack.append((nr, nc))
                            
        for b in blacks:
            if b not in visited:
                return False
        return True

    def check_connectivity(self):
        blacks = [(r, c) for r in range(self.rows) for c in range(self.cols) if self.grid[r][c] == BLACK]
        if not blacks: return True
        visited = set()
        stack = [blacks[0]]
        while stack:
            r, c = stack.pop()
            if (r, c) not in visited:
                visited.add((r, c))
                for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < self.rows and 0 <= nc < self.cols:
                        if self.grid[nr][nc] == BLACK and (nr, nc) not in visited:
                            stack.append((nr, nc))
        return len(visited) == len(blacks)

    def is_clue_satisfied(self, r, c, clue):
        if clue == ('?',): return True
        vizinhos = []
        dirs = [(-1,-1), (-1,0), (-1,1), (0,1), (1,1), (1,0), (1,-1), (0,-1)]
        for dr, dc in dirs:
            nr, nc = r + dr, c + dc
            if 0 <= nr < self.rows and 0 <= nc < self.cols:
                vizinhos.append(self.grid[nr][nc])
            else:
                vizinhos.append(WHITE)
                
        blocos = []
        count = 0
        for i in range(8):
            if vizinhos[i] == BLACK: count += 1
            else:
                if count > 0:
                    blocos.append(count)
                    count = 0
        if count > 0:
            if vizinhos[0] == BLACK and len(blocos) > 0: blocos[0] += count
            else: blocos.append(count)

        if clue == (0,):
            return len(blocos) == 0
        return sorted(blocos) == sorted(list(clue))

    def is_solved(self):
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c] == UNKNOWN: return False
        if not self.check_connectivity(): return False
        for (r, c), clue in self.clues.items():
            if not self.is_clue_satisfied(r, c, clue): return False
        return True

    def solve(self):
        self.nodes_visited += 1
        backup_grid = copy.deepcopy(self.grid)

        if not self.apply_deterministic_engine():
            self.grid = backup_grid
            return False

        if not self.is_viable_connectivity():
            self.grid = backup_grid
            return False

        if self.is_solved():
            return True

        best_r, best_c = -1, -1
        max_neighbors_filled = -1
        
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c] == UNKNOWN:
                    filled_neighbors = 0
                    for dr in [-1, 0, 1]:
                        for dc in [-1, 0, 1]:
                            if dr == 0 and dc == 0: continue
                            nr, nc = r + dr, c + dc
                            if 0 <= nr < self.rows and 0 <= nc < self.cols:
                                if self.grid[nr][nc] != UNKNOWN:
                                    filled_neighbors += 1
                    
                    if filled_neighbors > max_neighbors_filled:
                        max_neighbors_filled = filled_neighbors
                        best_r, best_c = r, c
            
        if best_r == -1:
            self.grid = backup_grid
            return False

        self.grid[best_r][best_c] = BLACK
        if self.solve(): return True
            
        self.grid = copy.deepcopy(backup_grid)
        self.grid[best_r][best_c] = WHITE
        if self.solve(): return True

        self.grid = backup_grid
        return False

    def save_solution_to_file(self, filename="solucao_tapa.txt"):
        with open(filename, 'w', encoding='utf-8') as f:
            for r in range(self.rows):
                linha_formatada = []
                for c in range(self.cols):
                    if self.grid[r][c] == BLACK:
                        linha_formatada.append('1')
                    else:
                        linha_formatada.append('0')
                
                linha_string = "".join(linha_formatada)
                print(linha_string)         
                f.write(linha_string + "\n") 
        print(f"\n[!] A matriz da solução foi salva com sucesso no arquivo: '{filename}'")

def validar_regras_tapa(grid_binario, dicas, linhas, colunas):
    """
    Fonte primária de verdade: valida estritamente a matriz contra o conjunto de regras do Tapa.
    """
    for (r, c) in dicas.keys():
        if grid_binario[r][c] == 1:
            return False, f"Célula de dica em ({r},{c}) foi preenchida como preta."

    for r in range(linhas - 1):
        for c in range(colunas - 1):
            if (grid_binario[r][c] == 1 and grid_binario[r+1][c] == 1 and 
                grid_binario[r][c+1] == 1 and grid_binario[r+1][c+1] == 1):
                return False, f"Bloco 2x2 de células pretas encontrado a partir de ({r},{c})."

    pretas = [(r, c) for r in range(linhas) for c in range(colunas) if grid_binario[r][c] == 1]
    if pretas:
        visitados = set()
        stack = [pretas[0]]
        while stack:
            r, c = stack.pop()
            if (r, c) not in visitados:
                visitados.add((r, c))
                for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < linhas and 0 <= nc < colunas:
                        if grid_binario[nr][nc] == 1 and (nr, nc) not in visitados:
                            stack.append((nr, nc))
        if len(visitados) != len(pretas):
            return False, "As células pretas estão fraturadas em múltiplos grupos (não há conectividade contínua)."

    for (r, c), clue in dicas.items():
        if clue == ('?',): continue
            
        vizinhos = []
        dirs = [(-1,-1), (-1,0), (-1,1), (0,1), (1,1), (1,0), (1,-1), (0,-1)]
        for dr, dc in dirs:
            nr, nc = r + dr, c + dc
            if 0 <= nr < linhas and 0 <= nc < colunas:
                vizinhos.append(grid_binario[nr][nc])
            else:
                vizinhos.append(0) 
                
        blocos_encontrados = []
        count = 0
        for v in vizinhos:
            if v == 1:
                count += 1
            else:
                if count > 0:
                    blocos_encontrados.append(count)
                    count = 0
                    
        if count > 0:
            if vizinhos[0] == 1 and len(blocos_encontrados) > 0:
                blocos_encontrados[0] += count
            else:
                blocos_encontrados.append(count)
                
        if clue == (0,):
            if blocos_encontrados:
                return False, f"Dica {clue} em ({r},{c}) falhou (esperava nenhuma célula preta ao redor). Formação real ao redor: {blocos_encontrados}"
        elif sorted(blocos_encontrados) != sorted(list(clue)):
            return False, f"Dica {clue} em ({r},{c}) falhou. Formação real ao redor: {blocos_encontrados}"

    return True, "Matriz perfeitamente válida sob as regras lógicas."

def localizar_gabarito(caminho_problema):
    """
    Procura um gabarito manual (<nome>_sol.txt ou <nome>_sol.csv) ao lado
    do arquivo de problema, para comparação opcional com a solução gerada.
    """
    pasta = os.path.dirname(caminho_problema)
    nome_base, _ = os.path.splitext(os.path.basename(caminho_problema))
    for sufixo in ("_sol.txt", "_sol.csv"):
        candidato = os.path.join(pasta, f"{nome_base}{sufixo}")
        if os.path.exists(candidato):
            return candidato
    return None

def carregar_grid_solucao(caminho, linhas_esperadas, colunas_esperadas):
    """
    Lê um arquivo de solução/gabarito: uma linha de 0/1 por linha do
    tabuleiro (mesmo formato gravado por save_solution_to_file).
    Retorna (grid, None) ou (None, motivo_do_erro).
    """
    with open(caminho, 'r', encoding='utf-8') as f:
        linhas_arquivo = [linha.strip() for linha in f if linha.strip()]

    if len(linhas_arquivo) != linhas_esperadas:
        return None, (f"esperava {linhas_esperadas} linha(s), mas o arquivo "
                       f"tem {len(linhas_arquivo)}.")

    grid = []
    for i, linha_str in enumerate(linhas_arquivo):
        linha_limpa = linha_str.replace(',', '').replace(' ', '')
        if len(linha_limpa) != colunas_esperadas:
            return None, (f"linha {i} tem {len(linha_limpa)} coluna(s), "
                           f"esperava {colunas_esperadas}.")
        try:
            valores = [int(ch) for ch in linha_limpa]
        except ValueError:
            return None, f"linha {i} contém caracteres fora de 0/1."

        if any(v not in (0, 1) for v in valores):
            return None, f"linha {i} contém valores fora de 0/1."

        grid.append(valores)

    return grid, None

def resolver_e_verificar(caminho_problema, pasta_saida="solucoes_geradas"):
    """
    Resolve um único arquivo de problema e imediatamente testa o resultado:
      1) contra as regras lógicas do Tapa (validar_regras_tapa);
      2) contra um gabarito manual (_sol.txt/_sol.csv), se existir ao lado
         do problema.
    Retorna um dict com o resumo da verificação, usado tanto pelo modo
    individual quanto pelo lote.
    """
    nome_base, ext = os.path.splitext(os.path.basename(caminho_problema))
    if not os.path.exists(pasta_saida):
        os.makedirs(pasta_saida)
    caminho_saida = os.path.join(pasta_saida, f"{nome_base}_output_gerado.txt")

    print(f"Resolvendo: {nome_base}{ext}")

    with open(caminho_problema, 'r', encoding='utf-8') as f:
        conteudo = f.read()

    solver = TapaSolver(conteudo)
    resultado = {
        'nome': f"{nome_base}{ext}",
        'dimensao': (solver.rows, solver.cols),
        'resolvido': False,
        'valido': False,
        'bate_gabarito': None,
        'nodes': 0,
        'tempo': 0.0,
    }

    inicio = time.perf_counter()
    sucesso = solver.solve()
    resultado['tempo'] = time.perf_counter() - inicio
    resultado['nodes'] = solver.nodes_visited

    if not sucesso:
        print(f" -> [ESGOTADO] Nenhuma combinação lógica atende às dicas. O tabuleiro provou-se impossível de ser resolvido de forma válida "
              f"(Busca levou {resultado['nodes']} nós em {resultado['tempo']:.3f}s).")
        print("-" * 50)
        return resultado

    resultado['resolvido'] = True
    solver.save_solution_to_file(caminho_saida)
    grid_binario = [[1 if solver.grid[r][c] == BLACK else 0 for c in range(solver.cols)] for r in range(solver.rows)]
    is_valido, motivo = validar_regras_tapa(grid_binario, solver.clues, solver.rows, solver.cols)
    resultado['valido'] = is_valido

    if is_valido:
        print(f" -> [VALIDADO] Matriz gerada bate com todas as regras do Tapa "
              f"(Busca levou {resultado['nodes']} nós em {resultado['tempo']:.3f}s).")
    else:
        print(f" -> [ERRO DO SOLVER] O algoritmo finalizou a matriz, mas ela quebra as regras lógicas. Motivo: {motivo}")

    caminho_gabarito = localizar_gabarito(caminho_problema)
    if caminho_gabarito:
        grid_gabarito, erro = carregar_grid_solucao(caminho_gabarito, solver.rows, solver.cols)
        if erro:
            print(f" -> [GABARITO INVÁLIDO] '{os.path.basename(caminho_gabarito)}': {erro}")
        else:
            bate = grid_binario == grid_gabarito
            resultado['bate_gabarito'] = bate
            if bate:
                print(f" -> [GABARITO] Solução gerada é idêntica ao gabarito '{os.path.basename(caminho_gabarito)}'.")
            else:
                print(f" -> [GABARITO] Solução gerada DIFERE do gabarito '{os.path.basename(caminho_gabarito)}' (pode haver mais de uma solução válida).")

    print("-" * 50)
    return resultado

def testar_dataset_em_lote(pasta_dataset="dataset_tapa", pasta_saida="solucoes_geradas"):
    if not os.path.isdir(pasta_dataset):
        print(f"Pasta '{pasta_dataset}' não encontrada (ou não é um diretório).")
        return

    arquivos = glob.glob(os.path.join(pasta_dataset, "*.*"))
    arquivos_problema = [f for f in arquivos if not f.endswith(("_sol.txt", "_sol.csv", "output_gerado.txt"))]

    if not arquivos_problema:
        print(f"Nenhum arquivo de problema encontrado na pasta '{pasta_dataset}'.")
        return

    total_geral = 0
    corretos_geral = 0
    bate_gabarito_geral = 0
    com_gabarito_geral = 0
    nodes_total = 0
    tempo_total = 0.0
    benchmark_por_tamanho = {}

    print(f"Iniciando testes em tabuleiros...\n")
    inicio_lote = time.perf_counter()

    for arq_prob in arquivos_problema:
        resultado = resolver_e_verificar(arq_prob, pasta_saida)

        dimensao = resultado['dimensao']
        if dimensao not in benchmark_por_tamanho:
            benchmark_por_tamanho[dimensao] = {'total': 0, 'corretos': 0}

        total_geral += 1
        benchmark_por_tamanho[dimensao]['total'] += 1
        nodes_total += resultado['nodes']
        tempo_total += resultado['tempo']

        if resultado['valido']:
            corretos_geral += 1
            benchmark_por_tamanho[dimensao]['corretos'] += 1

        if resultado['bate_gabarito'] is not None:
            com_gabarito_geral += 1
            if resultado['bate_gabarito']:
                bate_gabarito_geral += 1

    tempo_parede = time.perf_counter() - inicio_lote

    print("\n" + "=" * 50)
    print("RELATÓRIO DE BENCHMARK FINAL".center(50))
    print("=" * 50)

    taxa_global = (corretos_geral / total_geral) * 100 if total_geral > 0 else 0
    print(f"DESEMPENHO GERAL:")
    print(f"Tabuleiros logicamente validados: {corretos_geral} / {total_geral} ({taxa_global:.2f}%)")
    if com_gabarito_geral > 0:
        taxa_gabarito = (bate_gabarito_geral / com_gabarito_geral) * 100
        print(f"Soluções idênticas ao gabarito: {bate_gabarito_geral} / {com_gabarito_geral} ({taxa_gabarito:.2f}%)")
    print("-" * 50)
    print(f"TEMPO DE EXECUÇÃO:")
    print(f"Tempo total de busca (soma de solve() por tabuleiro): {tempo_total:.3f}s")
    print(f"Tempo de parede do lote completo: {tempo_parede:.3f}s")
    print(f"Total de nós gerados pela busca: {nodes_total}")
    if total_geral > 0:
        print(f"Média de nós por tabuleiro: {nodes_total / total_geral:.1f}")
    print("-" * 50)

    print("DESEMPENHO POR PROPORÇÃO (LINHAS x COLUNAS):")
    for dim, stats in sorted(benchmark_por_tamanho.items()):
        total_cat = stats['total']
        corretos_cat = stats['corretos']
        taxa_cat = (corretos_cat / total_cat) * 100 if total_cat > 0 else 0
        print(f"Tamanho {dim[0]}x{dim[1]}: {corretos_cat} / {total_cat} corretos ({taxa_cat:.2f}%)")
    print("=" * 50 + "\n")

def main():
    if len(sys.argv) == 2:
        resolver_e_verificar(sys.argv[1])
    elif len(sys.argv) == 1:
        testar_dataset_em_lote(pasta_dataset="dataset_tapa", pasta_saida="solucoes_geradas")
    else:
        print("Uso:")
        print("  python index.py                 -> resolve e verifica todo o 'dataset_tapa/'")
        print("  python index.py <problema.txt>  -> resolve e verifica um único problema")
        sys.exit(1)

if __name__ == "__main__":
    main()
