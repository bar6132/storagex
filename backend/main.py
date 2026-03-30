from fastapi import FastAPI, Depends, WebSocket, WebSocketDisconnect, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import engine, Base, get_db
import models
from routers import users, videos
import schemas
import time
from sqlalchemy.exc import OperationalError
from sqlalchemy import text
import search
import os
from ws_manager import manager

# NOTE: Base.metadata.create_all is intentionally NOT called here at module
# import time.  Calling it here means a DB-not-ready error crashes the whole
# uvicorn subprocess, which triggers an infinite --reload loop.
# It is called inside the startup event below, where retry logic already lives.

app = FastAPI()

CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router)
app.include_router(videos.router)

@app.get("/")
def root():
    return {"message": "Welcome to StorageX API"}

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await manager.connect(user_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(user_id, websocket)

# Internal endpoint — only the worker service should call this.
# Protected by a shared secret sent in the X-Internal-Token header.
INTERNAL_NOTIFY_SECRET = os.getenv("INTERNAL_NOTIFY_SECRET", "")

@app.post("/internal/notify")
async def notify_user(
    notification: schemas.NotifySchema,
    x_internal_token: str = Header(default=""),
):
    if INTERNAL_NOTIFY_SECRET and x_internal_token != INTERNAL_NOTIFY_SECRET:
        raise HTTPException(status_code=403, detail="Forbidden")

    print(f"Sending notification to User {notification.user_id}: {notification.status}")
    await manager.send_personal_message(
        {
            "type": "video_update",
            "video_id": notification.video_id,
            "status": notification.status,
            "msg": notification.message
        },
        notification.user_id
    )
    return {"status": "sent"}

@app.on_event("startup")
async def seed_database():
    from database import SessionLocal
    from models import User
    from main_utils import get_password_hash

    db = None
    retries = 10
    while retries > 0:
        try:
            db = SessionLocal()
            db.execute(text("SELECT 1"))
            print("Database is ready!")
            break
        except Exception as e:
            retries -= 1
            print(f"Database not ready yet... waiting 2 seconds ({retries} retries left)")
            db = None
            time.sleep(2)
            if retries == 0:
                print("Could not connect to DB after multiple tries.")
                raise e

    # Create / update tables now that the DB is confirmed reachable.
    # Doing this here (not at import time) prevents uvicorn --reload from
    # crashing the subprocess when the DB is briefly unavailable on startup.
    try:
        Base.metadata.create_all(bind=engine)
        print("Tables created / verified.")
    except Exception as e:
        print(f"create_all failed: {e}")
        raise e

    users_to_seed = [
        {
            "email": os.getenv("SEED_ADMIN_EMAIL", "admin@storagex.local"),
            "password": os.getenv("SEED_ADMIN_PASSWORD", "admin123"),
            "is_admin": True,
            "label": "ADMIN"
        },
        {
            "email": os.getenv("SEED_USER_EMAIL", "user@storagex.local"),
            "password": os.getenv("SEED_USER_PASSWORD", "user123"),
            "is_admin": False,
            "label": "REGULAR USER"
        },
        {
            "email": os.getenv("SEED_PERSONAL_ADMIN_EMAIL", "barbar6132@gmail.com"),
            "password": os.getenv("SEED_PERSONAL_ADMIN_PASSWORD", "admin123"),
            "is_admin": True,
            "label": "PERSONAL ADMIN"
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
                    print(f"[+] UPDATED: {user_data['email']} role changed.")
                else:
                    print(f"[=] User {user_data['email']} already exists.")

    except Exception as e:
        print(f"[!] Error during database seeding: {e}")

    try:
        search.create_index()
    except Exception as e:
        print(f"Elasticsearch not ready: {e}")
    finally:
        if db:
            db.close()
