#!/usr/bin/env python3
"""
Script Universal de Inicialização - Santander Credit Risk Platform
Executa todo o pipeline: setup → dados → modelo → testes → API + Dashboard Premium

 COMPATÍVEL COM QUALQUER MÁQUINA: Windows, Linux, macOS
 DETECÇÃO AVANÇADA DE NPM NO WINDOWS
"""

import os
import sys
import subprocess
import platform
from pathlib import Path
import time
import webbrowser

# Cores para terminal (compatível com Windows 10+)
if platform.system() == "Windows":
    try:
        os.system("color")  # Habilitar cores no Windows
    except:
        pass

RESET = "\033[0m"
BOLD = "\033[1m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"

# Variável global para armazenar o gerenciador de pacotes escolhido
PACKAGE_MANAGER = None
NPM_PATH = None


def print_header(text):
    """Imprime cabeçalho formatado"""
    print(f"\n{BOLD}{BLUE}{'=' * 70}{RESET}")
    print(f"{BOLD}{BLUE}{text:^70}{RESET}")
    print(f"{BOLD}{BLUE}{'=' * 70}{RESET}\n")


def print_success(text):
    """Imprime mensagem de sucesso"""
    print(f"{GREEN}OK {text}{RESET}")


def print_error(text):
    """Imprime mensagem de erro"""
    print(f"{RED}ERRO {text}{RESET}")


def print_warning(text):
    """Imprime mensagem de aviso"""
    print(f"{YELLOW} {text}{RESET}")


def print_info(text):
    """Imprime mensagem informativa"""
    print(f"{BLUE} {text}{RESET}")


def run_command(command, description, cwd=None, check=True, shell=False):
    """
    Executa comando e exibe resultado
    """
    print_info(f"{description}...")

    try:
        if isinstance(command, str) or shell:
            result = subprocess.run(
                command, shell=True, cwd=cwd, capture_output=True, text=True, check=check
            )
        else:
            result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=check)

        if result.returncode == 0:
            print_success(f"{description} - Concluído")
            return True
        else:
            print_error(f"{description} - Falhou")
            if result.stderr:
                print(f"  Erro: {result.stderr[:200]}")
            return False

    except subprocess.CalledProcessError as e:
        print_error(f"{description} - Falhou")
        print(f"  Erro: {e.stderr[:200] if e.stderr else str(e)}")
        if check:
            raise
        return False
    except Exception as e:
        print_error(f"{description} - Falhou")
        print(f"  Erro: {str(e)}")
        if check:
            raise
        return False


def find_npm_windows():
    """Busca npm em locais comuns do Windows"""
    possible_paths = [
        # Node.js instalado via instalador oficial
        os.path.expandvars(r"%ProgramFiles%\nodejs\npm.cmd"),
        os.path.expandvars(r"%ProgramFiles(x86)%\nodejs\npm.cmd"),
        
        # Node.js instalado via nvm-windows
        os.path.expandvars(r"%NVM_HOME%\npm.cmd"),
        os.path.expandvars(r"%APPDATA%\nvm\npm.cmd"),
        
        # Node.js instalado via Chocolatey
        os.path.expandvars(r"%ChocolateyInstall%\bin\npm.cmd"),
        
        # Node.js instalado via Scoop
        os.path.expandvars(r"%USERPROFILE%\scoop\shims\npm.cmd"),
        
        # Localização do usuário
        os.path.expandvars(r"%APPDATA%\npm\npm.cmd"),
        os.path.expandvars(r"%USERPROFILE%\AppData\Roaming\npm\npm.cmd"),
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    return None


def check_command_exists(command):
    """Verifica se um comando existe no sistema"""
    try:
        result = subprocess.run(
            [command, "--version"], 
            capture_output=True, 
            text=True,
            timeout=5,
            shell=True if platform.system() == "Windows" else False
        )
        return result.returncode == 0
    except:
        return False


def check_node_installed():
    """Verifica se Node.js está instalado"""
    try:
        result = subprocess.run(
            ["node", "--version"], 
            capture_output=True, 
            text=True, 
            timeout=5,
            shell=True if platform.system() == "Windows" else False
        )
        if result.returncode == 0:
            version = result.stdout.strip()
            print_success(f"Node.js {version} detectado")
            return True
    except:
        pass
    
    print_error("Node.js não encontrado!")
    print_info("O dashboard premium requer Node.js 18+")
    print_info("Baixe em: https://nodejs.org/")
    return False


def detect_package_manager():
    """Detecta qual gerenciador de pacotes usar (pnpm ou npm)"""
    global PACKAGE_MANAGER, NPM_PATH
    
    # Tentar pnpm primeiro
    if check_command_exists("pnpm"):
        try:
            result = subprocess.run(
                ["pnpm", "--version"], 
                capture_output=True, 
                text=True, 
                timeout=5,
                shell=True if platform.system() == "Windows" else False
            )
            if result.returncode == 0:
                version = result.stdout.strip()
                print_success(f"pnpm {version} detectado - Usando pnpm")
                PACKAGE_MANAGER = "pnpm"
                return "pnpm"
        except:
            pass
    
    # Tentar npm no PATH
    if check_command_exists("npm"):
        try:
            result = subprocess.run(
                ["npm", "--version"], 
                capture_output=True, 
                text=True, 
                timeout=5,
                shell=True if platform.system() == "Windows" else False
            )
            if result.returncode == 0:
                version = result.stdout.strip()
                print_success(f"npm {version} detectado - Usando npm")
                PACKAGE_MANAGER = "npm"
                NPM_PATH = "npm"
                return "npm"
        except:
            pass
    
    # No Windows, buscar npm em locais comuns
    if platform.system() == "Windows":
        print_warning("npm não encontrado no PATH, buscando em locais comuns...")
        npm_path = find_npm_windows()
        if npm_path:
            try:
                result = subprocess.run(
                    [npm_path, "--version"], 
                    capture_output=True, 
                    text=True, 
                    timeout=5,
                    shell=True
                )
                if result.returncode == 0:
                    version = result.stdout.strip()
                    print_success(f"npm {version} encontrado em: {npm_path}")
                    print_success("Usando npm")
                    PACKAGE_MANAGER = "npm"
                    NPM_PATH = npm_path
                    return "npm"
            except:
                pass
    
    print_error("Nenhum gerenciador de pacotes encontrado!")
    print_warning("O npm deveria vir instalado com o Node.js")
    print_info("Tente reinstalar o Node.js de: https://nodejs.org/")
    print_info("Durante a instalação, certifique-se de marcar 'Add to PATH'")
    return None


def generate_env_file():
    """Gera arquivo .env se não existir"""
    env_path = Path(".env")
    
    if env_path.exists():
        print_warning("Arquivo .env já existe - Pulando criação automática.")
        return True # Se já existe, não sobrescrevemos.
    
    # Se não existe, copiamos do .env.example
    example_path = Path(".env.example")
    if example_path.exists():
        try:
            import shutil
            shutil.copy(example_path, env_path)
            print_success("Arquivo .env criado a partir de .env.example")
            return True
        except Exception as e:
            print_error(f"Erro ao copiar .env.example para .env: {e}")
            return False
    else:
        print_error("Arquivo .env.example não encontrado. Não é possível criar .env.")
        return False
    
    print_info("Gerando arquivo .env...")
    
    import secrets
    secret_key = secrets.token_urlsafe(32)
    
    env_content = f"""# Santander Credit Risk Platform - Environment Variables
# Gerado automaticamente em {time.strftime('%Y-%m-%d %H:%M:%S')}

# Security
SECRET_KEY={secret_key}
ENCRYPTION_KEY={secrets.token_urlsafe(32)}

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true
API_WORKERS=1

# Database
DATABASE_URL=sqlite:///./santander_credit_risk.db

# Redis
REDIS_URL=redis://localhost:6379/0

# Logging
LOG_LEVEL=INFO

# CORS
CORS_ORIGINS=["http://localhost:5173","http://localhost:3000","http://localhost:8501"]

# Rate Limiting
RATE_LIMIT_ENABLED=false
RATE_LIMIT_PER_MINUTE=60

# Debug
DEBUG=true
"""
    
    try:
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write(env_content)
        print_success("Arquivo .env gerado com sucesso")
        return True
    except Exception as e:
        print_error(f"Erro ao gerar .env: {e}")
        return False


def generate_api_env():
    """Gera arquivo .env para a API"""
    api_env_path = Path("api") / ".env"
    
    if api_env_path.exists():
        print_warning("Arquivo .env da API já existe")
        return True
    
    print_info("Gerando arquivo .env da API...")
    
    import secrets
    secret_key = secrets.token_urlsafe(32)
    
    env_content = f"""# API Configuration
APP_ENV=development
DEBUG=true
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true
API_WORKERS=1

# Security
SECRET_KEY={secret_key}
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
CORS_ORIGINS=["http://localhost:5173","http://localhost:3000","http://localhost:8000"]

# Rate Limiting
RATE_LIMIT_ENABLED=false
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_PERIOD=60

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Database (opcional)
DATABASE_URL=sqlite:///./credit_risk.db

# Redis (opcional)
REDIS_URL=redis://localhost:6379/0
REDIS_ENABLED=false

# Model
MODEL_PATH=modelo_lgbm.pkl
MODEL_VERSION=1.0.0-lgbm
"""
    
    try:
        with open(api_env_path, 'w', encoding='utf-8') as f:
            f.write(env_content)
        print_success("Arquivo .env da API gerado com sucesso")
        return True
    except Exception as e:
        print_error(f"Erro ao gerar .env da API: {e}")
        return False


def generate_dashboard_env():
    """Gera arquivo .env para o dashboard premium"""
    dashboard_env_path = Path("dashboard_premium") / ".env"
    
    if dashboard_env_path.exists():
        print_warning("Arquivo .env do dashboard já existe")
        return True
    
    print_info("Gerando arquivo .env do dashboard...")
    
    env_content = """VITE_API_URL=http://localhost:8000
VITE_APP_TITLE=Santander Credit Risk Dashboard
"""
    
    try:
        with open(dashboard_env_path, 'w', encoding='utf-8') as f:
            f.write(env_content)
        print_success("Arquivo .env do dashboard gerado com sucesso")
        return True
    except Exception as e:
        print_error(f"Erro ao gerar .env do dashboard: {e}")
        return False


def check_python_version():
    """Verifica versão do Python"""
    print_header("VERIFICANDO AMBIENTE")

    version = sys.version_info
    print_info(f"Python {version.major}.{version.minor}.{version.micro}")
    print_info(f"Sistema Operacional: {platform.system()} {platform.release()}")

    if version.major < 3 or (version.major == 3 and version.minor < 11):
        print_error("Python 3.11+ é necessário")
        return False

    print_success("Versão do Python compatível")
    
    # Verificar Node.js
    if not check_node_installed():
        return False
    
    # Detectar gerenciador de pacotes
    pm = detect_package_manager()
    if not pm:
        return False
    
    return True


def install_python_dependencies():
    """Instala dependências Python"""
    print_header("INSTALANDO DEPENDÊNCIAS PYTHON")

    # Atualizar pip
    run_command([sys.executable, "-m", "pip", "install", "--upgrade", "pip", "-q"], "Atualizando pip", check=False)

    # Instalar dependências da API
    if not run_command(
        [sys.executable, "-m", "pip", "install", "-r", "api/requirements.txt", "-q"], 
        "Instalando dependências da API",
        check=False
    ):
        print_warning("Algumas dependências podem ter falhado, continuando...")

    # Instalar dependências adicionais
    additional_deps = ["pyarrow", "joblib", "scikit-learn", "lightgbm"]
    for dep in additional_deps:
        run_command(
            [sys.executable, "-m", "pip", "install", dep, "-q"], 
            f"Instalando {dep}",
            check=False
        )

    print_success("Dependências Python instaladas")
    return True


def install_dashboard_dependencies():
    """Instala dependências do dashboard premium"""
    global PACKAGE_MANAGER, NPM_PATH
    
    print_header("INSTALANDO DEPENDÊNCIAS DO DASHBOARD")

    dashboard_dir = Path("dashboard_premium")
    
    if not dashboard_dir.exists():
        print_error("Diretório dashboard_premium não encontrado")
        return False

    # Verificar se node_modules existe
    if (dashboard_dir / "node_modules").exists():
        print_warning("Dependências do dashboard já instaladas")
        return True

    # Preparar comando baseado no gerenciador
    if PACKAGE_MANAGER == "pnpm":
        command = "pnpm install"
    else:
        # Usar caminho completo do npm se disponível
        if NPM_PATH and NPM_PATH != "npm":
            command = f'"{NPM_PATH}" install'
        else:
            command = "npm install"

    print_info(f"Usando {PACKAGE_MANAGER} para instalar dependências...")
    
    # Instalar dependências
    if not run_command(
        command,
        f"Instalando dependências do dashboard com {PACKAGE_MANAGER} (isso pode demorar...)",
        cwd=str(dashboard_dir),
        shell=True,
        check=False
    ):
        print_error(f"Falha ao instalar dependências com {PACKAGE_MANAGER}")
        
        # Se pnpm falhou, tentar npm como fallback
        if PACKAGE_MANAGER == "pnpm":
            print_warning("Tentando com npm como alternativa...")
            PACKAGE_MANAGER = "npm"
            fallback_cmd = f'"{NPM_PATH}" install' if NPM_PATH and NPM_PATH != "npm" else "npm install"
            if not run_command(
                fallback_cmd,
                "Instalando dependências do dashboard com npm",
                cwd=str(dashboard_dir),
                shell=True,
                check=False
            ):
                print_error("Falha ao instalar dependências do dashboard")
                return False

    print_success("Dependências do dashboard instaladas")
    return True


def generate_data():
    """Gera dados sintéticos"""
    print_header("GERANDO DADOS SINTÉTICOS")

    # Verificar se dados já existem
    data_path = Path("data") / "processed" / "dataset_realista_1m.parquet"
    if data_path.exists():
        print_warning("Dataset já existe, pulando geração")
        return True

    # Gerar dados
    script_path = Path("scripts") / "gerar_dados_REALISTICOS.py"
    if not run_command(
        [sys.executable, str(script_path)], 
        "Gerando dataset de 1M de registros",
        check=False
    ):
        print_error("Falha ao gerar dados")
        return False

    print_success("Dados gerados com sucesso")
    return True


def train_model():
    """Treina modelo de ML"""
    print_header("TREINANDO MODELO DE MACHINE LEARNING")

    # Verificar se modelo já existe
    model_path = Path("api") / "modelo_lgbm.pkl"
    if model_path.exists():
        print_warning("Modelo já existe, pulando treinamento")
        return True

    # Treinar modelo
    script_path = Path("scripts") / "treinar_modelo_PREMIUM.py"
    if not run_command(
        [sys.executable, str(script_path)], 
        "Treinando modelo LightGBM",
        check=False
    ):
        print_error("Falha ao treinar modelo")
        return False

    print_success("Modelo treinado com sucesso")
    return True


def run_integration_tests():
    """Executa testes de integração"""
    print_header("EXECUTANDO TESTES DE INTEGRAÇÃO")

    test_script = Path("test_integration.py")
    if not test_script.exists():
        print_warning("Script de testes não encontrado, pulando")
        return True

    if not run_command(
        [sys.executable, str(test_script)], 
        "Executando testes de integração",
        check=False
    ):
        print_warning("Alguns testes falharam (verifique se a API está rodando)")
        return False

    print_success("Todos os testes passaram")
    return True


def start_api():
    """Inicia API FastAPI"""
    print_header("INICIANDO API")

    api_dir = Path("api")

    print_info("API será iniciada em http://localhost:8000")
    print_info("Documentação disponível em http://localhost:8000/docs")
    print_info("Pressione Ctrl+C para parar")
    print()

    try:
        subprocess.run(
            [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"],
            cwd=str(api_dir),
        )
    except KeyboardInterrupt:
        print_info("\nAPI encerrada")


def start_dashboard():
    """Inicia Dashboard Premium React"""
    global PACKAGE_MANAGER, NPM_PATH
    
    print_header("INICIANDO DASHBOARD PREMIUM")

    dashboard_dir = Path("dashboard_premium")
    
    # Verificar e instalar dependências se necessário
    if not (dashboard_dir / "node_modules").exists():
        print_warning("Dependências do dashboard não encontradas. Instalando...")
        if not install_dashboard_dependencies():
            print_error("Falha ao instalar dependências do dashboard")
            return

    print_info("Dashboard será iniciado em http://localhost:3000")
    print_info("Pressione Ctrl+C para parar")
    print()

    # Comando baseado no gerenciador de pacotes
    if PACKAGE_MANAGER == "pnpm":
        command = "pnpm dev"
    else:
        if NPM_PATH and NPM_PATH != "npm":
            command = f'"{NPM_PATH}" run dev'
        else:
            command = "npm run dev"

    try:
        subprocess.run(
            command,
            cwd=str(dashboard_dir),
            shell=True
        )
    except KeyboardInterrupt:
        print_info("\nDashboard encerrado")


def start_both():
    """Inicia API e Dashboard em paralelo"""
    global PACKAGE_MANAGER, NPM_PATH
    
    print_header("INICIANDO API + DASHBOARD")
    
    # Verificar e instalar dependências do dashboard se necessário
    dashboard_dir = Path("dashboard_premium")
    if not (dashboard_dir / "node_modules").exists():
        print_warning("Dependências do dashboard não encontradas. Instalando...")
        if not install_dashboard_dependencies():
            print_error("Falha ao instalar dependências do dashboard")
            return
    
    print_info("API: http://localhost:8000")
    print_info("Dashboard: http://localhost:3000")
    print_info("Pressione Ctrl+C para parar ambos")
    print()
    
    import threading
    
    api_process = None
    dashboard_process = None
    
    def start_api_thread():
        nonlocal api_process
        api_process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"],
            cwd=str(Path("api"))
        )
        api_process.wait()
    
    def start_dashboard_thread():
        nonlocal dashboard_process
        if PACKAGE_MANAGER == "pnpm":
            command = "pnpm dev"
        else:
            if NPM_PATH and NPM_PATH != "npm":
                command = f'"{NPM_PATH}" run dev'
            else:
                command = "npm run dev"
        
        dashboard_process = subprocess.Popen(
            command,
            cwd=str(Path("dashboard_premium")),
            shell=True
        )
        dashboard_process.wait()
    
    api_thread = threading.Thread(target=start_api_thread, daemon=True)
    dashboard_thread = threading.Thread(target=start_dashboard_thread, daemon=True)
    
    api_thread.start()
    time.sleep(3)  # Aguardar API iniciar
    dashboard_thread.start()
    
    # Aguardar API e Dashboard iniciarem completamente
    time.sleep(5)
    
    # Abrir múltiplas abas
    print_info("Abrindo navegador com múltiplas abas...")
    print()
    
    urls = [
        ("http://localhost:3000", "Dashboard Principal"),
        ("http://localhost:8000/docs", "API Documentation (Swagger)"),
        ("http://localhost:8000/health", "Health Check")
    ]
    
    abas_abertas = 0
    for url, descricao in urls:
        try:
            webbrowser.open_new_tab(url)
            print_success(f"{descricao}: {url}")
            abas_abertas += 1
            time.sleep(0.5)  # Delay entre abas para não sobrecarregar
        except Exception as e:
            print_warning(f"Não foi possível abrir {descricao}: {e}")
    
    print()
    if abas_abertas > 0:
        print_success(f"{abas_abertas} abas abertas com sucesso!")
        print_info("Sistema pronto")
    else:
        print_warning("Não foi possível abrir o navegador automaticamente")
        print_info("Abra manualmente as seguintes URLs:")
        for url, descricao in urls:
            print(f"  - {descricao}: {url}")
    
    try:
        # Manter o processo principal rodando
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print_info("\nEncerrando API e Dashboard...")
        if api_process:
            api_process.terminate()
        if dashboard_process:
            dashboard_process.terminate()


def show_menu():
    """Exibe menu de opções e valida entrada"""
    print_header("SANTANDER CREDIT RISK PLATFORM - MENU PRINCIPAL")

    print("Escolha uma opção:\n")
    print("  1. Setup Completo (recomendado para primeira execução)")
    print("  2. Gerar Dados Sintéticos")
    print("  3. Treinar Modelo")
    print("  4. Executar Testes de Integração")
    print("  5. Iniciar API")
    print("  6. Iniciar Dashboard Premium")
    print("  7. Iniciar API + Dashboard (ambos)")
    print("  8. Executar Tudo (setup + dados + modelo + API + Dashboard)")
    print("  0. Sair\n")

    while True:
        choice = input("Digite o número da opção: ").strip()
        if choice in ["0", "1", "2", "3", "4", "5", "6", "7", "8"]:
            return choice
        else:
            print_error("Opção inválida! Digite um número de 0 a 8.")
            print()


def main():
    """Função principal"""
    # Verificar Python
    if not check_python_version():
        print_error("\nPré-requisitos não atendidos!")
        print_info("\nVerifique:")
        print_info("1. Node.js está instalado? Execute: node --version")
        print_info("2. npm está no PATH? Execute: npm --version")
        print_info("\nSe npm não funcionar:")
        print_info("- Reinstale Node.js de: https://nodejs.org/")
        print_info("- Durante instalação, marque 'Add to PATH'")
        print_info("- Reinicie o terminal após instalação")
        input("\nPressione Enter para sair...")
        sys.exit(1)

    # Menu interativo
    while True:
        choice = show_menu()

        if choice == "0":
            print_info("Encerrando...")
            break

        elif choice == "1":
            # Setup completo
            generate_env_file()
            generate_api_env()
            generate_dashboard_env()
            install_python_dependencies()
            install_dashboard_dependencies()
            print_success("\n Setup completo!")

        elif choice == "2":
            # Gerar dados
            generate_data()

        elif choice == "3":
            # Treinar modelo
            train_model()

        elif choice == "4":
            # Executar testes
            run_integration_tests()

        elif choice == "5":
            # Iniciar API
            start_api()

        elif choice == "6":
            # Iniciar dashboard
            start_dashboard()

        elif choice == "7":
            # Iniciar ambos
            start_both()

        elif choice == "8":
            # Executar tudo
            generate_env_file()
            generate_api_env()
            generate_dashboard_env()
            install_python_dependencies()
            install_dashboard_dependencies()
            generate_data()
            train_model()
            print_success("\n Tudo pronto! Escolha opção 7 para iniciar API + Dashboard.")

        else:
            print_error("Opção inválida")

        input("\nPressione Enter para continuar...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_info("\n\nOperação cancelada pelo usuário")
        sys.exit(0)
    except Exception as e:
        print_error(f"\nErro inesperado: {e}")
        import traceback
        traceback.print_exc()
        input("\nPressione Enter para sair...")
        sys.exit(1)
