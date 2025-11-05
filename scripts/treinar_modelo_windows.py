import pandas as pd
import numpy as np
import joblib
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, classification_report, confusion_matrix, precision_score, recall_score, f1_score
from sklearn.preprocessing import LabelEncoder
import json

print("=" * 80)
print("TREINAMENTO DO MODELO - CREDIT RISK")
print("=" * 80)

# Instalar LightGBM se necessário
try:
    import lightgbm as lgb
    print("\n[OK] LightGBM disponível")
except ImportError:
    print("\n⏳ Instalando LightGBM...")
    import subprocess
    subprocess.check_call(['pip', 'install', '-q', 'lightgbm'])
    import lightgbm as lgb
    print("[OK] LightGBM instalado")

# Carregar dataset
print("\n[1/6] Carregando dataset...")
dataset_path = Path('data/processed/dataset_demo_1m.parquet')
if not dataset_path.exists():
    print(f"[ERRO] Dataset não encontrado: {dataset_path}")
    print("   Execute primeiro: python scripts\\criar_dataset_windows.py")
    exit(1)

df = pd.read_parquet(dataset_path, engine='pyarrow')
print(f"[OK] {len(df):,} registros | Taxa inadimplência: {df['inadimplente'].mean() * 100:.2f}%")

# Preparar features
print("\n[2/6] Preparando features...")
numeric_features = ['score', 'renda', 'idade', 'tempo_relacionamento', 
                   'qtd_produtos_ativos', 'prazo', 'taxa', 'valor_renda_ratio', 'ticket']
categorical_features = ['tipo_produto', 'regiao', 'canal']

le_dict = {}
for col in categorical_features:
    le = LabelEncoder()
    df[f'{col}_encoded'] = le.fit_transform(df[col])
    le_dict[col] = le

feature_cols = numeric_features + [f'{col}_encoded' for col in categorical_features]
X = df[feature_cols]
y = df['inadimplente']

# Split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
print(f"[OK] Train: {len(X_train):,} | Test: {len(X_test):,}")

# Treinar
print("\n[3/6] Treinando LightGBM...")
scale_pos_weight = (y_train == 0).sum() / (y_train == 1).sum()
print(f"   Scale pos weight: {scale_pos_weight:.2f}")

params = {
    'objective': 'binary',
    'metric': 'auc',
    'boosting_type': 'gbdt',
    'num_leaves': 63,
    'learning_rate': 0.03,
    'feature_fraction': 0.9,
    'bagging_fraction': 0.9,
    'bagging_freq': 5,
    'max_depth': 8,
    'min_child_samples': 50,
    'reg_alpha': 0.5,
    'reg_lambda': 0.5,
    'scale_pos_weight': scale_pos_weight,
    'random_state': 42,
    'verbose': -1
}

train_data = lgb.Dataset(X_train, label=y_train)
test_data = lgb.Dataset(X_test, label=y_test, reference=train_data)

model = lgb.train(
    params,
    train_data,
    num_boost_round=1000,
    valid_sets=[train_data, test_data],
    valid_names=['train', 'test'],
    callbacks=[
        lgb.early_stopping(stopping_rounds=100),
        lgb.log_evaluation(period=200)
    ]
)

print(f"[OK] Modelo treinado com {model.best_iteration} iterações")

# Avaliar
print("\n[4/6] Avaliando modelo...")
y_pred_proba = model.predict(X_test, num_iteration=model.best_iteration)

from sklearn.metrics import precision_recall_curve
precision, recall, thresholds = precision_recall_curve(y_test, y_pred_proba)
f1_scores = 2 * (precision * recall) / (precision + recall + 1e-10)
optimal_idx = np.argmax(f1_scores)
optimal_threshold = thresholds[optimal_idx] if optimal_idx < len(thresholds) else 0.5

y_pred = (y_pred_proba >= optimal_threshold).astype(int)

auc_score = roc_auc_score(y_test, y_pred_proba)
precision_val = precision_score(y_test, y_pred)
recall_val = recall_score(y_test, y_pred)
f1_val = f1_score(y_test, y_pred)

print(f"\n[INFO] Métricas de Performance:")
print(f"   AUC-ROC: {auc_score:.4f}")
print(f"   Precision: {precision_val:.4f}")
print(f"   Recall: {recall_val:.4f}")
print(f"   F1-Score: {f1_val:.4f}")
print(f"   Threshold Otimizado: {optimal_threshold:.4f}")

cm = confusion_matrix(y_test, y_pred)
print(f"\n[META] Confusion Matrix:")
print(f"   TN: {cm[0,0]:,} | FP: {cm[0,1]:,}")
print(f"   FN: {cm[1,0]:,} | TP: {cm[1,1]:,}")

# Feature Importance
importance = pd.DataFrame({
    'feature': feature_cols,
    'importance': model.feature_importance(importance_type='gain')
}).sort_values('importance', ascending=False)

print(f"\n Top 10 Features:")
for idx, row in importance.head(10).iterrows():
    print(f"   {row['feature']:25s}: {row['importance']:,.0f}")

# Salvar
print("\n[5/6] Salvando modelo...")
model_dir = Path('data/models')
model_dir.mkdir(parents=True, exist_ok=True)

model.save_model(str(model_dir / 'credit_risk_lgbm_v2.txt'))
joblib.dump(model, model_dir / 'credit_risk_model.pkl')
joblib.dump(le_dict, model_dir / 'label_encoders.pkl')

metadata = {
    'model_type': 'LightGBM',
    'version': '2.0.0',
    'train_date': pd.Timestamp.now().isoformat(),
    'features': feature_cols,
    'optimal_threshold': float(optimal_threshold),
    'metrics': {
        'auc_roc': float(auc_score),
        'precision': float(precision_val),
        'recall': float(recall_val),
        'f1_score': float(f1_val),
        'best_iteration': int(model.best_iteration)
    },
    'params': params
}

with open(model_dir / 'model_metadata.json', 'w') as f:
    json.dump(metadata, f, indent=2)

print(f"[OK] Modelo salvo em: {model_dir}")

print("\n" + "=" * 80)
print("[OK] TREINAMENTO CONCLUÍDO!")
print("=" * 80)
print(f"\n[META] AUC-ROC: {auc_score:.4f}")
print(f" Modelo: {model_dir / 'credit_risk_model.pkl'}")
print(f" Metadata: {model_dir / 'model_metadata.json'}")
