"""
Script de verificação de dataset - Versão Portável
"""
import pandas as pd
from pathlib import Path

# Determinar caminho base dinamicamente
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "processed"

# Caminho relativo e portável
file_path = DATA_DIR / "dataset_realista_1m.parquet"

print(f'Verificando arquivo: {file_path}')
print(f'Arquivo existe? {file_path.exists()}')

if not file_path.exists():
    print('\n Arquivo não encontrado!')
    print('\nArquivos disponíveis na pasta:')
    if DATA_DIR.exists():
        for arquivo in DATA_DIR.glob('*.parquet'):
            print(f'  - {arquivo.name}')
    else:
        print(f' Diretório não encontrado: {DATA_DIR}')
    exit()

# Carregar dataset
print('\nCarregando dataset...')
df = pd.read_parquet(file_path, engine='pyarrow')

print('\n=== INFORMAÇÕES DO DATASET ===')
print(f'Total de registros: {len(df):,}')
print(f'\nColunas disponíveis ({len(df.columns)} colunas):')
for i, col in enumerate(df.columns.tolist(), 1):
    print(f'  {i}. {col}')

print(f'\nPrimeiras 3 linhas:')
print(df.head(3))

print(f'\nEstatísticas básicas:')
print(df.describe())

# Verificar coluna de inadimplência
print(f'\n=== PROCURANDO COLUNA DE INADIMPLÊNCIA ===')
colunas_possiveis = ['inadimplente', 'TARGET', 'default', 'bad', 'target', 'Default', 'y', 'label']
coluna_encontrada = None

for col in colunas_possiveis:
    if col in df.columns:
        print(f'\n Coluna encontrada: {col}')
        coluna_encontrada = col
        print(f'Valores únicos: {df[col].unique()}')
        print(f'Contagem de valores:')
        print(df[col].value_counts())
        print(f'Total de inadimplentes (soma): {df[col].sum()}')
        print(f'Taxa de inadimplência (média): {df[col].mean() * 100:.2f}%')
        break

if coluna_encontrada is None:
    print('\n Nenhuma coluna de inadimplência encontrada!')
    print('Colunas disponíveis:', df.columns.tolist())

# Verificar coluna de valor/ticket
print(f'\n=== PROCURANDO COLUNA DE VALOR ===')
colunas_valor = ['ticket', 'valor', 'amount', 'VALOR_EMPRESTIMO', 'loan_amount']
for col in colunas_valor:
    if col in df.columns:
        print(f'\n Coluna de valor encontrada: {col}')
        print(f'Valor médio: R$ {df[col].mean():,.2f}')
        print(f'Valor total: R$ {df[col].sum():,.2f}')
        print(f'Valor mínimo: R$ {df[col].min():,.2f}')
        print(f'Valor máximo: R$ {df[col].max():,.2f}')
        break
