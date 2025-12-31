from fastapi import FastAPI, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import engine, Base, get_db
import models
from routers import users, videos
import schemas  

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[int, list[WebSocket]] = {}

    async def connect(self, user_id: int, websocket: WebSocket):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        print(f"User {user_id} connected via WebSocket")

    def disconnect(self, user_id: int, websocket: WebSocket):
        if user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
            print(f"User {user_id} disconnected")

    async def send_personal_message(self, message: dict, user_id: int):
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                await connection.send_json(message)

manager = ConnectionManager()

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

@app.post("/internal/notify")
async def notify_user(notification: schemas.NotifySchema):
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
    db = SessionLocal()

    users_to_seed = [
        {
            "email": "barbar6132@gmail.com",
            "password": "barbar6132",
            "is_admin": True,
            "label": "ADMIN"
        },
        {
            "email": "bar6132@gmail.com",
            "password": "bar6132",
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