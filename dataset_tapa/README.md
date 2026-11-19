# Dataset Tapa

## Origem dos arquivos

- **IDs de 5 caracteres alfanuméricos** (ex: `007z1.txt`): conjunto original do projeto (174 tabuleiros, 6×6 a 12×12).
- **IDs `hfpb_###`** (ex: `hfpb_001.txt`): 385 tabuleiros extraídos do dataset [`bluecoconut/pencil-puzzle-bench`](https://huggingface.co/datasets/bluecoconut/pencil-puzzle-bench) (Hugging Face, licença MIT), subconjunto `pid == "tapa"`.

## Como os puzzles `hfpb_###` foram gerados

1. Os puzzles originais estão codificados como URLs no formato puz.link/pzprjs (`.../tapa/<largura>/<altura>/<corpo>`). O corpo foi decodificado para uma grade de pistas reimplementando o esquema de codificação do `pzprjs`.
2. Cada grade foi convertida para o mesmo formato CSV usado pelo restante do dataset (uma linha por linha do tabuleiro, células separadas por vírgula; `?` representa uma pista de valor desconhecido na codificação original, tratada pelo solver como célula sem restrição).
3. Cada puzzle convertido foi resolvido com o próprio `TapaSolver` deste repositório (limite de 20s por tabuleiro) e a solução foi validada de forma independente com `validar_regras_tapa`.
4. Do total de 653 puzzles "tapa" presentes no dataset original, 385 foram resolvidos e validados dentro do limite de tempo; os demais (268) são tabuleiros muito grandes/irregulares (alguns acima de 40×40) que excederam o timeout de 20s e foram descartados — não entraram no dataset.

Nenhum arquivo do conjunto original (174 tabuleiros) foi alterado.
