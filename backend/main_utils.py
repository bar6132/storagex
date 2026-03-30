from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import database, models
from passlib.context import CryptContext
from typing import Optional
import logging
import json
import os

SECRET_KEY = os.getenv("SECRET_KEY", "dev_secret_key_change_in_production_please")
ALGORITHM = "HS256"

# [FIX: SEC-001] Access token lifetime reduced from 24h to 15 minutes.
# Short-lived tokens limit the damage window if a token is ever stolen.
# Refresh tokens (see below) handle keeping the user logged in long-term.
# OLD: ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24
ACCESS_TOKEN_EXPIRE_MINUTES = 15

# [FIX: SEC-003] Refresh token lifetime — 7 days.
# Stored as a separate httpOnly cookie, only sent to /users/refresh.
REFRESH_TOKEN_EXPIRE_DAYS = 7

# [FIX: SEC-004] Dedicated audit logger — all admin actions are recorded here.
# Logs appear in stdout which Docker / any log aggregator captures.
audit_logger = logging.getLogger("storagex.audit")
logging.basicConfig(level=logging.INFO)

# Kept for OpenAPI /docs "Authorize" button compatibility.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# [FIX: SEC-003] New — creates a long-lived refresh token.
# Distinguished from access tokens by the "type": "refresh" claim so the
# /users/refresh endpoint can reject an access token passed as a refresh token.
def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# [FIX: SEC-004] Structured JSON audit log for every admin action.
# Written to stdout so Docker / log shippers capture it automatically.
def log_admin_action(action: str, admin_id: int, admin_email: str, target: str, details: dict = None):
    log_entry = {
        "event": "ADMIN_ACTION",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "action": action,
        "admin_id": admin_id,
        "admin_email": admin_email,
        "target": target,
        "details": details or {}
    }
    audit_logger.warning(json.dumps(log_entry))
    print(f"[AUDIT] {json.dumps(log_entry)}", flush=True)

# [FIX: SEC-001] Updated to read token from httpOnly cookie first, then Authorization header.
# This supports both cookie-based auth (browser clients) and Bearer header (API clients / docs).
# OLD:
# async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
#     credentials_exception = HTTPException(
#         status_code=status.HTTP_401_UNAUTHORIZED,
#         detail="Could not validate credentials",
#         headers={"WWW-Authenticate": "Bearer"},
#     )
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         email: str = payload.get("sub")
#         if email is None: raise credentials_exception
#     except JWTError:
#         raise credentials_exception
#     user = db.query(models.User).filter(models.User.email == email).first()
#     if user is None: raise credentials_exception
#     return user
async def get_current_user(
    request: Request,
    token: Optional[str] = Depends(OAuth2PasswordBearer(tokenUrl="token", auto_error=False)),
    db: Session = Depends(database.get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    # Cookie takes priority (XSS-safe); Authorization header is the fallback for API/docs usage.
    resolved_token = request.cookies.get("access_token") or token
    if not resolved_token:
        raise credentials_exception

    try:
        payload = jwt.decode(resolved_token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        raise credentials_exception
    return user

# [FIX: SEC-001] Same cookie-first approach as get_current_user, but returns None instead of 401.
# Used by endpoints that allow both authenticated and anonymous access.
# OLD:
# async def get_current_user_optional(
#     token: Optional[str] = Depends(OAuth2PasswordBearer(tokenUrl="token", auto_error=False)),
#     db: Session = Depends(database.get_db)
# ):
#     if not token:
#         return None
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         email: str = payload.get("sub")
#         if email is None: return None
#     except JWTError:
#         return None
#     return db.query(models.User).filter(models.User.email == email).first()
async def get_current_user_optional(
    request: Request,
    token: Optional[str] = Depends(OAuth2PasswordBearer(tokenUrl="token", auto_error=False)),
    db: Session = Depends(database.get_db)
):
    resolved_token = request.cookies.get("access_token") or token
    if not resolved_token:
        return None

    try:
        payload = jwt.decode(resolved_token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
    except JWTError:
        return None

    return db.query(models.User).filter(models.User.email == email).first()
