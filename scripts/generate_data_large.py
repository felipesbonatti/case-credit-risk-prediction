"""
Santander Credit Risk Platform - Data Generation v3 (Large Scale)
Geração de dados sintéticos realistas - Otimizado para grandes volumes
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import logging
import gc

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_synthetic_data_batch(n, seed, start_id):
    """
    Gera base sintética com realismo bancário CALIBRADO (versão otimizada)
    
    Args:
        n: Número de registros
        seed: Seed para reprodutibilidade
        start_id: ID inicial para os clientes
        
    Returns:
        DataFrame com dados sintéticos
    """
    np.random.seed(seed)
    
    # IDs e Temporalidade
    ids = np.arange(start_id, start_id + n)
    meses = np.random.choice(
        ["202201", "202202", "202203", "202204", "202205", "202206",
         "202207", "202208", "202209", "202210", "202211", "202212"],
        size=n,
        p=[0.06, 0.07, 0.08, 0.09, 0.10, 0.09, 0.09, 0.09, 0.09, 0.09, 0.08, 0.07]
    )
    
    # Perfil do Cliente
    scores = np.random.normal(650, 120, size=n).clip(300, 950).astype(np.int32)
    renda_base = scores * 15 + np.random.normal(0, 3000, size=n)
    idades = np.random.normal(38, 12, size=n).clip(18, 75).astype(np.int32)
    tempo_relacionamento = np.random.exponential(24, size=n).clip(1, 200).astype(np.int32)
    
    qtd_produtos = np.where(
        scores > 750, np.random.choice([1, 2, 3, 4, 5], size=n, p=[0.1, 0.2, 0.3, 0.25, 0.15]),
        np.where(scores > 600, np.random.choice([1, 2, 3, 4, 5], size=n, p=[0.3, 0.35, 0.2, 0.1, 0.05]),
                 np.random.choice([1, 2, 3, 4, 5], size=n, p=[0.6, 0.25, 0.1, 0.04, 0.01]))
    )
    
    # Produtos
    tipos_produto = np.random.choice(
        ["CDC", "Imobiliário", "Cartão", "Pessoal"],
        size=n,
        p=[0.45, 0.15, 0.15, 0.25]
    )
    
    valores = np.where(
        tipos_produto == "Imobiliário",
        np.random.randint(80_000, 500_000, size=n),
        np.where(
            tipos_produto == "Cartão",
            np.random.randint(500, 15_000, size=n),
            np.where(
                tipos_produto == "Pessoal",
                np.random.randint(3_000, 30_000, size=n),
                np.random.randint(1_000, 50_000, size=n)
            )
        )
    )
    
    prazos = np.where(
        tipos_produto == "Imobiliário",
        np.random.choice([180, 240, 360], size=n),
        np.where(
            tipos_produto == "Pessoal",
            np.random.choice([24, 36, 48], size=n),
            np.random.choice([6, 12, 18, 24, 36, 48], size=n)
        )
    )
    
    taxa_base = 0.30 - (scores / 950) * 0.25
    taxa_produto = np.where(tipos_produto == "Cartão", 0.05,
                   np.where(tipos_produto == "Pessoal", 0.02, 0))
    taxas = (taxa_base + taxa_produto + np.random.normal(0, 0.02, size=n)).clip(0.015, 0.35).round(4)
    
    canais = np.random.choice(
        ["App", "Agência", "Parceiro", "Internet Banking"],
        size=n,
        p=[0.45, 0.25, 0.20, 0.10]
    )
    
    regioes = np.random.choice(
        ["Sudeste", "Sul", "Nordeste", "Centro-Oeste", "Norte"],
        size=n,
        p=[0.45, 0.20, 0.20, 0.10, 0.05]
    )
    
    # Correlação região x renda
    regiao_renda_factor = np.where(
        regioes == "Sudeste", 1.2,
        np.where(regioes == "Sul", 1.15,
        np.where(regioes == "Centro-Oeste", 1.0,
        np.where(regioes == "Nordeste", 0.85, 0.80)))
    )
    rendas = (renda_base * regiao_renda_factor).clip(1_200, 35_000).astype(np.int32)
    
    # Inadimplência calibrada
    risco_score = ((950 - scores) / 850) * 0.12
    risco_renda = np.where(rendas < 2_000, 0.08,
                  np.where(rendas < 3_500, 0.015, 0))
    risco_valor = np.where(valores > 200_000, 0.02,
                  np.where(valores > 100_000, 0.01, 0))
    risco_prazo = (prazos / 360) * 0.02
    risco_produto = np.where(tipos_produto == "Cartão", 0.04,
                    np.where(tipos_produto == "CDC", 0.02,
                    np.where(tipos_produto == "Pessoal", 0.025, -0.02)))
    fator_relacionamento = np.where(tempo_relacionamento > 36, -0.02,
                           np.where(tempo_relacionamento > 12, -0.01, 0))
    fator_produtos = np.where(qtd_produtos >= 3, -0.015, 0)
    
    # Sazonalidade
    mes_num = pd.Series(meses).str[-2:].astype(int).values
    fator_sazonal = np.where(
        mes_num == 12, 0.020,
        np.where(mes_num == 1, 0.015,
        np.where(mes_num == 2, 0.015,
        np.where(mes_num == 6, -0.005,
        np.where(mes_num == 7, -0.005, 0))))
    )
    
    # Tendência temporal
    mes_index = (mes_num - 1) / 11
    tendencia = mes_index * 0.01
    
    # Risco total
    risco_total = (
        risco_score + risco_renda + risco_valor + risco_prazo +
        risco_produto + fator_relacionamento + fator_produtos +
        fator_sazonal + tendencia +
        np.random.normal(0, 0.01, size=n)
    ).clip(0.005, 0.25)
    
    # Outliers - 2%
    outliers_mask = np.random.random(n) < 0.02
    risco_total[outliers_mask] = np.random.uniform(0.5, 0.9, outliers_mask.sum())
    
    # Inadimplência binária
    inadimplente = np.random.binomial(1, risco_total).astype(np.int8)
    
    # DataFrame
    df = pd.DataFrame({
        'cliente_id': ids,
        'mes_referencia': meses,
        'score_credito': scores,
        'renda_mensal': rendas,
        'idade': idades,
        'tempo_relacionamento': tempo_relacionamento,
        'qtd_produtos_ativos': qtd_produtos.astype(np.int8),
        'tipo_produto': tipos_produto,
        'valor': valores,
        'prazo': prazos.astype(np.int16),
        'taxa': taxas.astype(np.float32),
        'canal_aquisicao': canais,
        'regiao': regioes,
        'inadimplente': inadimplente
    })
    
    # Missing values - 5%
    missing_mask = np.random.random(n) < 0.05
    df.loc[missing_mask, 'regiao'] = "Não Informado"
    df.loc[missing_mask, 'canal_aquisicao'] = "Não Informado"
    
    return df


def main():
    """Main function - Gera dados em lotes"""
    
    # Configurações
    total_records = 5_000_000
    batch_size = 500_000  # 500 mil por lote
    num_batches = total_records // batch_size
    
    logger.info(f" Gerando base sintética premium com {total_records:,} registros")
    logger.info(f" Processando em {num_batches} lotes de {batch_size:,} registros cada")
    
    # Criar diretórios
    data_dir = Path(__file__).parent.parent / "data"
    processed_dir = data_dir / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = processed_dir / "dataset_modelo_sintetico_v3.parquet"
    
    # Gerar e salvar em lotes
    for i in range(num_batches):
        start_id = 10_000_000 + (i * batch_size)
        seed = 42 + i
        
        logger.info(f"[INFO] Gerando lote {i+1}/{num_batches} (IDs {start_id:,} a {start_id + batch_size - 1:,})...")
        
        df_batch = generate_synthetic_data_batch(batch_size, seed, start_id)
        
        # Salvar (append após o primeiro lote)
        if i == 0:
            df_batch.to_parquet(output_path, index=False, compression='snappy')
        else:
            # Append ao arquivo existente
            existing_df = pd.read_parquet(output_path, engine='pyarrow')
            combined_df = pd.concat([existing_df, df_batch], ignore_index=True)
            combined_df.to_parquet(output_path, index=False, compression='snappy')
            del existing_df, combined_df
        
        # Estatísticas do lote
        logger.info(f"   [OK] Lote {i+1} concluído - Taxa inadimplência: {df_batch['inadimplente'].mean()*100:.2f}%")
        
        # Limpar memória
        del df_batch
        gc.collect()
    
    # Estatísticas finais
    logger.info(f"\n{'='*80}")
    logger.info(f"[OK] Base gerada com sucesso!")
    
    df_final = pd.read_parquet(output_path, engine='pyarrow')
    logger.info(f"[INFO] Estatísticas finais:")
    logger.info(f"   - Total de registros: {len(df_final):,}")
    logger.info(f"   - Taxa de inadimplência: {df_final['inadimplente'].mean()*100:.2f}%")
    logger.info(f"   - Score médio: {df_final['score_credito'].mean():.0f}")
    logger.info(f"   - Renda média: R$ {df_final['renda_mensal'].mean():,.2f}")
    logger.info(f"   - Valor médio: R$ {df_final['valor'].mean():,.2f}")
    logger.info(f"[SALVO] Dados salvos em: {output_path}")
    logger.info(f" Tamanho do arquivo: {output_path.stat().st_size / 1024 / 1024:.2f} MB")
    logger.info(f"{'='*80}\n")


if __name__ == "__main__":
    main()

