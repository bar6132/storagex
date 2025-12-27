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
async def seed_database():
    from database import SessionLocal
    from models import User
    from main_utils import get_password_hash 
    db = SessionLocal()

    users_to_seed = [
        {
            "email": "",
            "password": "",
            "is_admin": True,
            "label": "ADMIN"
        },
        {
            "email": "",
            "password": "",
            "is_admin": False, 
            "label": "REGULAR USER"
        }
    ]

    try:
        for user_data in users_to_seed:
            user = db.query(User).filter(User.email == user_data["email"]).first()
            
            if not user:
                print(f"[*] {user_data['label']} not found. Creating {user_data['email']}...")
                hashed_pwd = get_password_hash(user_data["password"])
                
                new_user = User(
                    email=user_data["email"],
                    hashed_password=hashed_pwd,
                    is_admin=user_data["is_admin"]
                )
                db.add(new_user)
                db.commit()
                print(f"[+] SUCCESS: {user_data['label']} created.")
                
            else:
                if user.is_admin != user_data["is_admin"]:
                    user.is_admin = user_data["is_admin"]
                    db.commit()
                    print(f"[+] UPDATED: {user_data['email']} role changed to {user_data['label']}.")
                else:
                    print(f"[=] User {user_data['email']} already exists as {user_data['label']}.")

    except Exception as e:
        print(f"[!] Error during database seeding: {e}")
    finally:
        db.close()