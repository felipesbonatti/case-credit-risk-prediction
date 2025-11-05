"""
Módulo de Auditoria e Logging Seguro
Conformidade com LGPD e requisitos do Banco Central
"""

import structlog
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from enum import Enum
import json
from pathlib import Path

from app.security.encryption import sanitize_log_data, mask_for_log


# ============================================================================
# Configuração de Logging Estruturado
# ============================================================================


def setup_audit_logging():
    """
    Configura logging estruturado para auditoria

    Logs são salvos em formato JSON para fácil parsing e análise
    """
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


# ============================================================================
# Enums de Eventos de Auditoria
# ============================================================================


class AuditEventType(str, Enum):
    """Tipos de eventos auditáveis"""

    # Autenticação
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"
    TOKEN_REFRESH = "token_refresh"
    TOKEN_EXPIRED = "token_expired"

    # Predições
    PREDICTION_REQUEST = "prediction_request"
    PREDICTION_SUCCESS = "prediction_success"
    PREDICTION_FAILED = "prediction_failed"
    BATCH_PREDICTION = "batch_prediction"

    # Acesso a Dados
    DATA_ACCESS = "data_access"
    DATA_EXPORT = "data_export"

    # Administração
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    PERMISSION_CHANGED = "permission_changed"

    # Segurança
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    PERMISSION_DENIED = "permission_denied"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"

    # Sistema
    MODEL_LOADED = "model_loaded"
    MODEL_UPDATED = "model_updated"
    DRIFT_DETECTED = "drift_detected"
    SYSTEM_ERROR = "system_error"


class AuditSeverity(str, Enum):
    """Severidade do evento de auditoria"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


# ============================================================================
# Logger de Auditoria
# ============================================================================


class AuditLogger:
    """
    Logger especializado para auditoria bancária

    Registra todos os eventos relevantes para conformidade regulatória
    """

    def __init__(self, log_dir: Optional[str] = None):
        self.logger = structlog.get_logger("audit")
        # Usar diretório local ao invés de /var/log (requer permissões)
        if log_dir:
            self.log_dir = Path(log_dir)
        else:
            self.log_dir = Path.cwd().parent / "logs" / "audit"
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def log_event(
        self,
        event_type: AuditEventType,
        severity: AuditSeverity = AuditSeverity.INFO,
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        ip_address: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        compliance_flags: Optional[Dict[str, bool]] = None,
    ):
        """
        Registra evento de auditoria

        Args:
            event_type: Tipo do evento
            severity: Severidade do evento
            user_id: ID do usuário (se aplicável)
            username: Nome do usuário (se aplicável)
            ip_address: Endereço IP de origem
            details: Detalhes adicionais do evento
            compliance_flags: Flags de conformidade (LGPD, BACEN, etc.)
        """
        # Sanitizar dados sensíveis
        safe_details = sanitize_log_data(details) if details else {}

        # Preparar log entry
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type.value,
            "severity": severity.value,
            "user_id": user_id,
            "username": username,
            "ip_address": ip_address,
            "details": safe_details,
            "compliance": compliance_flags or {"lgpd_compliant": True, "bacen_audit": True, "pci_dss": False},
        }

        # Logar de acordo com severidade
        if severity == AuditSeverity.INFO:
            self.logger.info(event_type.value, **log_entry)
        elif severity == AuditSeverity.WARNING:
            self.logger.warning(event_type.value, **log_entry)
        elif severity == AuditSeverity.ERROR:
            self.logger.error(event_type.value, **log_entry)
        elif severity == AuditSeverity.CRITICAL:
            self.logger.critical(event_type.value, **log_entry)

        # Salvar em arquivo de auditoria
        self._save_to_audit_file(log_entry)

    def _save_to_audit_file(self, log_entry: dict):
        """
        Salva entrada de auditoria em arquivo dedicado

        Arquivo separado para facilitar análise e conformidade
        Usa formato audit_YYYY-MM-DD.jsonl
        """
        try:
            # Nome do arquivo com data
            today = datetime.now().strftime("%Y-%m-%d")
            audit_file = self.log_dir / f"audit_{today}.jsonl"
            
            with open(audit_file, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            self.logger.error(f"Failed to write audit log: {e}")

    # ========================================================================
    # Métodos de Conveniência
    # ========================================================================

    def log_login_success(self, user_id: str, username: str, ip_address: str, roles: list):
        """Registra login bem-sucedido"""
        self.log_event(
            event_type=AuditEventType.LOGIN_SUCCESS,
            severity=AuditSeverity.INFO,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            details={"roles": roles},
        )

    def log_login_failed(self, username: str, ip_address: str, reason: str):
        """Registra tentativa de login falhada"""
        self.log_event(
            event_type=AuditEventType.LOGIN_FAILED,
            severity=AuditSeverity.WARNING,
            username=username,
            ip_address=ip_address,
            details={"reason": reason},
        )

    def log_prediction(
        self,
        cliente_id: str,
        prediction: int,
        probability: float,
        recommendation: str,
        model_version: str,
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        ip_address: Optional[str] = None,
    ):
        """Registra predição de crédito"""
        # Alto risco (probability > 0.7) deve ter severidade WARNING
        severity = AuditSeverity.WARNING if probability > 0.7 else AuditSeverity.INFO
        
        self.log_event(
            event_type=AuditEventType.PREDICTION_SUCCESS,
            severity=severity,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            details={
                "cliente_id": mask_for_log(cliente_id),
                "prediction": prediction,
                "probability": round(probability, 4),
                "recommendation": recommendation,
                "model_version": model_version,
            },
            compliance_flags={"lgpd_compliant": True, "bacen_audit": True, "data_masked": True},
        )

    def log_unauthorized_access(
        self, user_id: Optional[str], username: Optional[str], ip_address: str, endpoint: str, reason: str
    ):
        """Registra tentativa de acesso não autorizado"""
        self.log_event(
            event_type=AuditEventType.UNAUTHORIZED_ACCESS,
            severity=AuditSeverity.ERROR,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            details={"endpoint": endpoint, "reason": reason},
        )

    def log_permission_denied(
        self, user_id: str, username: str, ip_address: str, required_permission: str, endpoint: str
    ):
        """Registra negação de permissão"""
        self.log_event(
            event_type=AuditEventType.PERMISSION_DENIED,
            severity=AuditSeverity.WARNING,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            details={"required_permission": required_permission, "endpoint": endpoint},
        )

    def log_rate_limit_exceeded(
        self, user_id: Optional[str], username: Optional[str], ip_address: str, endpoint: str, limit: int
    ):
        """Registra excesso de rate limit"""
        self.log_event(
            event_type=AuditEventType.RATE_LIMIT_EXCEEDED,
            severity=AuditSeverity.WARNING,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            details={"endpoint": endpoint, "limit": limit},
        )

    def log_model_drift(self, feature: str, ks_statistic: float, p_value: float, severity: str):
        """Registra detecção de drift no modelo"""
        self.log_event(
            event_type=AuditEventType.DRIFT_DETECTED,
            severity=AuditSeverity.WARNING if severity == "medium" else AuditSeverity.CRITICAL,
            details={"feature": feature, "ks_statistic": ks_statistic, "p_value": p_value, "severity": severity},
            compliance_flags={"lgpd_compliant": True, "bacen_audit": True, "model_risk_management": True},
        )

    def log_system_error(
        self, error_type: str, error_message: str, stack_trace: Optional[str] = None, user_id: Optional[str] = None
    ):
        """Registra erro de sistema"""
        self.log_event(
            event_type=AuditEventType.SYSTEM_ERROR,
            severity=AuditSeverity.ERROR,
            user_id=user_id,
            details={
                "error_type": error_type,
                "error_message": error_message,
                "stack_trace": stack_trace[:500] if stack_trace else None,  # Limita tamanho
            },
        )

    # ========================================================================
    # Métodos Adicionais para Testes Estendidos
    # ========================================================================

    def log_authentication(
        self,
        success: bool,
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        ip_address: Optional[str] = None,
        reason: Optional[str] = None,
    ):
        """Registra tentativa de autenticação"""
        if success:
            self.log_event(
                event_type=AuditEventType.LOGIN_SUCCESS,
                severity=AuditSeverity.INFO,
                user_id=user_id,
                username=username,
                ip_address=ip_address,
                details={"success": True},
            )
        else:
            self.log_event(
                event_type=AuditEventType.LOGIN_FAILED,
                severity=AuditSeverity.WARNING,
                username=username,
                ip_address=ip_address,
                details={"success": False, "reason": reason or "Invalid credentials"},
            )

    def log_data_access(
        self,
        resource: str,
        action: Optional[str] = None,
        operation: Optional[str] = None,
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        ip_address: Optional[str] = None,
        record_count: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Registra acesso a dados"""
        # Aceitar tanto 'action' quanto 'operation' para compatibilidade
        op = action or operation or "access"
        
        event_details = {
            "operation": op,
            "resource": resource,
        }
        
        if record_count is not None:
            event_details["record_count"] = record_count
        
        if details:
            event_details.update(details)
        
        self.log_event(
            event_type=AuditEventType.DATA_ACCESS,
            severity=AuditSeverity.INFO,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            details=event_details,
        )

    def log_security_event(
        self,
        event_type: Optional[AuditEventType] = None,
        event_description: Optional[str] = None,
        severity: AuditSeverity = AuditSeverity.WARNING,
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        ip_address: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Registra evento de segurança"""
        # Usar event_type fornecido ou padrão SUSPICIOUS_ACTIVITY
        evt_type = event_type or AuditEventType.SUSPICIOUS_ACTIVITY
        
        event_details = details.copy() if details else {}
        if event_description:
            event_details["description"] = event_description
        
        self.log_event(
            event_type=evt_type,
            severity=severity,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            details=event_details,
        )

    def log_model_event(
        self,
        event_type: Optional[AuditEventType] = None,
        event_description: Optional[str] = None,
        model_version: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Registra evento relacionado ao modelo"""
        # Usar event_type fornecido ou padrão MODEL_LOADED
        evt_type = event_type or AuditEventType.MODEL_LOADED
        
        event_details = details.copy() if details else {}
        if event_description:
            event_details["description"] = event_description
        if model_version:
            event_details["model_version"] = model_version
        
        self.log_event(
            event_type=evt_type,
            severity=AuditSeverity.INFO,
            details=event_details,
        )

    def get_recent_events(
        self,
        limit: int = 100,
        event_type: Optional[AuditEventType] = None,
        severity: Optional[AuditSeverity] = None,
    ) -> list:
        """
        Retorna eventos recentes de auditoria
        
        Args:
            limit: Número máximo de eventos a retornar
            event_type: Filtrar por tipo de evento
            severity: Filtrar por severidade
            
        Returns:
            Lista de eventos de auditoria
        """
        events = []
        
        # Ler todos os arquivos de log do diretório
        log_files = sorted(self.log_dir.glob("audit_*.jsonl"), reverse=True)
        
        for log_file in log_files:
            try:
                with open(log_file, "r") as f:
                    for line in f:
                        try:
                            event = json.loads(line.strip())
                            
                            # Aplicar filtros
                            if event_type and event.get("event_type") != event_type.value:
                                continue
                            
                            if severity and event.get("severity") != severity.value:
                                continue
                            
                            events.append(event)
                            
                            if len(events) >= limit:
                                return events
                        except json.JSONDecodeError:
                            continue
            except Exception:
                continue
        
        return events

    def get_statistics(self, days: int = 7) -> dict:
        """
        Retorna estatísticas de auditoria
        
        Args:
            days: Número de dias para análise
            
        Returns:
            Dicionário com estatísticas
        """
        events = self.get_recent_events(limit=10000)
        
        # Filtrar por período
        cutoff_date = datetime.now() - timedelta(days=days)
        filtered_events = []
        
        for event in events:
            try:
                event_date = datetime.fromisoformat(event.get("timestamp", ""))
                if event_date >= cutoff_date:
                    filtered_events.append(event)
            except (ValueError, TypeError):
                continue
        
        # Calcular estatísticas
        stats = {
            "total_events": len(filtered_events),
            "period_days": days,
            "events_by_type": {},
            "events_by_severity": {},
            "unique_users": set(),
            "unique_ips": set(),
        }
        
        for event in filtered_events:
            # Por tipo
            event_type = event.get("event_type", "unknown")
            stats["events_by_type"][event_type] = stats["events_by_type"].get(event_type, 0) + 1
            
            # Por severidade
            severity = event.get("severity", "unknown")
            stats["events_by_severity"][severity] = stats["events_by_severity"].get(severity, 0) + 1
            
            # Usuários únicos
            if event.get("user_id"):
                stats["unique_users"].add(event["user_id"])
            
            # IPs únicos
            if event.get("ip_address"):
                stats["unique_ips"].add(event["ip_address"])
        
        # Converter sets para contadores
        stats["unique_users"] = len(stats["unique_users"])
        stats["unique_ips"] = len(stats["unique_ips"])
        
        return stats

    def rotate_logs(self, days: int = 90, days_to_keep: Optional[int] = None):
        """
        Remove logs de auditoria antigos
        
        Args:
            days: Número de dias de logs para manter (alias para days_to_keep)
            days_to_keep: Número de dias de logs para manter (deprecated)
        """
        # Aceitar tanto 'days' quanto 'days_to_keep' para compatibilidade
        keep_days = days_to_keep if days_to_keep is not None else days
        cutoff_date = datetime.now() - timedelta(days=keep_days)
        
        log_files = list(self.log_dir.glob("audit_*.jsonl"))
        
        for log_file in log_files:
            try:
                # Extrair data do nome do arquivo (audit_YYYY-MM-DD.jsonl)
                date_str = log_file.stem.replace("audit_", "")
                file_date = datetime.strptime(date_str, "%Y-%m-%d")
                
                if file_date < cutoff_date:
                    log_file.unlink()
            except (ValueError, OSError):
                continue


# ============================================================================
# Instância Global
# ============================================================================

audit_logger = AuditLogger()


# ============================================================================
# Decorators para Auditoria Automática
# ============================================================================


def audit_endpoint(event_type: AuditEventType):
    """
    Decorator para auditar automaticamente endpoints

    Usage:
        @router.post("/predict")
        @audit_endpoint(AuditEventType.PREDICTION_REQUEST)
        async def predict(...):
            ...
    """

    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extrair informações do request
            request = kwargs.get("req") or kwargs.get("request")
            current_user = kwargs.get("current_user")

            # Logar início da operação
            audit_logger.log_event(
                event_type=event_type,
                severity=AuditSeverity.INFO,
                user_id=current_user.user_id if current_user else None,
                username=current_user.username if current_user else None,
                ip_address=request.client.host if request else None,
                details={"endpoint": func.__name__},
            )

            # Executar função
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                # Logar erro
                audit_logger.log_system_error(
                    error_type=type(e).__name__,
                    error_message=str(e),
                    user_id=current_user.user_id if current_user else None,
                )
                raise

        return wrapper

    return decorator


# ============================================================================
# Funções de Análise de Logs
# ============================================================================


def analyze_audit_logs(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    event_type: Optional[AuditEventType] = None,
    user_id: Optional[str] = None,
) -> list:
    """
    Analisa logs de auditoria

    Args:
        start_date: Data inicial
        end_date: Data final
        event_type: Filtrar por tipo de evento
        user_id: Filtrar por usuário

    Returns:
        Lista de eventos de auditoria
    """
    audit_file = Path("/var/log/santander/audit.log")

    if not audit_file.exists():
        return []

    events = []

    with open(audit_file, "r") as f:
        for line in f:
            try:
                event = json.loads(line)

                # Aplicar filtros
                if start_date and datetime.fromisoformat(event["timestamp"]) < start_date:
                    continue

                if end_date and datetime.fromisoformat(event["timestamp"]) > end_date:
                    continue

                if event_type and event["event_type"] != event_type.value:
                    continue

                if user_id and event.get("user_id") != user_id:
                    continue

                events.append(event)
            except (json.JSONDecodeError, KeyError, ValueError):
                continue

    return events


def get_audit_summary(days: int = 7) -> dict:
    """
    Gera resumo de auditoria dos últimos N dias

    Args:
        days: Número de dias para análise

    Returns:
        Dicionário com estatísticas
    """
    start_date = datetime.utcnow() - timedelta(days=days)
    events = analyze_audit_logs(start_date=start_date)

    summary = {
        "total_events": len(events),
        "period_days": days,
        "events_by_type": {},
        "events_by_severity": {},
        "events_by_user": {},
        "failed_logins": 0,
        "unauthorized_access": 0,
        "predictions_made": 0,
    }

    for event in events:
        # Por tipo
        event_type = event["event_type"]
        summary["events_by_type"][event_type] = summary["events_by_type"].get(event_type, 0) + 1

        # Por severidade
        severity = event["severity"]
        summary["events_by_severity"][severity] = summary["events_by_severity"].get(severity, 0) + 1

        # Por usuário
        username = event.get("username", "unknown")
        summary["events_by_user"][username] = summary["events_by_user"].get(username, 0) + 1

        # Métricas específicas
        if event_type == AuditEventType.LOGIN_FAILED.value:
            summary["failed_logins"] += 1
        elif event_type == AuditEventType.UNAUTHORIZED_ACCESS.value:
            summary["unauthorized_access"] += 1
        elif event_type == AuditEventType.PREDICTION_SUCCESS.value:
            summary["predictions_made"] += 1

    return summary

