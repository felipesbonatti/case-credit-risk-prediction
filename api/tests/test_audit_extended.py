"""
Testes Estendidos para o módulo de auditoria
Aumenta cobertura de 50% para 80%+
"""

import pytest
from pathlib import Path
import json
from datetime import datetime
from app.security.audit import (
    AuditLogger,
    AuditEventType,
    AuditSeverity,
    setup_audit_logging,
)


@pytest.fixture
def audit_logger(tmp_path):
    """Fixture para criar instância de AuditLogger com diretório temporário"""
    log_dir = tmp_path / "audit_logs"
    logger = AuditLogger(log_dir=str(log_dir))
    return logger


@pytest.fixture
def temp_log_dir(tmp_path):
    """Fixture para diretório temporário de logs"""
    return tmp_path / "audit_logs"


# ============================================================================
# Testes para setup_audit_logging
# ============================================================================


def test_setup_audit_logging():
    """Testa configuração de logging de auditoria"""
    # Não deve gerar erro
    setup_audit_logging()


# ============================================================================
# Testes para AuditLogger
# ============================================================================


def test_audit_logger_initialization(temp_log_dir):
    """Testa inicialização do AuditLogger"""
    logger = AuditLogger(log_dir=str(temp_log_dir))

    assert logger.log_dir == temp_log_dir
    assert temp_log_dir.exists()


def test_log_event(audit_logger):
    """Testa logging de evento básico"""
    audit_logger.log_event(
        event_type=AuditEventType.PREDICTION_SUCCESS, severity=AuditSeverity.INFO, details={"cliente_id": "12345"}
    )

    # Verificar que arquivo de log foi criado
    log_files = list(audit_logger.log_dir.glob("audit_*.jsonl"))
    assert len(log_files) > 0


def test_log_event_with_user(audit_logger):
    """Testa logging de evento com usuário"""
    audit_logger.log_event(
        event_type=AuditEventType.LOGIN_SUCCESS,
        severity=AuditSeverity.INFO,
        user_id="user123",
        details={"ip": "192.168.1.1"},
    )

    log_files = list(audit_logger.log_dir.glob("audit_*.jsonl"))
    assert len(log_files) > 0


def test_log_event_critical(audit_logger):
    """Testa logging de evento crítico"""
    audit_logger.log_event(
        event_type=AuditEventType.UNAUTHORIZED_ACCESS, severity=AuditSeverity.CRITICAL, details={"attempt": 1}
    )

    log_files = list(audit_logger.log_dir.glob("audit_*.jsonl"))
    assert len(log_files) > 0


def test_log_prediction(audit_logger):
    """Testa logging de predição"""
    audit_logger.log_prediction(
        cliente_id="12345", prediction=0, probability=0.15, recommendation="Aprovar", model_version="1.0.0"
    )

    log_files = list(audit_logger.log_dir.glob("audit_*.jsonl"))
    assert len(log_files) > 0

    # Ler o log e verificar conteúdo
    with open(log_files[0], "r") as f:
        lines = f.readlines()
        last_log = json.loads(lines[-1])

        assert last_log["event_type"] == AuditEventType.PREDICTION_SUCCESS
        assert last_log["details"]["prediction"] == 0
        assert last_log["details"]["probability"] == 0.15


def test_log_prediction_high_risk(audit_logger):
    """Testa logging de predição de alto risco"""
    audit_logger.log_prediction(
        cliente_id="12345", prediction=1, probability=0.85, recommendation="Negar", model_version="1.0.0"
    )

    log_files = list(audit_logger.log_dir.glob("audit_*.jsonl"))
    with open(log_files[0], "r") as f:
        lines = f.readlines()
        last_log = json.loads(lines[-1])

        # Alto risco deve ter severidade WARNING
        assert last_log["severity"] == AuditSeverity.WARNING


def test_log_authentication(audit_logger):
    """Testa logging de autenticação"""
    audit_logger.log_authentication(user_id="user123", success=True, ip_address="192.168.1.1")

    log_files = list(audit_logger.log_dir.glob("audit_*.jsonl"))
    with open(log_files[0], "r") as f:
        lines = f.readlines()
        last_log = json.loads(lines[-1])

        assert last_log["event_type"] == AuditEventType.LOGIN_SUCCESS
        assert last_log["user_id"] == "user123"


def test_log_authentication_failed(audit_logger):
    """Testa logging de autenticação falhada"""
    audit_logger.log_authentication(user_id="user123", success=False, ip_address="192.168.1.1", reason="Invalid password")

    log_files = list(audit_logger.log_dir.glob("audit_*.jsonl"))
    with open(log_files[0], "r") as f:
        lines = f.readlines()
        last_log = json.loads(lines[-1])

        assert last_log["event_type"] == AuditEventType.LOGIN_FAILED
        assert last_log["severity"] == AuditSeverity.WARNING


def test_log_data_access(audit_logger):
    """Testa logging de acesso a dados"""
    audit_logger.log_data_access(user_id="user123", resource="customer_data", action="read", record_count=100)

    log_files = list(audit_logger.log_dir.glob("audit_*.jsonl"))
    with open(log_files[0], "r") as f:
        lines = f.readlines()
        last_log = json.loads(lines[-1])

        assert last_log["event_type"] == AuditEventType.DATA_ACCESS
        assert last_log["details"]["resource"] == "customer_data"
        assert last_log["details"]["record_count"] == 100


def test_log_security_event(audit_logger):
    """Testa logging de evento de segurança"""
    audit_logger.log_security_event(
        event_type=AuditEventType.RATE_LIMIT_EXCEEDED, user_id="user123", ip_address="192.168.1.1", details={"limit": 100}
    )

    log_files = list(audit_logger.log_dir.glob("audit_*.jsonl"))
    with open(log_files[0], "r") as f:
        lines = f.readlines()
        last_log = json.loads(lines[-1])

        assert last_log["event_type"] == AuditEventType.RATE_LIMIT_EXCEEDED
        assert last_log["severity"] == AuditSeverity.WARNING


def test_log_system_error(audit_logger):
    """Testa logging de erro do sistema"""
    audit_logger.log_system_error(error_type="DatabaseError", error_message="Connection timeout", stack_trace="...")

    log_files = list(audit_logger.log_dir.glob("audit_*.jsonl"))
    with open(log_files[0], "r") as f:
        lines = f.readlines()
        last_log = json.loads(lines[-1])

        assert last_log["event_type"] == AuditEventType.SYSTEM_ERROR
        assert last_log["severity"] == AuditSeverity.ERROR
        assert last_log["details"]["error_type"] == "DatabaseError"


def test_log_model_event(audit_logger):
    """Testa logging de evento do modelo"""
    audit_logger.log_model_event(
        event_type=AuditEventType.MODEL_LOADED, model_version="1.0.0", details={"features": 21, "auc": 0.79}
    )

    log_files = list(audit_logger.log_dir.glob("audit_*.jsonl"))
    with open(log_files[0], "r") as f:
        lines = f.readlines()
        last_log = json.loads(lines[-1])

        assert last_log["event_type"] == AuditEventType.MODEL_LOADED
        assert last_log["details"]["model_version"] == "1.0.0"


def test_get_recent_events(audit_logger):
    """Testa recuperação de eventos recentes"""
    # Criar alguns eventos
    for i in range(5):
        audit_logger.log_event(
            event_type=AuditEventType.PREDICTION_SUCCESS, severity=AuditSeverity.INFO, details={"id": i}
        )

    # Recuperar eventos
    events = audit_logger.get_recent_events(limit=3)

    assert len(events) <= 3
    assert all(isinstance(e, dict) for e in events)


def test_get_recent_events_by_type(audit_logger):
    """Testa recuperação de eventos por tipo"""
    # Criar eventos de diferentes tipos
    audit_logger.log_event(event_type=AuditEventType.PREDICTION_SUCCESS, severity=AuditSeverity.INFO, details={})
    audit_logger.log_event(event_type=AuditEventType.LOGIN_SUCCESS, severity=AuditSeverity.INFO, details={})
    audit_logger.log_event(event_type=AuditEventType.PREDICTION_SUCCESS, severity=AuditSeverity.INFO, details={})

    # Recuperar apenas predições
    events = audit_logger.get_recent_events(event_type=AuditEventType.PREDICTION_SUCCESS)

    assert len(events) == 2
    assert all(e["event_type"] == AuditEventType.PREDICTION_SUCCESS for e in events)


def test_get_recent_events_by_severity(audit_logger):
    """Testa recuperação de eventos por severidade"""
    # Criar eventos de diferentes severidades
    audit_logger.log_event(event_type=AuditEventType.PREDICTION_SUCCESS, severity=AuditSeverity.INFO, details={})
    audit_logger.log_event(event_type=AuditEventType.SYSTEM_ERROR, severity=AuditSeverity.ERROR, details={})
    audit_logger.log_event(event_type=AuditEventType.UNAUTHORIZED_ACCESS, severity=AuditSeverity.CRITICAL, details={})

    # Recuperar apenas erros críticos
    events = audit_logger.get_recent_events(severity=AuditSeverity.CRITICAL)

    assert len(events) == 1
    assert events[0]["severity"] == AuditSeverity.CRITICAL


def test_get_statistics(audit_logger):
    """Testa obtenção de estatísticas"""
    # Criar eventos
    audit_logger.log_event(event_type=AuditEventType.PREDICTION_SUCCESS, severity=AuditSeverity.INFO, details={})
    audit_logger.log_event(event_type=AuditEventType.PREDICTION_SUCCESS, severity=AuditSeverity.INFO, details={})
    audit_logger.log_event(event_type=AuditEventType.LOGIN_SUCCESS, severity=AuditSeverity.INFO, details={})

    stats = audit_logger.get_statistics()

    assert isinstance(stats, dict)
    assert "total_events" in stats
    assert stats["total_events"] >= 3


def test_rotate_logs(audit_logger):
    """Testa rotação de logs"""
    # Criar arquivo de log antigo
    old_log = audit_logger.log_dir / "audit_2020-01-01.jsonl"
    old_log.write_text('{"event": "old"}\n')

    # Executar rotação (manter logs dos últimos 30 dias)
    audit_logger.rotate_logs(days=30)

    # Arquivo antigo deve ter sido removido
    assert not old_log.exists()


def test_multiple_events_same_file(audit_logger):
    """Testa múltiplos eventos no mesmo arquivo"""
    # Criar vários eventos
    for i in range(10):
        audit_logger.log_event(event_type=AuditEventType.PREDICTION_SUCCESS, severity=AuditSeverity.INFO, details={"id": i})

    # Verificar que todos estão no mesmo arquivo
    log_files = list(audit_logger.log_dir.glob("audit_*.jsonl"))
    assert len(log_files) == 1

    # Verificar que arquivo tem 10 linhas
    with open(log_files[0], "r") as f:
        lines = f.readlines()
        assert len(lines) == 10


def test_log_file_naming(audit_logger):
    """Testa nomenclatura do arquivo de log"""
    audit_logger.log_event(event_type=AuditEventType.PREDICTION_SUCCESS, severity=AuditSeverity.INFO, details={})

    log_files = list(audit_logger.log_dir.glob("audit_*.jsonl"))
    assert len(log_files) == 1

    # Nome deve conter data no formato YYYY-MM-DD
    filename = log_files[0].name
    assert filename.startswith("audit_")
    assert filename.endswith(".jsonl")


# ============================================================================
# Testes de Enums
# ============================================================================


def test_audit_event_type_values():
    """Testa valores do enum AuditEventType"""
    assert AuditEventType.LOGIN_SUCCESS == "login_success"
    assert AuditEventType.PREDICTION_REQUEST == "prediction_request"
    assert AuditEventType.SYSTEM_ERROR == "system_error"


def test_audit_severity_values():
    """Testa valores do enum AuditSeverity"""
    assert AuditSeverity.INFO == "info"
    assert AuditSeverity.WARNING == "warning"
    assert AuditSeverity.ERROR == "error"
    assert AuditSeverity.CRITICAL == "critical"
