from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
import models, database, main_utils, schemas 
from main_utils import get_password_hash, verify_password 

router = APIRouter(prefix="/users", tags=["Authentication"])

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
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    access_token = main_utils.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/admin/users", response_model=List[schemas.UserOut])
async def list_users_admin(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(main_utils.get_current_user)
):
    if not current_user.is_admin: 
        raise HTTPException(status_code=403, detail="Admin only")
    return db.query(models.User).all()