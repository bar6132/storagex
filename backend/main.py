from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import models, database
from routers import videos, users 

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="StorageX API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router)
app.include_router(videos.router)

@app.get("/")
def root():
    return {"message": "Welcome to StorageX API"}

@app.on_event("startup")
async def create_super_admin():
    from database import SessionLocal
    from models import User
    from main_utils import get_password_hash 
    db = SessionLocal()
    target_email = "<email>"
    target_password = "<password>"

    try:
        user = db.query(User).filter(User.email == target_email).first()
        
        if not user:
            print(f"[*] Admin user not found. Creating {target_email}...")
            hashed_pwd = get_password_hash(target_password)
            
            new_admin = User(
                email=target_email,
                hashed_password=hashed_pwd,
                is_admin=True 
            )
            db.add(new_admin)
            db.commit()
            print(f"[+] SUCCESS: Admin created. Login with {target_email} / {target_password}")
            
        else:
            if not user.is_admin:
                user.is_admin = True
                db.commit()
                print(f"[+] UPDATED: Existing user {target_email} is now an Admin.")
            else:
                print(f"[=] Admin {target_email} already exists and is configured correctly.")

    except Exception as e:
        print(f"[!] Error creating admin user: {e}")
    finally:
        db.close()