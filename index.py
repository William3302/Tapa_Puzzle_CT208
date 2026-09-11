import os
import glob
import copy
import sys

# Força o terminal a aceitar o formato visual UTF-8
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
        """Lê o formato CSV. Células vazias viram UNKNOWN. '24' vira (2,4)."""
        linhas = text.strip().split('\n')
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
                        dicas = tuple(int(x) for x in celula)
                        self.clues[(r, c)] = dicas
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
        """Salva a solução no formato binário contínuo (ex: 000100)."""
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

# ==========================================
# GESTOR DE TESTE EM LOTE
# ==========================================

def testar_dataset_em_lote(pasta_dataset="dataset_tapa"):
    """
    Varre a pasta em busca de instâncias, as resolve e compara com 
    o gabarito _sol correspondente.
    """
    if not os.path.exists(pasta_dataset):
        print(f"Pasta '{pasta_dataset}' não encontrada. Crie a pasta e adicione os arquivos.")
        return

    # Busca todos os arquivos de texto/csv que não terminam com "_sol"
    arquivos = glob.glob(os.path.join(pasta_dataset, "*.*"))
    arquivos_problema = [f for f in arquivos if not f.endswith(("_sol.txt", "_sol.csv"))]
    
    if not arquivos_problema:
        print(f"Nenhum arquivo de problema encontrado na pasta '{pasta_dataset}'.")
        return

    print(f"Iniciando testes em {len(arquivos_problema)} tabuleiros...\n")

    for arq_prob in arquivos_problema:
        nome_base, ext = os.path.splitext(arq_prob)
        arq_sol = f"{nome_base}_sol{ext}"
        
        print(f"Resolvendo: {os.path.basename(arq_prob)}")
        
        with open(arq_prob, 'r', encoding='utf-8') as f:
            conteudo = f.read()
            
        solver = TapaSolver(conteudo)
        sucesso = solver.solve()
        
        if sucesso:
            print(f" -> Sucesso! Resolvido em {solver.nodes_visited} nós.")
            solver.save_solution_to_file(f"{nome_base}_output_gerado{ext}")
            
            # Validação caso o gabarito _sol exista
            if os.path.exists(arq_sol):
                with open(arq_sol, 'r', encoding='utf-8') as f:
                    # Remove quebras de linha e trata a string como uma sequência linear de caracteres
                    gabarito_bruto = f.read().replace('\n', '').strip()
                    gabarito_linear = list(gabarito_bruto)
                    
                # Extrai a solução do solver de forma sequencial
                solucao_linear = []
                for r in range(solver.rows):
                    for c in range(solver.cols):
                        solucao_linear.append('1' if solver.grid[r][c] == BLACK else '0')
                
                # Validação Lógica
                if solucao_linear == gabarito_linear:
                    print(" -> [VERIFICADO] A matriz bate exatamente com o arquivo _sol!")
                else:
                    print(" -> [ERRO] A solução difere do gabarito oficial.")
            else:
                print(" -> [AVISO] Arquivo de gabarito (_sol) não encontrado para verificação.")
        else:
            print(" -> [FALHA] Nenhuma solução válida encontrada.")
        print("-" * 50)

if __name__ == "__main__":
    testar_dataset_em_lote("dataset_tapa")
