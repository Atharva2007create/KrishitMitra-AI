from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import get_settings
from app.db.connection import get_db
from app.models.entities import User
from app.models.enums import UserRole
from app.security.cognito import AuthenticationError, CognitoJWTVerifier

bearer = HTTPBearer(auto_error=False)


def get_jwt_verifier() -> CognitoJWTVerifier:
    return CognitoJWTVerifier(get_settings())


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    session: Annotated[AsyncSession, Depends(get_db)],
    verifier: Annotated[CognitoJWTVerifier, Depends(get_jwt_verifier)],
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required"
        )
    try:
        claims = await verifier.verify(credentials.credentials)
    except AuthenticationError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    user = await session.scalar(select(User).where(User.cognito_sub == claims.subject))
    if user is None:
        role = (
            UserRole.ADMIN
            if get_settings().aws_cognito_admin_group in claims.groups
            else UserRole.FARMER
        )
        user = User(
            cognito_sub=claims.subject,
            role=role,
            phone_number=claims.phone_number,
            email=claims.email,
            last_login_at=datetime.now(UTC),
        )
        session.add(user)
    else:
        user.last_login_at = datetime.now(UTC)
        user.phone_number = user.phone_number or claims.phone_number
        user.email = user.email or claims.email
    await session.commit()
    await session.refresh(user)
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive")
    return user


async def require_farmer(user: Annotated[User, Depends(get_current_user)]) -> User:
    if user.role != UserRole.FARMER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Farmer role required")
    return user


async def require_admin(user: Annotated[User, Depends(get_current_user)]) -> User:
    if user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Administrator role required"
        )
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
FarmerUser = Annotated[User, Depends(require_farmer)]
AdminUser = Annotated[User, Depends(require_admin)]
