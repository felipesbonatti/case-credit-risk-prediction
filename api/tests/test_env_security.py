"""
Testes de segurança e validação do .env
"""

import pytest
from pathlib import Path


def test_env_exists():
    """
    Verifica se o arquivo .env existe
    """
    project_root = Path(__file__).parent.parent.parent
    env_file = project_root / ".env"
    assert env_file.exists(), "Arquivo .env não encontrado"


def test_env_security():
    """
    Verifica se o .env contém as variáveis de segurança necessárias
    """
    project_root = Path(__file__).parent.parent.parent
    env_file = project_root / ".env"

    with open(env_file, "r") as f:
        content = f.read()

    # Verificar variáveis obrigatórias
    assert "SECRET_KEY" in content, "SECRET_KEY não encontrada no .env"
    assert "DATA_PATH" in content, "DATA_PATH não encontrada no .env"

    # Verificar que não há caminhos absolutos hardcoded (Windows/Linux específicos)
    assert "C:/" not in content, "Caminho absoluto Windows encontrado no .env"
    assert "C:\\" not in content, "Caminho absoluto Windows encontrado no .env"
    assert "/home/" not in content or "${PROJECT_ROOT}" in content, "Caminho absoluto Linux hardcoded encontrado"


def test_env_no_hardcoded_credentials():
    """
    Verifica que não há credenciais hardcoded no código Python
    """
    project_root = Path(__file__).parent.parent.parent

    # Verificar arquivos Python principais
    files_to_check = [
        project_root / "api" / "app" / "main.py",
        project_root / "api" / "app" / "utils" / "config.py",
    ]

    for file_path in files_to_check:
        if file_path.exists():
            with open(file_path, "r") as f:
                content = f.read()

            # Não deve haver SECRET_KEY hardcoded
            assert (
                'SECRET_KEY = "' not in content or "os.getenv" in content
            ), f"SECRET_KEY hardcoded encontrada em {file_path.name}"


def test_env_dynamic_paths():
    """
    Verifica se os caminhos são dinâmicos usando PROJECT_ROOT
    """
    project_root = Path(__file__).parent.parent.parent
    env_file = project_root / ".env"

    with open(env_file, "r") as f:
        content = f.read()

    # DATA_PATH deve usar ${PROJECT_ROOT} ou ser relativo
    data_path_line = [line for line in content.split("\n") if "DATA_PATH" in line and not line.strip().startswith("#")]

    if data_path_line:
        assert (
            "${PROJECT_ROOT}" in data_path_line[0] or "C:/" not in data_path_line[0]
        ), "DATA_PATH deve usar ${PROJECT_ROOT} para ser universal"


def test_rate_limit_disabled():
    """
    Verifica se rate limiting está desabilitado para desenvolvimento
    """
    project_root = Path(__file__).parent.parent.parent
    env_file = project_root / ".env"

    with open(env_file, "r") as f:
        content = f.read()

    # RATE_LIMIT_ENABLED deve estar false
    assert "RATE_LIMIT_ENABLED=false" in content, "RATE_LIMIT_ENABLED deve estar false para desenvolvimento"
