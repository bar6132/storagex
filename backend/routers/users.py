from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
from jose import JWTError, jwt
from datetime import datetime, timedelta
import hashlib
import models, database, main_utils, schemas, cache
from main_utils import get_password_hash, verify_password
import os

router = APIRouter(prefix="/users", tags=["Authentication"])

# Read from env so this is True in production (HTTPS) and False in dev (HTTP)
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"

def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()

@router.post("/register")
def register(user_data: schemas.UserCreate, db: Session = Depends(database.get_db)):
    db_user = db.query(models.User).filter(models.User.email == user_data.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_pwd = get_password_hash(user_data.password)
    new_user = models.User(email=user_data.email, hashed_password=hashed_pwd, is_admin=False)
    db.add(new_user)
    db.commit()
    return {"message": "User created successfully"}

@router.post("/token")
async def login(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(database.get_db)
):
    client_ip = request.client.host if request.client else "unknown"
    if not cache.check_rate_limit(f"login:{client_ip}", limit=10, window_seconds=60):
        raise HTTPException(
            status_code=429,
            detail="Too many login attempts. Please wait a minute and try again."
        )

    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    access_token = main_utils.create_access_token(data={"sub": user.email, "id": user.id})
    refresh_token = main_utils.create_refresh_token(data={"sub": user.email, "id": user.id})

    # Store hashed refresh token in DB for revocation support
    expires_at = datetime.utcnow() + timedelta(days=main_utils.REFRESH_TOKEN_EXPIRE_DAYS)
    db_token = models.RefreshToken(
        token_hash=_hash_token(refresh_token),
        user_id=user.id,
        expires_at=expires_at
    )
    db.add(db_token)
    db.commit()

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        samesite="lax",
        max_age=15 * 60,
        secure=COOKIE_SECURE,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        samesite="lax",
        max_age=7 * 24 * 60 * 60,
        secure=COOKIE_SECURE,
        path="/users",   # sent to all /users/... endpoints (refresh + logout)
    )

    main_utils.log_admin_action("LOGIN", user.id, user.email, "auth", {"ip": client_ip})
    return {"access_token": access_token, "token_type": "bearer", "user_id": user.id}

@router.get("/me", response_model=schemas.UserOut)
async def get_me(current_user: models.User = Depends(main_utils.get_current_user)):
    return current_user

@router.post("/refresh")
async def refresh_token(
    request: Request,
    response: Response,
    db: Session = Depends(database.get_db)
):
    refresh_token_cookie = request.cookies.get("refresh_token")
    if not refresh_token_cookie:
        raise HTTPException(status_code=401, detail="No refresh token provided")

    try:
        payload = jwt.decode(
            refresh_token_cookie,
            main_utils.SECRET_KEY,
            algorithms=[main_utils.ALGORITHM]
        )
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        email: str = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid refresh token payload")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    # Verify the token exists in DB (revocation check)
    token_hash = _hash_token(refresh_token_cookie)
    stored = db.query(models.RefreshToken).filter(
        models.RefreshToken.token_hash == token_hash,
        models.RefreshToken.user_id == user.id
    ).first()
    if not stored:
        raise HTTPException(status_code=401, detail="Refresh token has been revoked")

    # Rotate: delete old token, issue new one
    db.delete(stored)
    new_access_token = main_utils.create_access_token(data={"sub": user.email, "id": user.id})
    new_refresh_token = main_utils.create_refresh_token(data={"sub": user.email, "id": user.id})
    new_expires_at = datetime.utcnow() + timedelta(days=main_utils.REFRESH_TOKEN_EXPIRE_DAYS)
    db.add(models.RefreshToken(
        token_hash=_hash_token(new_refresh_token),
        user_id=user.id,
        expires_at=new_expires_at
    ))
    db.commit()

    response.set_cookie(
        key="access_token",
        value=new_access_token,
        httponly=True,
        samesite="lax",
        max_age=15 * 60,
        secure=COOKIE_SECURE,
    )
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        samesite="lax",
        max_age=7 * 24 * 60 * 60,
        secure=COOKIE_SECURE,
        path="/users",
    )
    return {"message": "Token refreshed successfully"}

@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    db: Session = Depends(database.get_db)
):
    # Revoke refresh token from DB if present
    refresh_token_cookie = request.cookies.get("refresh_token")
    if refresh_token_cookie:
        token_hash = _hash_token(refresh_token_cookie)
        stored = db.query(models.RefreshToken).filter_by(token_hash=token_hash).first()
        if stored:
            db.delete(stored)
            db.commit()

    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token", path="/users")
    return {"message": "Logged out successfully"}

@router.get("/admin/users", response_model=List[schemas.UserOut])
async def list_users_admin(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(main_utils.get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin only")

    limit = min(limit, 200)
    main_utils.log_admin_action(
        "LIST_USERS", current_user.id, current_user.email, "all_users"
    )
    return db.query(models.User).offset(skip).limit(limit).all()

@router.delete("/admin/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(main_utils.get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin privileges required")

    user_to_delete = db.query(models.User).filter(models.User.id == user_id).first()
    if not user_to_delete:
        raise HTTPException(status_code=404, detail="User not found")

    main_utils.log_admin_action(
        "DELETE_USER", current_user.id, current_user.email,
        f"user:{user_id}", {"deleted_email": user_to_delete.email}
    )
    db.delete(user_to_delete)
    db.commit()
    return {"message": "User deleted"}

@router.patch("/admin/users/{user_id}/make-admin")
def promote_user(
    user_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(main_utils.get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin privileges required")

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_admin = True
    db.commit()

    main_utils.log_admin_action(
        "PROMOTE_TO_ADMIN", current_user.id, current_user.email,
        f"user:{user_id}", {"promoted_email": user.email}
    )
    return {"message": "User promoted to Admin"}
