from datetime import datetime, timedelta, timezone
import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings
from app.core.database import get_db
from app.core.limiter import limiter
from app.core.security import create_access_token, verify_password
from app.models.user import User

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

logger = logging.getLogger(__name__)


def mask_email(email: str) -> str:
    """Mask email address for logging purposes."""
    if not email or "@" not in email:
        return "********"
    user, domain = email.split("@", 1)
    if len(user) <= 2:
        return f"{user[:1]}***@{domain}"
    return f"{user[:2]}***@{domain}"


def get_client_ip(request: Request) -> str:
    """Safely get client IP address."""
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


class Token(BaseModel):
    access_token: str
    token_type: str


@router.post("/login", response_model=Token)
@limiter.limit("5/minute")  # Max 5 attempts per minute
def login(
    request: Request,  # Required for rate limiting
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == form_data.username).first()
    
    # Authenticate first to prevent account enumeration
    if not user or not verify_password(form_data.password, user.hashed_password):
        # Log without revealing specific user details for security
        logger.warning(f"Failed login attempt from IP: {get_client_ip(request)}")
        
        if user:
            user.increment_failed_attempts(db)
            
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    # Check account status after successful authentication
    if user.is_locked():
        logger.warning(
            f"Login attempt on locked account: {mask_email(form_data.username)} "
            f"from IP: {get_client_ip(request)}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account locked due to too many failed attempts. Try again after {user.locked_until.strftime('%H:%M')}",
        )

    if not user.is_active:
        logger.warning(
            f"Login attempt on inactive account: {mask_email(form_data.username)} "
            f"from IP: {get_client_ip(request)}"
        )
        raise HTTPException(status_code=400, detail="Inactive user")

    # Successful login - reset failed attempts
    user.reset_failed_attempts()
    user.last_login = datetime.now(timezone.utc)
    db.commit()
    
    logger.info(
        f"Successful login: {mask_email(user.email)} (ID: {user.id}, Role: {user.role.value}) "
        f"from IP: {get_client_ip(request)}"
    )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id, "role": user.role.value},
        expires_delta=access_token_expires,
    )
    return {"access_token": access_token, "token_type": "bearer"}


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    from app.core.security import verify_token

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = verify_token(token)
    if payload is None:
        raise credentials_exception

    email = payload.get("sub")
    if not email:
        raise credentials_exception

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise credentials_exception

    return user
