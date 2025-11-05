"""
Rotas de Autenticação JWT
"""

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
import structlog
from jose import jwt

from app.security.auth import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_active_user,
    Token,
    User,
    LoginRequest,
    RefreshTokenRequest,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    SECRET_KEY,
    ALGORITHM,
)

router = APIRouter()
logger = structlog.get_logger()


@router.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Endpoint de login OAuth2 (compatível com Swagger UI)

    Retorna access token e refresh token

    Credenciais de teste:
    - admin / Santander@2025
    - analyst / Analyst@2025
    - operator / Operator@2025
    """
    user = authenticate_user(form_data.username, form_data.password)

    if not user:
        logger.warning(
            "Failed login attempt", username=form_data.username, ip="<request.client.host>"  # TODO: Capturar IP real
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Criar tokens
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.user_id, "scopes": user.permissions},
        expires_delta=access_token_expires,
    )

    refresh_token = create_refresh_token(data={"sub": user.username, "user_id": user.user_id})

    logger.info("User logged in successfully", username=user.username, user_id=user.user_id, roles=user.roles)

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/login", response_model=Token)
async def login_json(login_request: LoginRequest):
    """
    Endpoint de login alternativo (JSON body)

    Aceita username e password no corpo da requisição
    """
    user = authenticate_user(login_request.username, login_request.password)

    if not user:
        logger.warning("Failed login attempt (JSON)", username=login_request.username)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário ou senha incorretos")

    # Criar tokens
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.user_id, "scopes": user.permissions},
        expires_delta=access_token_expires,
    )

    refresh_token = create_refresh_token(data={"sub": user.username, "user_id": user.user_id})

    logger.info("User logged in successfully (JSON)", username=user.username, user_id=user.user_id)

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_request: RefreshTokenRequest):
    """
    Renova access token usando refresh token

    Permite manter usuário logado sem pedir senha novamente
    """
    try:
        token_data = decode_token(refresh_request.refresh_token)

        # Verificar se é refresh token
        payload = jwt.decode(refresh_request.refresh_token, SECRET_KEY, algorithms=[ALGORITHM])

        if payload.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido: não é refresh token")

        # Criar novo access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": token_data.username, "user_id": token_data.user_id, "scopes": token_data.scopes},
            expires_delta=access_token_expires,
        )

        logger.info("Access token refreshed", username=token_data.username)

        return Token(
            access_token=access_token,
            refresh_token=refresh_request.refresh_token,  # Mantém o mesmo refresh token
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token inválido ou expirado")


@router.get("/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """
    Retorna informações do usuário autenticado

    Requer token JWT válido
    """
    logger.info("User info requested", username=current_user.username)

    return current_user


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_active_user)):
    """
    Logout do usuário

    TODO: Implementar blacklist de tokens para invalidação imediata
    Por enquanto, apenas registra o logout (token expira naturalmente)
    """
    logger.info("User logged out", username=current_user.username, user_id=current_user.user_id)

    return {"message": "Logout realizado com sucesso", "username": current_user.username}


@router.get("/validate")
async def validate_token(current_user: User = Depends(get_current_active_user)):
    """
    Valida se token ainda é válido

    Útil para frontend verificar se precisa renovar token
    """
    return {
        "valid": True,
        "username": current_user.username,
        "user_id": current_user.user_id,
        "roles": current_user.roles,
        "permissions": current_user.permissions,
    }


# Imports movidos para o topo do arquivo
