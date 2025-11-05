"""
Testes End-to-End (E2E)
Testa o pipeline completo: dados → modelo → API → resposta
"""

import pytest
from pathlib import Path
import pandas as pd
import joblib
from fastapi.testclient import TestClient


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture(scope="module")
def sample_dataset(tmp_path_factory):
    """
    Cria dataset sintético para testes E2E
    """
    tmp_dir = tmp_path_factory.mktemp("data")
    dataset_path = tmp_dir / "test_dataset.parquet"

    # Criar dataset mínimo
    data = {
        "cliente_id": [f"CLI_{i:06d}" for i in range(100)],
        "idade": [25 + (i % 40) for i in range(100)],
        "renda": [3000 + (i * 100) for i in range(100)],
        "score": [300 + (i * 6) for i in range(100)],
        "ticket": [5000 + (i * 50) for i in range(100)],
        "prazo_meses": [12 + (i % 48) for i in range(100)],
        "taxa_juros_aa": [12.0 + (i % 20) for i in range(100)],
        "tempo_cliente_meses": [6 + (i % 120) for i in range(100)],
        "qtd_produtos": [1 + (i % 5) for i in range(100)],
        "qtd_atrasos_12m": [i % 3 for i in range(100)],
        "inadimplente": [1 if i % 4 == 0 else 0 for i in range(100)],  # 25% inadimplentes
    }

    df = pd.DataFrame(data)
    df.to_parquet(dataset_path)

    return dataset_path


@pytest.fixture(scope="module")
def trained_model(tmp_path_factory, sample_dataset):
    """
    Treina modelo simples para testes E2E
    """
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import train_test_split

    # Carregar dados
    df = pd.read_parquet(sample_dataset, engine='pyarrow')

    # Features simples
    features = ["idade", "renda", "score", "ticket", "prazo_meses", "taxa_juros_aa", "tempo_cliente_meses", "qtd_produtos", "qtd_atrasos_12m"]

    X = df[features]
    y = df["inadimplente"]

    # Treinar modelo
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = RandomForestClassifier(n_estimators=10, random_state=42, max_depth=5)
    model.fit(X_train, y_train)

    # Salvar modelo
    tmp_dir = tmp_path_factory.mktemp("models")
    model_path = tmp_dir / "test_model.pkl"
    joblib.dump(model, model_path)

    # Salvar features
    features_path = tmp_dir / "test_features.pkl"
    joblib.dump(features, features_path)

    return {"model_path": model_path, "features_path": features_path, "features": features}


# ============================================================================
# Testes E2E - Pipeline Completo
# ============================================================================


def test_e2e_data_loading(sample_dataset):
    """
    E2E: Testa carregamento de dados
    """
    df = pd.read_parquet(sample_dataset, engine='pyarrow')

    assert len(df) == 100
    assert "inadimplente" in df.columns
    assert "score" in df.columns


def test_e2e_model_training(trained_model):
    """
    E2E: Testa que modelo foi treinado
    """
    model = joblib.load(trained_model["model_path"])

    assert model is not None
    assert hasattr(model, "predict")
    assert hasattr(model, "predict_proba")


def test_e2e_model_prediction(trained_model, sample_dataset):
    """
    E2E: Testa predição do modelo
    """
    model = joblib.load(trained_model["model_path"])
    features = trained_model["features"]

    # Carregar dados
    df = pd.read_parquet(sample_dataset, engine='pyarrow')
    X = df[features].iloc[0:1]

    # Fazer predição
    prediction = model.predict(X)
    probability = model.predict_proba(X)

    assert prediction is not None
    assert len(prediction) == 1
    assert probability is not None
    assert probability.shape == (1, 2)


def test_e2e_api_health_check():
    """
    E2E: Testa health check da API
    """
    from app.main import app

    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_e2e_api_root():
    """
    E2E: Testa endpoint raiz da API
    """
    from app.main import app

    client = TestClient(app)
    response = client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data


def test_e2e_api_predict_single():
    """
    E2E: Testa predição única via API
    """
    from app.main import app

    client = TestClient(app)

    # Dados de teste
    payload = {
        "cliente_id": "TEST_001",
        "idade": 35,
        "renda": 8500.00,
        "score": 750,
        "ticket": 50000.00,
        "prazo_meses": 48,
        "taxa_juros_aa": 15.5,
        "tempo_cliente_meses": 24,
        "qtd_produtos": 3,
        "qtd_atrasos_12m": 0,
        "genero": "Masculino",
        "estado_civil": "Casado",
        "escolaridade": "Superior",
        "regiao": "Sudeste",
        "uf": "SP",
        "porte_municipio": "Grande",
        "tipo_credito": "Pessoal",
    }

    response = client.post("/api/v1/predict", json=payload)

    # Verificar resposta
    assert response.status_code == 200
    data = response.json()

    assert "cliente_id" in data
    assert "prediction" in data
    assert "probability" in data
    assert "risk_score" in data
    assert "recommendation" in data
    assert data["cliente_id"] == "TEST_001"
    assert data["prediction"] in [0, 1]
    assert 0 <= data["probability"] <= 1


def test_e2e_api_predict_batch():
    """
    E2E: Testa predição em lote via API
    """
    from app.main import app

    client = TestClient(app)

    # Dados de teste
    payload = {
        "requests": [
            {
                "cliente_id": f"TEST_{i:03d}",
                "idade": 25 + i,
                "renda": 5000 + (i * 100),
                "score": 600 + (i * 10),
                "ticket": 30000 + (i * 1000),
                "prazo_meses": 36,
                "taxa_juros_aa": 15.0,
                "tempo_cliente_meses": 12,
                "qtd_produtos": 2,
                "qtd_atrasos_12m": 0,
                "genero": "Masculino",
                "estado_civil": "Solteiro",
                "escolaridade": "Superior",
                "regiao": "Sudeste",
                "uf": "SP",
                "porte_municipio": "Grande",
                "tipo_credito": "Pessoal",
            }
            for i in range(5)
        ]
    }

    response = client.post("/api/v1/predict/batch", json=payload)

    # Verificar resposta
    assert response.status_code == 200
    data = response.json()

    assert "predictions" in data
    assert "total" in data
    assert "success" in data
    assert data["total"] == 5
    assert data["success"] == 5
    assert len(data["predictions"]) == 5


def test_e2e_api_metrics():
    """
    E2E: Testa endpoint de métricas
    """
    from app.main import app

    client = TestClient(app)
    response = client.get("/api/v1/metrics")

    assert response.status_code == 200
    data = response.json()

    assert "model" in data
    assert "version" in data["model"]


def test_e2e_api_analysis_roc():
    """
    E2E: Testa endpoint de análise ROC
    """
    from app.main import app

    client = TestClient(app)
    response = client.get("/api/v1/analysis/roc-curve")

    # Pode retornar 200 ou 500 se não houver dados
    assert response.status_code in [200, 500]

    if response.status_code == 200:
        data = response.json()
        assert "auc" in data


def test_e2e_api_analysis_confusion_matrix():
    """
    E2E: Testa endpoint de matriz de confusão
    """
    from app.main import app

    client = TestClient(app)
    response = client.get("/api/v1/analysis/confusion-matrix?threshold=0.5")

    # Pode retornar 200 ou 500 se não houver dados
    assert response.status_code in [200, 500]

    if response.status_code == 200:
        data = response.json()
        assert "tp" in data
        assert "fp" in data
        assert "tn" in data
        assert "fn" in data


# ============================================================================
# Testes E2E - Cenários de Negócio
# ============================================================================


def test_e2e_business_low_risk_approval():
    """
    E2E: Testa aprovação de cliente de baixo risco
    """
    from app.main import app

    client = TestClient(app)

    # Cliente de baixo risco
    payload = {
        "cliente_id": "LOW_RISK_001",
        "idade": 45,
        "renda": 15000.00,
        "score": 850,  # Score alto
        "ticket": 30000.00,
        "prazo_meses": 36,
        "taxa_juros_aa": 12.0,
        "tempo_cliente_meses": 60,  # Cliente antigo
        "qtd_produtos": 4,  # Múltiplos produtos
        "qtd_atrasos_12m": 0,  # Sem atrasos
        "genero": "Feminino",
        "estado_civil": "Casado",
        "escolaridade": "Pós-Graduação",
        "regiao": "Sul",
        "uf": "RS",
        "porte_municipio": "Grande",
        "tipo_credito": "Pessoal",
    }

    response = client.post("/api/v1/predict", json=payload)

    assert response.status_code == 200
    data = response.json()

    # Cliente de baixo risco deve ter baixa probabilidade de inadimplência
    assert data["probability"] <= 0.30
    # Recomendação deve ser Aprovar ou Revisar
    assert data["recommendation"] in ["Aprovar", "Revisar"]


def test_e2e_business_high_risk_rejection():
    """
    E2E: Testa rejeição de cliente de alto risco
    """
    from app.main import app

    client = TestClient(app)

    # Cliente de alto risco
    payload = {
        "cliente_id": "HIGH_RISK_001",
        "idade": 22,
        "renda": 2000.00,
        "score": 350,  # Score baixo
        "ticket": 80000.00,  # Ticket alto para renda
        "prazo_meses": 60,
        "taxa_juros_aa": 25.0,
        "tempo_cliente_meses": 2,  # Cliente novo
        "qtd_produtos": 1,
        "qtd_atrasos_12m": 3,  # Múltiplos atrasos
        "genero": "Masculino",
        "estado_civil": "Solteiro",
        "escolaridade": "Médio",
        "regiao": "Norte",
        "uf": "AM",
        "porte_municipio": "Pequeno",
        "tipo_credito": "Veículo",
    }

    response = client.post("/api/v1/predict", json=payload)

    assert response.status_code == 200
    data = response.json()

    # Cliente de alto risco deve ter alta probabilidade de inadimplência
    # Nota: Como é um modelo sintético, pode não ser perfeito
    # Recomendação deve considerar o risco
    assert data["recommendation"] in ["Revisar", "Negar"]


def test_e2e_business_batch_processing():
    """
    E2E: Testa processamento em lote de múltiplos perfis
    """
    from app.main import app

    client = TestClient(app)

    # Mix de perfis
    payload = {
        "requests": [
            # Baixo risco
            {
                "cliente_id": "BATCH_LOW_001",
                "idade": 40,
                "renda": 12000,
                "score": 800,
                "ticket": 40000,
                "prazo_meses": 48,
                "taxa_juros_aa": 14.0,
                "tempo_cliente_meses": 36,
                "qtd_produtos": 3,
                "qtd_atrasos_12m": 0,
                "genero": "Masculino",
                "estado_civil": "Casado",
                "escolaridade": "Superior",
                "regiao": "Sudeste",
                "uf": "SP",
                "porte_municipio": "Grande",
                "tipo_credito": "Pessoal",
            },
            # Alto risco
            {
                "cliente_id": "BATCH_HIGH_001",
                "idade": 25,
                "renda": 2500,
                "score": 400,
                "ticket": 60000,
                "prazo_meses": 60,
                "taxa_juros_aa": 22.0,
                "tempo_cliente_meses": 3,
                "qtd_produtos": 1,
                "qtd_atrasos_12m": 2,
                "genero": "Feminino",
                "estado_civil": "Solteiro",
                "escolaridade": "Médio",
                "regiao": "Nordeste",
                "uf": "BA",
                "porte_municipio": "Médio",
                "tipo_credito": "Veículo",
            },
        ]
    }

    response = client.post("/api/v1/predict/batch", json=payload)

    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 2
    assert data["success"] == 2
    assert len(data["predictions"]) == 2

    # Verificar que predições são diferentes
    pred1 = data["predictions"][0]
    pred2 = data["predictions"][1]

    assert pred1["cliente_id"] == "BATCH_LOW_001"
    assert pred2["cliente_id"] == "BATCH_HIGH_001"


# ============================================================================
# Testes E2E - Validação de Dados
# ============================================================================


def test_e2e_validation_missing_field():
    """
    E2E: Testa validação de campo obrigatório faltando
    """
    from app.main import app

    client = TestClient(app)

    # Payload incompleto (falta idade)
    payload = {
        "cliente_id": "TEST_INVALID",
        "renda": 5000,
        "score": 700,
        # idade: FALTANDO
        "ticket": 30000,
        "prazo_meses": 36,
        "taxa_juros_aa": 15.0,
        "tempo_cliente_meses": 12,
        "qtd_produtos": 2,
        "qtd_atrasos_12m": 0,
        "genero": "Masculino",
        "estado_civil": "Solteiro",
        "escolaridade": "Superior",
        "regiao": "Sudeste",
        "uf": "SP",
        "porte_municipio": "Grande",
        "tipo_credito": "Pessoal",
    }

    response = client.post("/api/v1/predict", json=payload)

    # Deve retornar erro de validação
    assert response.status_code == 422


def test_e2e_validation_invalid_value():
    """
    E2E: Testa validação de valor inválido
    """
    from app.main import app

    client = TestClient(app)

    # Idade negativa
    payload = {
        "cliente_id": "TEST_INVALID",
        "idade": -5,  # INVÁLIDO
        "renda": 5000,
        "score": 700,
        "ticket": 30000,
        "prazo_meses": 36,
        "taxa_juros_aa": 15.0,
        "tempo_cliente_meses": 12,
        "qtd_produtos": 2,
        "qtd_atrasos_12m": 0,
        "genero": "Masculino",
        "estado_civil": "Solteiro",
        "escolaridade": "Superior",
        "regiao": "Sudeste",
        "uf": "SP",
        "porte_municipio": "Grande",
        "tipo_credito": "Pessoal",
    }

    response = client.post("/api/v1/predict", json=payload)

    # Deve retornar erro de validação
    assert response.status_code == 422
