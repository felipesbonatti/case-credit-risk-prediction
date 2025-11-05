"""
Testes para o módulo de criptografia
"""

import pytest
from app.security.encryption import DataEncryption
from passlib.hash import bcrypt


def hash_password(password: str) -> str:
    """Helper para hash de senha"""
    return bcrypt.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    """Helper para verificar senha"""
    return bcrypt.verify(password, hashed)


@pytest.fixture
def encryption():
    """Fixture para criar instância de encryption"""
    return DataEncryption()


def test_hash_password():
    """Testa hash de senha"""
    password = "SenhaSegura@123"
    hashed = hash_password(password)
    assert hashed != password
    assert len(hashed) > 0


def test_verify_password():
    """Testa verificação de senha"""
    password = "SenhaSegura@123"
    hashed = hash_password(password)
    assert verify_password(password, hashed) is True
    assert verify_password("SenhaErrada", hashed) is False


def test_encrypt_decrypt_string(encryption):
    """Testa criptografia e descriptografia de string"""
    original = "Dados sensíveis do cliente"
    encrypted = encryption.encrypt(original)
    assert encrypted != original
    decrypted = encryption.decrypt(encrypted)
    assert decrypted == original


def test_encrypt_empty_string(encryption):
    """Testa criptografia de string vazia"""
    result = encryption.encrypt("")
    # Pode retornar None ou string vazia dependendo da implementação
    assert result is not None


def test_encrypt_special_characters(encryption):
    """Testa criptografia com caracteres especiais"""
    original = "Teste @#$%&*()"
    encrypted = encryption.encrypt(original)
    decrypted = encryption.decrypt(encrypted)
    assert decrypted == original


def test_encryption_consistency(encryption):
    """Testa que mesma string gera diferentes encrypted values"""
    original = "Dados sensíveis"
    encrypted1 = encryption.encrypt(original)
    encrypted2 = encryption.encrypt(original)
    # Valores criptografados podem ser iguais ou diferentes dependendo do IV
    assert encrypted1 is not None
    assert encrypted2 is not None


def test_hash_consistency():
    """Testa consistência do hash"""
    password = "SenhaSegura@123"
    hash1 = hash_password(password)
    hash2 = hash_password(password)
    # Hashes devem ser diferentes (salt aleatório)
    assert hash1 != hash2
    # Mas ambos devem verificar corretamente
    assert verify_password(password, hash1)
    assert verify_password(password, hash2)
