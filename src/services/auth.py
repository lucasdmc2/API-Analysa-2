"""
Authentication and authorization service
"""

from typing import Optional, List
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import uuid

from src.core.exceptions import (
    TokenMissingError, TokenInvalidError, TokenExpiredError,
    InsufficientScopeError, TenantAccessDeniedError
)
from src.core.config import settings

# OAuth2 security scheme
security = HTTPBearer(auto_error=False)


class User(BaseModel):
    """Current user model"""
    user_id: str
    tenant_id: uuid.UUID
    scopes: List[str]
    email: Optional[str] = None
    name: Optional[str] = None


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> User:
    """
    Get current authenticated user from JWT token.
    In production, this would validate against OAuth2/OIDC provider.
    """
    
    if not credentials:
        raise TokenMissingError()
    
    token = credentials.credentials
    
    # TODO: In production, validate JWT token against OIDC provider
    # For development/testing, use mock validation
    if settings.ENVIRONMENT == "development":
        return _mock_user_validation(token)
    
    # Production JWT validation would go here
    # jwt_payload = validate_jwt_token(token)
    # return User.from_jwt_payload(jwt_payload)
    
    raise TokenInvalidError("Token validation not implemented for production")


def _mock_user_validation(token: str) -> User:
    """Mock user validation for development"""
    
    # Simple mock tokens for development
    mock_users = {
        "dev-admin": User(
            user_id="admin-001",
            tenant_id=uuid.UUID("00000000-0000-0000-0000-000000000000"),
            scopes=["read", "write", "admin"],
            email="admin@clinical-extraction.com",
            name="Admin User"
        ),
        "dev-user": User(
            user_id="user-001", 
            tenant_id=uuid.UUID("00000000-0000-0000-0000-000000000000"),
            scopes=["read", "write"],
            email="user@clinical-extraction.com",
            name="Regular User"
        ),
        "dev-read": User(
            user_id="read-001",
            tenant_id=uuid.UUID("00000000-0000-0000-0000-000000000000"),
            scopes=["read"],
            email="read@clinical-extraction.com",
            name="Read Only User"
        ),
    }
    
    if token in mock_users:
        return mock_users[token]
    
    raise TokenInvalidError(f"Invalid development token: {token}")


def require_scope(required_scope: str):
    """Dependency to require specific OAuth2 scope"""
    
    async def _require_scope(current_user: User = Depends(get_current_user)):
        if required_scope not in current_user.scopes:
            raise InsufficientScopeError(required_scope)
        return None
    
    return _require_scope


def require_tenant_access(tenant_id: uuid.UUID):
    """Dependency to require access to specific tenant"""
    
    async def _require_tenant_access(current_user: User = Depends(get_current_user)):
        if current_user.tenant_id != tenant_id:
            raise TenantAccessDeniedError()
        return None
    
    return _require_tenant_access