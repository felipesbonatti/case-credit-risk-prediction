-- ==============================================================================
-- Santander Credit Risk Platform - Database Initialization
-- ==============================================================================

-- CRIA O BANCO (executa apenas se você for rodar como superuser ou fora do Docker)
-- Se já está usando Docker com POSTGRES_DB=credit_risk, não é necessario.
DO $$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_database WHERE datname = 'credit_risk') THEN
      CREATE DATABASE credit_risk;
   END IF;
END $$;

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Create schema
CREATE SCHEMA IF NOT EXISTS credit_risk;

-- Set search path
SET search_path TO credit_risk, public;

-- ==============================================================================
-- Tables
-- ==============================================================================

-- Predictions table
CREATE TABLE IF NOT EXISTS predictions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cliente_id VARCHAR(20),
    score_credito INTEGER NOT NULL,
    renda_mensal DECIMAL(12, 2) NOT NULL,
    idade INTEGER NOT NULL,
    tempo_relacionamento INTEGER NOT NULL,
    qtd_produtos_ativos INTEGER NOT NULL,
    tipo_produto VARCHAR(20) NOT NULL,
    valor DECIMAL(12, 2) NOT NULL,
    prazo INTEGER NOT NULL,
    taxa DECIMAL(6, 4) NOT NULL,
    canal_aquisicao VARCHAR(30),
    regiao VARCHAR(20),
    prediction INTEGER NOT NULL,
    probability DECIMAL(6, 4) NOT NULL,
    risk_score DECIMAL(5, 2) NOT NULL,
    recommendation VARCHAR(20) NOT NULL,
    confidence DECIMAL(6, 4) NOT NULL,
    threshold DECIMAL(6, 4) NOT NULL,
    model_version VARCHAR(10) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Model metrics table
CREATE TABLE IF NOT EXISTS model_metrics (
    id SERIAL PRIMARY KEY,
    model_version VARCHAR(10) NOT NULL,
    metric_name VARCHAR(50) NOT NULL,
    metric_value DECIMAL(10, 6) NOT NULL,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Audit log table
CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(50),
    action VARCHAR(100) NOT NULL,
    resource VARCHAR(100),
    details JSONB,
    ip_address INET,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==============================================================================
-- Indexes
-- ==============================================================================

CREATE INDEX IF NOT EXISTS idx_predictions_cliente_id ON predictions(cliente_id);
CREATE INDEX IF NOT EXISTS idx_predictions_created_at ON predictions(created_at);
CREATE INDEX IF NOT EXISTS idx_predictions_prediction ON predictions(prediction);
CREATE INDEX IF NOT EXISTS idx_model_metrics_version ON model_metrics(model_version);
CREATE INDEX IF NOT EXISTS idx_audit_log_created_at ON audit_log(created_at);

-- ==============================================================================
-- Initial Data
-- ==============================================================================

-- Insert initial model metrics
INSERT INTO model_metrics (model_version, metric_name, metric_value) VALUES
    ('1.0.0', 'accuracy', 0.92),
    ('1.0.0', 'precision', 0.82),
    ('1.0.0', 'recall', 0.78),
    ('1.0.0', 'f1_score', 0.80),
    ('1.0.0', 'auc_roc', 0.85)
ON CONFLICT DO NOTHING;

-- ==============================================================================
-- Grants
-- ==============================================================================

GRANT ALL PRIVILEGES ON SCHEMA credit_risk TO santander;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA credit_risk TO santander;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA credit_risk TO santander;