"""
Módulo de Autenticação JWT/OAuth2
Implementação enterprise-grade para ambiente bancário
"""

from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, Field
import structlog
from app.utils.config import settings

logger = structlog.get_logger()

# Configurações de segurança (importadas do .env via settings)
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__max_rounds=12)

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


# ============================================================================
# Modelos de Dados
# ============================================================================


class Token(BaseModel):
    """Token de acesso"""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    """Dados extraídos do token"""

    username: Optional[str] = None
    user_id: Optional[str] = None
    scopes: List[str] = []
    exp: Optional[datetime] = None


class User(BaseModel):
    """Modelo de usuário"""

    user_id: str
    username: str
    email: EmailStr
    full_name: str
    disabled: bool = False
    roles: List[str] = []
    permissions: List[str] = []


class UserInDB(User):
    """Usuário com senha hasheada"""

    hashed_password: str


class LoginRequest(BaseModel):
    """Request de login"""

    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=100)


class RefreshTokenRequest(BaseModel):
    """Request de refresh token"""

    refresh_token: str


# ============================================================================
# Funções de Autenticação
# ============================================================================


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica se a senha corresponde ao hash
    Trunca senhas longas para evitar erro do bcrypt (max 72 bytes)
    """
    # Bcrypt tem limite de 72 bytes
    if len(plain_password) > 72:
        plain_password = plain_password[:72]
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Gera hash bcrypt da senha
    Trunca senhas longas para evitar erro do bcrypt (max 72 bytes)
    """
    # Bcrypt tem limite de 72 bytes
    if len(password) > 72:
        password = password[:72]
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Cria token JWT de acesso

    Args:
        data: Dados a serem codificados no token
        expires_delta: Tempo de expiração customizado

    Returns:
        Token JWT assinado
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "iat": datetime.utcnow(), "type": "access"})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    logger.info("Access token created", username=data.get("sub"), expires_at=expire.isoformat())

    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """
    Cria token JWT de refresh (longa duração)

    Args:
        data: Dados a serem codificados no token

    Returns:
        Refresh token JWT assinado
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode.update({"exp": expire, "iat": datetime.utcnow(), "type": "refresh"})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    logger.info("Refresh token created", username=data.get("sub"), expires_at=expire.isoformat())

    return encoded_jwt


def decode_token(token: str) -> TokenData:
    """
    Decodifica e valida token JWT

    Args:
        token: Token JWT a ser decodificado

    Returns:
        Dados extraídos do token

    Raises:
        HTTPException: Se token for inválido ou expirado
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        username: str = payload.get("sub")
        user_id: str = payload.get("user_id")
        scopes: List[str] = payload.get("scopes", [])
        exp: int = payload.get("exp")

        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido: username não encontrado",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token_data = TokenData(
            username=username, user_id=user_id, scopes=scopes, exp=datetime.fromtimestamp(exp) if exp else None
        )

        return token_data

    except JWTError as e:
        logger.error(f"Token decode error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ============================================================================
# Database de Usuários (Mock - Substituir por DB real)
# ============================================================================

# TODO: Substituir por consulta ao banco de dados real
# Database de usuários (inicialização lazy para evitar erro bcrypt)
FAKE_USERS_DB = {}


def init_users_db():
    """Inicializa o banco de usuários fake"""
    import os

    global FAKE_USERS_DB
    if not FAKE_USERS_DB:
        # Usuários padrão
        FAKE_USERS_DB = {
            "admin": UserInDB(
                user_id="USR001",
                username="admin",
                email="admin@santander.com.br",
                full_name="Administrador do Sistema",
                hashed_password="$2b$12$placeholder",  # Será gerado no primeiro uso
                disabled=False,
                roles=["admin", "analyst"],
                permissions=["predict", "batch_predict", "view_metrics", "manage_users"],
            ),
            "analyst": UserInDB(
                user_id="USR002",
                username="analyst",
                email="analyst@santander.com.br",
                full_name="Analista de Crédito",
                hashed_password="$2b$12$placeholder",
                disabled=False,
                roles=["analyst"],
                permissions=["predict", "batch_predict", "view_metrics"],
            ),
        }
        # Gerar hashes reais
        FAKE_USERS_DB["admin"].hashed_password = get_password_hash("Santander@2025")
        FAKE_USERS_DB["analyst"].hashed_password = get_password_hash("Analyst@2025")

        # Adicionar usuários de teste em modo DEBUG
        if os.getenv("DEBUG", "false").lower() == "true":
            FAKE_USERS_DB["admin@santander.com"] = UserInDB(
                user_id="USR_TEST_001",
                username="admin@santander.com",
                email="admin@santander.com",
                full_name="Admin Santander (Teste)",
                hashed_password=get_password_hash("Santander@2025"),
                disabled=False,
                roles=["admin", "analyst"],
                permissions=["predict", "batch_predict", "view_metrics", "manage_users"],
            )
            FAKE_USERS_DB["teste@santander.com"] = UserInDB(
                user_id="USR_TEST_002",
                username="teste@santander.com",
                email="teste@santander.com",
                full_name="Usuário Teste",
                hashed_password=get_password_hash("Teste@123"),
                disabled=False,
                roles=["user"],
                permissions=["predict", "view_metrics"],
            )
            logger.info("Usuários de teste adicionados (DEBUG mode)")
    return FAKE_USERS_DB


def get_user(username: str) -> Optional[UserInDB]:
    """
    Busca usuário no banco de dados

    TODO: Substituir por consulta real ao PostgreSQL
    """
    users_db = init_users_db()
    if username in users_db:
        return users_db[username]
    return None


def authenticate_user(username: str, password: str) -> Optional[UserInDB]:
    """
    Autentica usuário verificando credenciais

    Args:
        username: Nome de usuário
        password: Senha em texto plano

    Returns:
        Usuário autenticado ou None se credenciais inválidas
    """
    user = get_user(username)

    if not user:
        logger.warning(f"Login attempt with non-existent user: {username}")
        return None

    if not verify_password(password, user.hashed_password):
        logger.warning(f"Failed login attempt for user: {username}")
        return None

    if user.disabled:
        logger.warning(f"Login attempt with disabled user: {username}")
        return None

    logger.info(f"User authenticated successfully: {username}")
    return user


# ============================================================================
# Dependências de Autenticação
# ============================================================================


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """
    Obtém usuário atual a partir do token JWT

    Dependency para proteger endpoints

    Usage:
        @router.get("/protected")
        async def protected_route(current_user: User = Depends(get_current_user)):
            return {"user": current_user.username}
    """
    token_data = decode_token(token)

    user = get_user(username=token_data.username)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.disabled:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuário desabilitado")

    return User(**user.model_dump())


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Verifica se usuário está ativo
    """
    if current_user.disabled:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuário inativo")
    return current_user


def require_permission(permission: str):
    """
    Decorator para exigir permissão específica

    Usage:
        @router.post("/predict")
        async def predict(
            request: PredictRequest,
            current_user: User = Depends(require_permission("predict"))
        ):
            ...
    """

    async def permission_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if permission not in current_user.permissions:
            logger.warning(
                f"Permission denied: {permission}", user=current_user.username, required_permission=permission
            )
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Permissão necessária: {permission}")
        return current_user

    return permission_checker


def require_role(role: str):
    """
    Decorator para exigir role específica

    Usage:
        @router.get("/admin/users")
        async def list_users(
            current_user: User = Depends(require_role("admin"))
        ):
            ...
    """

    async def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if role not in current_user.roles:
            logger.warning(f"Role denied: {role}", user=current_user.username, required_role=role)
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Role necessária: {role}")
        return current_user

    return role_checker


# ============================================================================
# Funções de Validação de Senha
# ============================================================================


def validate_password_strength(password: str) -> bool:
    """
    Valida força da senha (requisitos bancários)

    Requisitos:
    - Mínimo 8 caracteres
    - Pelo menos 1 letra maiúscula
    - Pelo menos 1 letra minúscula
    - Pelo menos 1 número
    - Pelo menos 1 caractere especial
    """
    if len(password) < 8:
        return False

    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)

    return has_upper and has_lower and has_digit and has_special


def check_password_common(password: str) -> bool:
    """
    Verifica se senha está na lista de senhas comuns
    """
    common_passwords = [
        "password",
        "123456",
        "12345678",
        "qwerty",
        "abc123",
        "password123",
        "admin",
        "letmein",
        "welcome",
        "monkey",
    ]
    return password.lower() in common_passwords
