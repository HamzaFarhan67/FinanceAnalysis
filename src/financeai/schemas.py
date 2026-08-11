from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID
import os
import jwt
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr
from pwdlib import PasswordHash
from sqlalchemy.orm import Session
from .database import get_db, User

SECRET_KEY = os.getenv("JWT_SECRET", "super-secret-jwt-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/token")
password_hash_context = PasswordHash.recommended()


API_KEY_NAME = "X-API-Key"
VALID_API_KEY = os.getenv("INGESTION_API_KEY", "my-super-secret-ingestion-key-123")
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != VALID_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API Key in X-API-Key header",
        )
    return api_key


password_hash_context = PasswordHash.recommended()

def hash_password(password: str) -> str:
    return password_hash_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials or token expired",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Decode JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        user_id = int(user_id_str)
    except jwt.PyJWTError:
        raise credentials_exception

    # Query DB for authenticated user
    user = db.get(User, user_id)
    if user is None:
        raise credentials_exception
    return user

# --- Pydantic API Schemas ---
class ChatRequest(BaseModel):
    user_message: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    username: str

class ChatResponse(BaseModel):
    reply: str


class ConversationResponse(BaseModel):
    id: UUID
    title: str

class MessageOut(BaseModel):
    role: str
    content: str

class CreateChatRequest(BaseModel):
    user_id: Optional[str] = None
    title: Optional[str] = "New Chat"

class SummaryResponse(BaseModel):
    conversation_id: UUID
    summary: str
    open_questions: list[str] = []
    recommended_next_actions: list[str] = []
    recent_messages: list[MessageOut] = []

class UserSignUp(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserSignIn(BaseModel):
    username: str
    password: str

class AuthResponse(BaseModel):
    status: str
    message: str
    user_id: int
    username: str
    access_token: Optional[str] = None


class ConversationUpdate(BaseModel):
    title: str