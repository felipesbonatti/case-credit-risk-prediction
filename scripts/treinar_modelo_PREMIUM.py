#!/usr/bin/env python3
"""
Treinamento Premium do Modelo LightGBM
Meta: AUC-ROC >= 0.95 com hiperparametros otimizados
"""

import pandas as pd
import numpy as np
import joblib
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, classification_report, confusion_matrix, precision_score, recall_score, f1_score
from sklearn.preprocessing import LabelEncoder
from lightgbm import LGBMClassifier
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

print("=" * 80)
print("TREINAMENTO PREMIUM - LIGHTGBM OTIMIZADO")
print("Meta: AUC-ROC >= 0.95")
print("=" * 80)

# Determinar caminhos base
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "processed"
API_DIR = BASE_DIR / "api"

# Carregar dataset realista
print("\n[1/7] Carregando dataset realista...")
df = pd.read_parquet(DATA_DIR / 'dataset_realista_1m.parquet', engine='pyarrow')
print(f"   [OK] {len(df):,} registros | Taxa inadimplencia: {df['inadimplente'].mean() * 100:.2f}%")

# Preparar features
print("\n[2/7] Preparando features...")

# Features numéricas
numeric_features = [
    'score', 'renda', 'idade', 'tempo_cliente_meses', 'qtd_produtos',
    'ticket', 'prazo_meses', 'taxa_juros_aa', 'parcela_mensal',
    'perc_comprometimento_renda', 'alto_comprometimento', 'fator_risco',
    'qtd_atrasos_12m'
]

# Features categóricas
categorical_features = [
    'tipo_credito', 'regiao', 'genero', 'estado_civil', 
    'escolaridade', 'uf', 'porte_municipio'
]

# Criar faixa etaria
df['faixa_etaria'] = pd.cut(df['idade'], 
                             bins=[0, 25, 35, 45, 55, 65, 100],
                             labels=['18-25', '26-35', '36-45', '46-55', '56-65', '66+'])
categorical_features.append('faixa_etaria')

# Encodar categóricas
label_encoders = {}
for col in categorical_features:
    le = LabelEncoder()
    df[f'{col}_encoded'] = le.fit_transform(df[col].astype(str))
    label_encoders[col] = le

# Montar feature set
feature_cols = numeric_features + [f'{col}_encoded' for col in categorical_features]

print(f"   [OK] {len(feature_cols)} features preparadas")
print(f"      Numericas: {len(numeric_features)}")
print(f"      Categoricas: {len(categorical_features)}")

# Preparar dados
X = df[feature_cols].fillna(0)
y = df['inadimplente']

# Split estratificado
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print(f"\n[3/7] Split de dados:")
print(f"   Treino: {len(X_train):,} ({y_train.mean()*100:.2f}% inadimplencia)")
print(f"   Teste:  {len(X_test):,} ({y_test.mean()*100:.2f}% inadimplencia)")

# Hiperparâmetros otimizados para alta performance
print("\n[4/7] Configurando modelo com hiperparametros premium...")
params = {
    'objective': 'binary',
    'metric': 'auc',
    'boosting_type': 'gbdt',
    'n_estimators': 500,
    'learning_rate': 0.05,
    'num_leaves': 100,
    'max_depth': 10,
    'min_child_samples': 20,
    'subsample': 0.8,
    'colsample_bytree': 0.8,
    'reg_alpha': 0.1,
    'reg_lambda': 0.1,
    'random_state': 42,
    'n_jobs': -1,
    'verbose': -1,
    'scale_pos_weight': len(y_train[y_train == 0]) / len(y_train[y_train == 1])
}

print(f"   [OK] Scale pos weight: {params['scale_pos_weight']:.2f}")

# Treinar modelo
print("\n[5/7] Treinando modelo...")
model = LGBMClassifier(**params)
model.fit(
    X_train, y_train,
    eval_set=[(X_test, y_test)],
    eval_metric='auc'
)

# Avaliar modelo
print("\n[6/7] Avaliando modelo...")
y_pred_proba = model.predict_proba(X_test)[:, 1]
y_pred = model.predict(X_test)

auc_score = roc_auc_score(y_test, y_pred_proba)
precision = precision_score(y_test, y_pred)
recall = recall_score(y_test, y_pred)
f1 = f1_score(y_test, y_pred)
cm = confusion_matrix(y_test, y_pred)

print(f"\n   [INFO] MÉTRICAS DO MODELO:")
print(f"   [META] AUC-ROC:   {auc_score:.4f}")
print(f"   [META] Precision: {precision:.4f}")
print(f"   [META] Recall:    {recall:.4f}")
print(f"   [META] F1-Score:  {f1:.4f}")

print(f"\n   Matriz de Confusão:")
print(f"      TN: {cm[0,0]:,} | FP: {cm[0,1]:,}")
print(f"      FN: {cm[1,0]:,} | TP: {cm[1,1]:,}")

# Calcular KS
def calculate_ks(y_true, y_pred_proba):
    """Calcula o KS (Kolmogorov-Smirnov)"""
    df_ks = pd.DataFrame({'y_true': y_true, 'y_pred_proba': y_pred_proba})
    df_ks = df_ks.sort_values('y_pred_proba', ascending=False).reset_index(drop=True)
    df_ks['cumsum_good'] = (1 - df_ks['y_true']).cumsum() / (1 - df_ks['y_true']).sum()
    df_ks['cumsum_bad'] = df_ks['y_true'].cumsum() / df_ks['y_true'].sum()
    df_ks['ks'] = abs(df_ks['cumsum_good'] - df_ks['cumsum_bad'])
    return df_ks['ks'].max()

ks_score = calculate_ks(y_test, y_pred_proba)
print(f"   [META] KS Score:  {ks_score:.4f}")

if auc_score >= 0.95:
    print(f"\n   [OK] [OK] [OK] META ATINGIDA! AUC >= 0.95 [OK] [OK] [OK]")
elif auc_score >= 0.90:
    print(f"\n   [OK] Excelente! AUC >= 0.90 (proximo da meta)")
elif auc_score >= 0.85:
    print(f"\n   [AVISO]  Bom, mas abaixo da meta. AUC >= 0.85")
else:
    print(f"\n   [ERRO] AUC abaixo do esperado. Necessário feature engineering adicional.")

# Feature importance
print("\n   Feature Importance (Top 15):")
feature_importance = pd.DataFrame({
    'feature': feature_cols,
    'importance': model.feature_importances_
}).sort_values('importance', ascending=False).head(15)

for idx, row in feature_importance.iterrows():
    print(f"      {row['feature']:35s}: {row['importance']:,.0f}")

# Salvar modelo e artefatos
print("\n[7/7] Salvando modelo e artefatos...")
API_DIR.mkdir(parents=True, exist_ok=True)

# Salvar modelo
joblib.dump(model, API_DIR / 'modelo_lgbm.pkl')
print(f"   [OK] Modelo: {API_DIR / 'modelo_lgbm.pkl'}")

# Salvar encoders
joblib.dump(label_encoders, API_DIR / 'label_encoders.pkl')
print(f"   [OK] Encoders: {API_DIR / 'label_encoders.pkl'}")

# Salvar feature cols
joblib.dump(feature_cols, API_DIR / 'feature_cols.pkl')
print(f"   [OK] Features: {API_DIR / 'feature_cols.pkl'}")

# Salvar métricas
metricas = {
    'model_type': 'LGBMClassifier',
    'version': '2.2.1-premium',
    'train_date': datetime.now().isoformat(),
    'n_features': len(feature_cols),
    'feature_names': feature_cols,
    'auc_roc': float(auc_score),
    'ks_score': float(ks_score),
    'precision': float(precision),
    'recall': float(recall),
    'f1_score': float(f1),
    'confusion_matrix': cm.tolist(),
    'feature_importance': feature_importance.to_dict('records'),
    'hyperparameters': params,
    'dataset': 'dataset_realista_1m.parquet',
    'train_size': len(X_train),
    'test_size': len(X_test)
}

joblib.dump(metricas, API_DIR / 'metricas_modelo.pkl')
print(f"   [OK] Métricas: {API_DIR / 'metricas_modelo.pkl'}")

# Gerar relatório
report = f"""# Relatório de Treinamento do Modelo

**Dataset:** dataset_realista_1m.parquet  
**Registros:** {len(df):,}  

## Métricas de Performance

| Métrica | Valor |
|---------|-------|
| **AUC-ROC** | **{auc_score:.4f}** |
| **KS Score** | **{ks_score:.4f}** |
| **Precision** | {precision:.4f} |
| **Recall** | {recall:.4f} |
| **F1-Score** | {f1:.4f} |

## Matriz de Confusão

|  | Predito Negativo | Predito Positivo |
|---|---|---|
| **Real Negativo** | {cm[0,0]:,} | {cm[0,1]:,} |
| **Real Positivo** | {cm[1,0]:,} | {cm[1,1]:,} |

## Features Utilizadas

**Total:** {len(feature_cols)} features  
**Numericas:** {len(numeric_features)}  
**Categoricas:** {len(categorical_features)}  

## Features Mais Importantes

{feature_importance.head(10).to_markdown(index=False)}

## Hiperparâmetros

- **n_estimators:** {params['n_estimators']}
- **learning_rate:** {params['learning_rate']}
- **num_leaves:** {params['num_leaves']}
- **max_depth:** {params['max_depth']}
- **scale_pos_weight:** {params['scale_pos_weight']:.2f}

## Conclusão

{'[OK] Modelo atingiu a meta de AUC >= 0.95 e está pronto para produção.' if auc_score >= 0.95 else '[AVISO] Modelo apresenta boa performance mas não atingiu a meta de AUC >= 0.95.'}
"""

with open(BASE_DIR / 'RELATORIO_MODELO_PREMIUM.md', 'w') as f:
    f.write(report)

print(f"   [OK] Relatório: {BASE_DIR / 'RELATORIO_MODELO_PREMIUM.md'}")

print("\n" + "=" * 80)
print("[OK] TREINAMENTO PREMIUM CONCLUÍDO!")
print("=" * 80)
print(f"[META] AUC-ROC: {auc_score:.4f}")
print(f"[INFO] KS Score: {ks_score:.4f}")
print(f"[INFO] Artefatos salvos em: {API_DIR}")
print("=" * 80)
