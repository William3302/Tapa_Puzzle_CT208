import copy
import sys

# Força o terminal a aceitar o bloco visual do Tapa
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
        linhas = text.strip().split('\n')
        self.rows = len(linhas)
        self.cols = len(linhas[0].split())
        
        for r in range(self.rows):
            linha_grid = []
            colunas = linhas[r].split()
            for c in range(self.cols):
                celula = colunas[c]
                if celula == '.':
                    linha_grid.append(UNKNOWN)
                else:
                    linha_grid.append(WHITE)
                    if celula == '?':
                        self.clues[(r, c)] = ('?',)
                    else:
                        dicas = tuple(int(x) for x in celula.split(','))
                        self.clues[(r, c)] = dicas
            self.grid.append(linha_grid)

    def apply_deterministic_engine(self):
        """Aplica regras absolutas até travar. (Inalterado)"""
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
                max_bloco = max(clue)
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
        """
        NOVO FILTRO: Avalia se ainda é matematicamente possível conectar o mar.
        Se houverem duas áreas pretas que não podem se tocar nem usando
        as casas vazias, corta o galho da árvore na mesma hora.
        """
        blacks = [(r, c) for r in range(self.rows) for c in range(self.cols) if self.grid[r][c] == BLACK]
        if not blacks: return True
        
        # Faz um "Flood Fill" a partir da primeira célula preta,
        # caminhando apenas por células PRETAS ou DESCONHECIDAS.
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
                            
        # Se alguma célula preta existente ficou de fora da área alcançável,
        # significa que o mar foi permanentemente cortado por paredes brancas.
        for b in blacks:
            if b not in visited:
                return False
        return True

    def check_connectivity(self):
        """Verificação estrita de final de jogo (apenas peças pretas)."""
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

        # NOVA PODA: Valida a conectividade das casas que ainda estão vazias
        if not self.is_viable_connectivity():
            self.grid = backup_grid
            return False

        if self.is_solved():
            return True

        # NOVA HEURÍSTICA: Escolhe a célula vazia com mais "informação" em volta (MRV)
        # Isso faz o algoritmo preencher os arredores das dicas primeiro,
        # em vez de chutar aleatoriamente num canto vazio do tabuleiro.
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

        # Tenta Preta primeiro (heurística: em geral, há mais pretas que brancas no mar)
        self.grid[best_r][best_c] = BLACK
        if self.solve(): return True
            
        self.grid = copy.deepcopy(backup_grid)
        self.grid[best_r][best_c] = WHITE
        if self.solve(): return True

        self.grid = backup_grid
        return False

    def print_board(self):
        simbolos = {UNKNOWN: '.', BLACK: '█', WHITE: ' '}
        for r in range(self.rows):
            linha = ""
            for c in range(self.cols):
                if (r, c) in self.clues:
                    dica = ",".join(map(str, self.clues[(r, c)]))
                    linha += f"[{dica:^3}]"
                else:
                    linha += f"  {simbolos[self.grid[r][c]]}  "
            print(linha)

tabuleiro_texto = """
. 5 . . 1,2 . . . . .
. . . . . 1,2,2 3,3 . . 5
. . . . . . . . . .
. 1,3 . . . 7 . . . .
. 1,2,2 . 7 . . . . . 1,1,1
1,2 . . . . . 5 . 2,4 .
. . . . 1,4 . . . 3,3 .
. . . . . . . . . .
5 . . 1,3 1,2,2 . . . . .
. . . . . 1,1 . . 5 .
"""

solver = TapaSolver(tabuleiro_texto)
if solver.solve():
    print(f"Solução encontrada após gerar {solver.nodes_visited} nós de busca!")
    solver.print_board()
else:
    print("Nenhuma solução válida encontrada.")
