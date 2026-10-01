import os
import glob
import copy
import sys

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
                    
                estados_anel = [v[2] for v in vizinhos] * 2
                blocos_adjacentes = 0
                for estado in estados_anel:
                    if estado == BLACK:
                        blocos_adjacentes += 1
                        if blocos_adjacentes > max_bloco: return False
                    else:
                        blocos_adjacentes = 0

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
                
        if sorted(blocos_encontrados) != sorted(list(clue)):
            return False, f"Dica {clue} em ({r},{c}) falhou. Formação real ao redor: {blocos_encontrados}"

    return True, "Matriz perfeitamente válida sob as regras lógicas."

def testar_dataset_em_lote(pasta_dataset="dataset_tapa", pasta_saida="solucoes_geradas"):
    if not os.path.exists(pasta_dataset):
        print(f"Pasta '{pasta_dataset}' não encontrada.")
        return

    if not os.path.exists(pasta_saida):
        os.makedirs(pasta_saida)

    arquivos = glob.glob(os.path.join(pasta_dataset, "*.*"))
    arquivos_problema = [f for f in arquivos if not f.endswith(("_sol.txt", "_sol.csv", "output_gerado.txt"))]
    
    if not arquivos_problema:
        print(f"Nenhum arquivo de problema encontrado na pasta '{pasta_dataset}'.")
        return

    total_geral = 0
    corretos_geral = 0
    benchmark_por_tamanho = {}

    print(f"Iniciando testes em tabuleiros...\n")

    for arq_prob in arquivos_problema:
        nome_base, ext = os.path.splitext(os.path.basename(arq_prob))
        caminho_saida = os.path.join(pasta_saida, f"{nome_base}_output_gerado.txt")
        
        print(f"Resolvendo: {nome_base}{ext}")
        
        with open(arq_prob, 'r', encoding='utf-8') as f:
            conteudo = f.read()
            
        solver = TapaSolver(conteudo)
        
        dimensao = (solver.rows, solver.cols)
        if dimensao not in benchmark_por_tamanho:
            benchmark_por_tamanho[dimensao] = {'total': 0, 'corretos': 0}
            
        total_geral += 1
        benchmark_por_tamanho[dimensao]['total'] += 1
        
        sucesso = solver.solve()
        
        if sucesso:
            solver.save_solution_to_file(caminho_saida)
            grid_binario = [[1 if solver.grid[r][c] == BLACK else 0 for c in range(solver.cols)] for r in range(solver.rows)]
            is_valido, motivo = validar_regras_tapa(grid_binario, solver.clues, solver.rows, solver.cols)
            
            if is_valido:
                print(f" -> [VALIDADO] Matriz gerada bate com todas as regras do Tapa (Busca levou {solver.nodes_visited} nós).")
                corretos_geral += 1
                benchmark_por_tamanho[dimensao]['corretos'] += 1
            else:
                print(f" -> [ERRO DO SOLVER] O algoritmo finalizou a matriz, mas ela quebra as regras lógicas. Motivo: {motivo}")
        else:
            print(" -> [ESGOTADO] Nenhuma combinação lógica atende às dicas. O tabuleiro provou-se impossível de ser resolvido de forma válida.")
        print("-" * 50)

    print("\n" + "=" * 50)
    print("RELATÓRIO DE BENCHMARK FINAL".center(50))
    print("=" * 50)
    
    taxa_global = (corretos_geral / total_geral) * 100 if total_geral > 0 else 0
    print(f"DESEMPENHO GERAL:")
    print(f"Tabuleiros logicamente validados: {corretos_geral} / {total_geral} ({taxa_global:.2f}%)")
    print("-" * 50)
    
    print("DESEMPENHO POR PROPORÇÃO (LINHAS x COLUNAS):")
    for dim, stats in sorted(benchmark_por_tamanho.items()): 
        total_cat = stats['total']
        corretos_cat = stats['corretos']
        taxa_cat = (corretos_cat / total_cat) * 100 if total_cat > 0 else 0
        print(f"Tamanho {dim[0]}x{dim[1]}: {corretos_cat} / {total_cat} corretos ({taxa_cat:.2f}%)")
    print("=" * 50 + "\n")

if __name__ == "__main__":
    testar_dataset_em_lote(pasta_dataset="dataset_tapa", pasta_saida="solucoes_geradas")
