"""
Testes Estendidos para o módulo de criptografia
Aumenta cobertura de 45% para 80%+
"""

import pytest
from app.security.encryption import (
    DataEncryption,
    PIIMasking,
    DataHashing,
    encrypt_pii,
    decrypt_pii,
    mask_for_log,
    sanitize_log_data,
)


@pytest.fixture
def encryption():
    """Fixture para criar instância de encryption"""
    return DataEncryption()


@pytest.fixture
def masker():
    """Fixture para PIIMasking"""
    return PIIMasking()


@pytest.fixture
def hasher():
    """Fixture para DataHashing"""
    return DataHashing()


# ============================================================================
# Testes para DataEncryption.encrypt_dict e decrypt_dict
# ============================================================================


def test_encrypt_dict(encryption):
    """Testa criptografia de campos específicos em dicionário"""
    data = {"nome": "João Silva", "cpf": "123.456.789-01", "idade": 35, "cidade": "São Paulo"}

    encrypted = encryption.encrypt_dict(data, ["nome", "cpf"])

    # Campos criptografados devem ser diferentes
    assert encrypted["nome"] != data["nome"]
    assert encrypted["cpf"] != data["cpf"]

    # Campos não especificados devem permanecer iguais
    assert encrypted["idade"] == data["idade"]
    assert encrypted["cidade"] == data["cidade"]


def test_decrypt_dict(encryption):
    """Testa descriptografia de campos específicos em dicionário"""
    data = {"nome": "João Silva", "cpf": "123.456.789-01", "idade": 35}

    encrypted = encryption.encrypt_dict(data, ["nome", "cpf"])
    decrypted = encryption.decrypt_dict(encrypted, ["nome", "cpf"])

    # Dados descriptografados devem ser iguais aos originais
    assert decrypted["nome"] == data["nome"]
    assert decrypted["cpf"] == data["cpf"]
    assert decrypted["idade"] == data["idade"]


def test_encrypt_dict_missing_field(encryption):
    """Testa criptografia quando campo não existe no dicionário"""
    data = {"nome": "João Silva"}

    # Não deve gerar erro se campo não existir
    encrypted = encryption.encrypt_dict(data, ["nome", "cpf"])

    assert "nome" in encrypted
    assert encrypted["nome"] != data["nome"]


def test_encrypt_dict_empty_value(encryption):
    """Testa criptografia de campo vazio"""
    data = {"nome": "", "cpf": "123.456.789-01"}

    encrypted = encryption.encrypt_dict(data, ["nome", "cpf"])

    # Campo vazio não deve ser criptografado
    assert encrypted["nome"] == ""
    assert encrypted["cpf"] != data["cpf"]


# ============================================================================
# Testes para PIIMasking
# ============================================================================


def test_mask_cpf_formatted(masker):
    """Testa mascaramento de CPF formatado"""
    cpf = "123.456.789-01"
    masked = masker.mask_cpf(cpf)
    assert masked == "***.***.***-01"


def test_mask_cpf_unformatted(masker):
    """Testa mascaramento de CPF sem formatação"""
    cpf = "12345678901"
    masked = masker.mask_cpf(cpf)
    assert masked == "***.***.***-01"


def test_mask_cpf_invalid(masker):
    """Testa mascaramento de CPF inválido"""
    cpf = "123"
    masked = masker.mask_cpf(cpf)
    assert masked == "***INVALID***"


def test_mask_cpf_empty(masker):
    """Testa mascaramento de CPF vazio"""
    masked = masker.mask_cpf("")
    assert masked == ""


def test_mask_email(masker):
    """Testa mascaramento de email"""
    email = "joao.silva@santander.com.br"
    masked = masker.mask_email(email)
    assert masked == "j***@santander.com.br"


def test_mask_email_short(masker):
    """Testa mascaramento de email curto"""
    email = "a@example.com"
    masked = masker.mask_email(email)
    assert masked == "*@example.com"


def test_mask_email_invalid(masker):
    """Testa mascaramento de email inválido"""
    email = "invalid-email"
    masked = masker.mask_email(email)
    assert masked == "***@***"


def test_mask_phone(masker):
    """Testa mascaramento de telefone"""
    phone = "(11) 98765-4321"
    masked = masker.mask_phone(phone)
    assert masked == "(11) ****-4321"


def test_mask_phone_unformatted(masker):
    """Testa mascaramento de telefone sem formatação"""
    phone = "11987654321"
    masked = masker.mask_phone(phone)
    assert masked == "(11) ****-4321"


def test_mask_phone_short(masker):
    """Testa mascaramento de telefone curto"""
    phone = "1234"
    masked = masker.mask_phone(phone)
    assert masked == "****-****"


def test_mask_account(masker):
    """Testa mascaramento de conta bancária"""
    account = "12345-6"
    masked = masker.mask_account(account)
    assert masked == "****5-6"


def test_mask_account_no_digit(masker):
    """Testa mascaramento de conta sem dígito"""
    account = "123456"
    masked = masker.mask_account(account)
    assert masked == "****56"


def test_mask_credit_card(masker):
    """Testa mascaramento de cartão de crédito"""
    card = "1234 5678 9012 3456"
    masked = masker.mask_credit_card(card)
    assert masked == "**** **** **** 3456"


def test_mask_credit_card_unformatted(masker):
    """Testa mascaramento de cartão sem formatação"""
    card = "1234567890123456"
    masked = masker.mask_credit_card(card)
    assert masked == "**** **** **** 3456"


def test_mask_credit_card_short(masker):
    """Testa mascaramento de cartão inválido"""
    card = "123"
    masked = masker.mask_credit_card(card)
    assert masked == "**** **** **** ****"


def test_mask_name(masker):
    """Testa mascaramento de nome"""
    name = "João da Silva"
    masked = masker.mask_name(name)
    assert masked == "J*** da S***"


def test_mask_name_single(masker):
    """Testa mascaramento de nome simples"""
    name = "João"
    masked = masker.mask_name(name)
    assert masked == "J***"


def test_mask_name_with_prepositions(masker):
    """Testa mascaramento de nome com preposições"""
    name = "Maria de Souza"
    masked = masker.mask_name(name)
    assert masked == "M*** de S***"


def test_mask_renda(masker):
    """Testa mascaramento de renda"""
    renda = 8500.00
    masked = masker.mask_renda(renda)
    assert masked == "R$ 8.5k"


def test_mask_renda_low(masker):
    """Testa mascaramento de renda baixa"""
    renda = 500.00
    masked = masker.mask_renda(renda)
    assert masked == "R$ 500"


def test_mask_renda_high(masker):
    """Testa mascaramento de renda alta"""
    renda = 1500000.00
    masked = masker.mask_renda(renda)
    assert masked == "R$ 1.5M"


# ============================================================================
# Testes para DataHashing
# ============================================================================


def test_hash_sha256(hasher):
    """Testa hash SHA-256"""
    data = "dados sensíveis"
    hash_value = hasher.hash_sha256(data)

    # Hash deve ter 64 caracteres (SHA-256)
    assert len(hash_value) == 64
    # Hash deve ser hexadecimal
    assert all(c in "0123456789abcdef" for c in hash_value)


def test_hash_sha256_consistency(hasher):
    """Testa consistência do hash SHA-256"""
    data = "dados sensíveis"
    hash1 = hasher.hash_sha256(data)
    hash2 = hasher.hash_sha256(data)

    # Mesmo dado deve gerar mesmo hash
    assert hash1 == hash2


def test_hash_sha256_different_data(hasher):
    """Testa que dados diferentes geram hashes diferentes"""
    hash1 = hasher.hash_sha256("dado1")
    hash2 = hasher.hash_sha256("dado2")

    assert hash1 != hash2


def test_hash_cpf(hasher):
    """Testa hash de CPF"""
    cpf = "123.456.789-01"
    hash_value = hasher.hash_cpf(cpf)

    # Hash deve ter 64 caracteres
    assert len(hash_value) == 64


def test_hash_cpf_consistency(hasher):
    """Testa consistência do hash de CPF"""
    cpf = "123.456.789-01"
    hash1 = hasher.hash_cpf(cpf)
    hash2 = hasher.hash_cpf(cpf)

    # Mesmo CPF deve gerar mesmo hash
    assert hash1 == hash2


def test_hash_cpf_formatted_vs_unformatted(hasher):
    """Testa que CPF formatado e não formatado geram mesmo hash"""
    cpf_formatted = "123.456.789-01"
    cpf_unformatted = "12345678901"

    hash1 = hasher.hash_cpf(cpf_formatted)
    hash2 = hasher.hash_cpf(cpf_unformatted)

    # Devem gerar o mesmo hash
    assert hash1 == hash2


def test_pseudonymize(hasher):
    """Testa pseudonimização"""
    data = "joao.silva@example.com"
    pseudo = hasher.pseudonymize(data)

    # Deve começar com prefixo padrão
    assert pseudo.startswith("PSE_")
    # Deve ter formato PSE_xxxxxxxx
    assert len(pseudo) == 12  # PSE_ + 8 caracteres


def test_pseudonymize_custom_prefix(hasher):
    """Testa pseudonimização com prefixo customizado"""
    data = "joao.silva@example.com"
    pseudo = hasher.pseudonymize(data, prefix="CLI")

    assert pseudo.startswith("CLI_")
    assert len(pseudo) == 12


def test_pseudonymize_consistency(hasher):
    """Testa consistência da pseudonimização"""
    data = "joao.silva@example.com"
    pseudo1 = hasher.pseudonymize(data)
    pseudo2 = hasher.pseudonymize(data)

    # Mesmo dado deve gerar mesmo pseudônimo
    assert pseudo1 == pseudo2


# ============================================================================
# Testes para funções de conveniência
# ============================================================================


def test_encrypt_pii():
    """Testa função de conveniência encrypt_pii"""
    data = "dados sensíveis"
    encrypted = encrypt_pii(data)

    assert encrypted != data
    assert len(encrypted) > 0


def test_decrypt_pii():
    """Testa função de conveniência decrypt_pii"""
    data = "dados sensíveis"
    encrypted = encrypt_pii(data)
    decrypted = decrypt_pii(encrypted)

    assert decrypted == data


def test_mask_for_log_cpf():
    """Testa mascaramento para log com CPF"""
    cpf = "123.456.789-01"
    masked = mask_for_log(cpf)

    assert masked == "***.***.***-01"


def test_mask_for_log_hash():
    """Testa mascaramento para log com hash"""
    hash_id = "a1b2c3d4e5f6g7h8i9j0"
    masked = mask_for_log(hash_id)

    assert masked == "a1b2...i9j0"


def test_mask_for_log_short():
    """Testa mascaramento para log com ID curto"""
    short_id = "abc"
    masked = mask_for_log(short_id)

    assert masked == "***"


def test_mask_for_log_empty():
    """Testa mascaramento para log com string vazia"""
    masked = mask_for_log("")

    assert masked == "***"


def test_sanitize_log_data():
    """Testa sanitização de dados para log"""
    data = {
        "cliente_id": "123.456.789-01",
        "nome": "João Silva",
        "email": "joao@example.com",
        "renda_mensal": 8500.00,
        "password": "senha123",
        "token": "abc123def456ghi789",
        "idade": 35,
    }

    sanitized = sanitize_log_data(data)

    # Campos sensíveis devem ser mascarados
    assert sanitized["cliente_id"] != data["cliente_id"]
    assert sanitized["nome"] != data["nome"]
    assert sanitized["email"] != data["email"]
    assert sanitized["password"] == "***"
    assert sanitized["token"] == "abc123de..."

    # Campos não sensíveis devem permanecer
    assert sanitized["idade"] == data["idade"]


def test_sanitize_log_data_missing_fields():
    """Testa sanitização quando campos sensíveis não existem"""
    data = {"idade": 35, "cidade": "São Paulo"}

    # Não deve gerar erro
    sanitized = sanitize_log_data(data)

    assert sanitized["idade"] == 35
    assert sanitized["cidade"] == "São Paulo"


def test_sanitize_log_data_none_values():
    """Testa sanitização com valores None"""
    data = {"cliente_id": None, "nome": None, "idade": 35}

    sanitized = sanitize_log_data(data)

    # Não deve gerar erro
    assert "idade" in sanitized
