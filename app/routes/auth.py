from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.utils.auth import hash_password, verify_password, create_access_token

router = APIRouter()

# Temporary in-memory user DB (replace with SQLite/Postgres for production)
fake_users_db = {}

@router.post("/register")
async def register(username: str, password: str):
    if username in fake_users_db:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    user_id = f"user_{len(fake_users_db) + 1}"
    fake_users_db[username] = {
        "username": username,
        "user_id": user_id,
        "password_hash": hash_password(password)
    }
    return {"message": "User registered successfully", "user_id": user_id}

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = fake_users_db.get(form_data.username)
    if not user or not verify_password(form_data.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    access_token = create_access_token(data={"sub": user["username"], "user_id": user["user_id"]})
    return {"access_token": access_token, "token_type": "bearer"}