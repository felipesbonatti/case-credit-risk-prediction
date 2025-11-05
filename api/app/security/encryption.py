"""
Módulo de Criptografia de Dados Sensíveis
Implementação LGPD-compliant para dados bancários
"""

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64
import hashlib
import re
from typing import Optional
import structlog

logger = structlog.get_logger()

# TODO: Mover para AWS Secrets Manager ou Vault
ENCRYPTION_KEY = b"CHANGE-THIS-IN-PRODUCTION-USE-32-BYTE-KEY-FROM-VAULT"
SALT = b"santander-salt-change-in-production"


class DataEncryption:
    """
    Classe para criptografia de dados sensíveis (PII)

    Usa Fernet (AES-128 em modo CBC) para criptografia simétrica
    """

    def __init__(self, key: Optional[bytes] = None):
        """
        Inicializa encryptor com chave

        Args:
            key: Chave de criptografia (32 bytes). Se None, usa chave padrão.
        """
        if key is None:
            # Derivar chave a partir da master key usando PBKDF2
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(), length=32, salt=SALT, iterations=100000, backend=default_backend()
            )
            key = base64.urlsafe_b64encode(kdf.derive(ENCRYPTION_KEY))

        self.cipher = Fernet(key)
        logger.info("Encryption module initialized")

    def encrypt(self, data: str) -> str:
        """
        Criptografa string

        Args:
            data: Dados em texto plano

        Returns:
            Dados criptografados (base64)
        """
        if not data:
            return ""

        try:
            encrypted = self.cipher.encrypt(data.encode("utf-8"))
            return encrypted.decode("utf-8")
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise

    def decrypt(self, encrypted_data: str) -> str:
        """
        Descriptografa string

        Args:
            encrypted_data: Dados criptografados (base64)

        Returns:
            Dados em texto plano
        """
        if not encrypted_data:
            return ""

        try:
            decrypted = self.cipher.decrypt(encrypted_data.encode("utf-8"))
            return decrypted.decode("utf-8")
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise

    def encrypt_dict(self, data: dict, fields: list) -> dict:
        """
        Criptografa campos específicos de um dicionário

        Args:
            data: Dicionário com dados
            fields: Lista de campos a criptografar

        Returns:
            Dicionário com campos criptografados
        """
        encrypted_data = data.copy()

        for field in fields:
            if field in encrypted_data and encrypted_data[field]:
                encrypted_data[field] = self.encrypt(str(encrypted_data[field]))

        return encrypted_data

    def decrypt_dict(self, data: dict, fields: list) -> dict:
        """
        Descriptografa campos específicos de um dicionário

        Args:
            data: Dicionário com dados criptografados
            fields: Lista de campos a descriptografar

        Returns:
            Dicionário com campos descriptografados
        """
        decrypted_data = data.copy()

        for field in fields:
            if field in decrypted_data and decrypted_data[field]:
                decrypted_data[field] = self.decrypt(decrypted_data[field])

        return decrypted_data


class PIIMasking:
    """
    Classe para mascaramento de dados sensíveis (PII) em logs

    Implementa mascaramento conforme LGPD
    """

    @staticmethod
    def mask_cpf(cpf: str) -> str:
        """
        Mascara CPF: 123.456.789-01 → ***.***.***-01
        """
        if not cpf:
            return ""

        # Remove formatação
        cpf_clean = re.sub(r"[^\d]", "", cpf)

        if len(cpf_clean) != 11:
            return "***INVALID***"

        # Mascara primeiros 9 dígitos
        return f"***.***.***-{cpf_clean[-2:]}"

    @staticmethod
    def mask_email(email: str) -> str:
        """
        Mascara email: joao.silva@santander.com.br → j***@santander.com.br
        """
        if not email or "@" not in email:
            return "***@***"

        local, domain = email.split("@", 1)

        if len(local) <= 1:
            masked_local = "*"
        else:
            masked_local = local[0] + "***"

        return f"{masked_local}@{domain}"

    @staticmethod
    def mask_phone(phone: str) -> str:
        """
        Mascara telefone: (11) 98765-4321 → (11) ****-4321
        """
        if not phone:
            return ""

        # Remove formatação
        phone_clean = re.sub(r"[^\d]", "", phone)

        if len(phone_clean) < 8:
            return "****-****"

        # Mascara dígitos do meio
        return f"({phone_clean[:2]}) ****-{phone_clean[-4:]}"

    @staticmethod
    def mask_account(account: str) -> str:
        """
        Mascara conta bancária: 12345-6 → ****5-6
        """
        if not account:
            return ""

        if "-" in account:
            number, digit = account.split("-", 1)
            return f"****{number[-1]}-{digit}"
        else:
            return f"****{account[-2:]}"

    @staticmethod
    def mask_credit_card(card: str) -> str:
        """
        Mascara cartão: 1234 5678 9012 3456 → **** **** **** 3456
        """
        if not card:
            return ""

        # Remove formatação
        card_clean = re.sub(r"[^\d]", "", card)

        if len(card_clean) < 13:
            return "**** **** **** ****"

        # Mostra apenas últimos 4 dígitos
        return f"**** **** **** {card_clean[-4:]}"

    @staticmethod
    def mask_name(name: str) -> str:
        """
        Mascara nome: João da Silva → J*** da S***
        """
        if not name:
            return ""

        parts = name.split()

        masked_parts = []
        for part in parts:
            if len(part) <= 2:
                masked_parts.append(part)  # Mantém preposições
            else:
                masked_parts.append(f"{part[0]}***")

        return " ".join(masked_parts)

    @staticmethod
    def mask_renda(renda: float) -> str:
        """
        Mascara renda: 8500.00 → R$ 8.5k
        """
        if renda < 1000:
            return f"R$ {int(renda)}"
        elif renda < 1000000:
            return f"R$ {renda/1000:.1f}k"
        else:
            return f"R$ {renda/1000000:.1f}M"


class DataHashing:
    """
    Classe para hashing irreversível de dados

    Usado para identificadores únicos sem expor dados reais
    """

    @staticmethod
    def hash_sha256(data: str) -> str:
        """
        Gera hash SHA-256 de string

        Args:
            data: Dados a serem hasheados

        Returns:
            Hash hexadecimal (64 caracteres)
        """
        return hashlib.sha256(data.encode("utf-8")).hexdigest()

    @staticmethod
    def hash_cpf(cpf: str) -> str:
        """
        Gera hash de CPF para uso como identificador único

        Args:
            cpf: CPF em qualquer formato

        Returns:
            Hash SHA-256 do CPF
        """
        # Remove formatação
        cpf_clean = re.sub(r"[^\d]", "", cpf)

        # Adiciona salt
        salted = f"{cpf_clean}:{SALT.decode('utf-8')}"

        return hashlib.sha256(salted.encode("utf-8")).hexdigest()

    @staticmethod
    def pseudonymize(data: str, prefix: str = "PSE") -> str:
        """
        Cria pseudônimo para dados sensíveis

        Args:
            data: Dados a pseudonimizar
            prefix: Prefixo do pseudônimo

        Returns:
            Pseudônimo (ex: PSE_a1b2c3d4)
        """
        hash_value = hashlib.sha256(data.encode("utf-8")).hexdigest()[:8]
        return f"{prefix}_{hash_value}"


# Instância global para uso em toda aplicação
encryptor = DataEncryption()
masker = PIIMasking()
hasher = DataHashing()


# ============================================================================
# Funções de Conveniência
# ============================================================================


def encrypt_pii(data: str) -> str:
    """Criptografa dado sensível"""
    return encryptor.encrypt(data)


def decrypt_pii(encrypted_data: str) -> str:
    """Descriptografa dado sensível"""
    return encryptor.decrypt(encrypted_data)


def mask_for_log(cliente_id: str) -> str:
    """
    Mascara cliente_id para uso em logs

    Se for CPF: mascara
    Se for hash: mostra primeiros e últimos 4 caracteres
    """
    if not cliente_id:
        return "***"

    # Verifica se é CPF
    cpf_clean = re.sub(r"[^\d]", "", cliente_id)
    if len(cpf_clean) == 11:
        return masker.mask_cpf(cliente_id)

    # Se for hash ou outro identificador
    if len(cliente_id) > 8:
        return f"{cliente_id[:4]}...{cliente_id[-4:]}"

    return "***"


def sanitize_log_data(data: dict) -> dict:
    """
    Remove/mascara dados sensíveis de dicionário para logging seguro

    Args:
        data: Dicionário com dados potencialmente sensíveis

    Returns:
        Dicionário com dados mascarados
    """
    sanitized = data.copy()

    # Campos a mascarar
    sensitive_fields = {
        "cliente_id": lambda x: mask_for_log(x),
        "cpf": lambda x: masker.mask_cpf(x),
        "email": lambda x: masker.mask_email(x),
        "telefone": lambda x: masker.mask_phone(x),
        "nome": lambda x: masker.mask_name(x),
        "renda_mensal": lambda x: masker.mask_renda(x),
        "password": lambda x: "***",
        "token": lambda x: f"{x[:8]}..." if x else "***",
        "access_token": lambda x: f"{x[:8]}..." if x else "***",
        "refresh_token": lambda x: f"{x[:8]}..." if x else "***",
    }

    for field, mask_func in sensitive_fields.items():
        if field in sanitized and sanitized[field]:
            try:
                sanitized[field] = mask_func(sanitized[field])
            except (TypeError, ValueError, AttributeError):
                sanitized[field] = "***"

    return sanitized
