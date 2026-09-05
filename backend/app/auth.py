
import os
import re
import bcrypt
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from .database import get_db
from .models import User


SECRET_KEY = os.getenv("AUTH_SECRET_KEY", "dev-secret-key-please-change-in-production-64chars!")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 7


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None or not user.is_active:
        raise credentials_exception
    return user



def _has_sequential_chars(password: str, length: int = 6) -> bool:
    for i in range(len(password) - length + 1):
        window = password[i:i + length]
        diffs = [ord(window[j + 1]) - ord(window[j]) for j in range(len(window) - 1)]
        if all(d == 1 for d in diffs) or all(d == -1 for d in diffs):
            return True
    return False


def validate_password_strength(password: str) -> Optional[str]:
    
    if not (8 <= len(password) <= 20):
        return "密码长度须在 8-20 位之间"
    if not re.search(r"[a-zA-Z]", password):
        return "密码须包含字母"
    if not re.search(r"[0-9]", password):
        return "密码须包含数字"
    if not re.search(r"""[!@#$%^&*()\-_=+\[\]{};:'",.<>/?\\|`~]""", password):
        return "密码须包含特殊符号（如 !@#$%）"
    if re.search(r"(.)\1{3,}", password):
        return "密码不能包含 4 个及以上连续相同字符（如 aaaa）"
    if _has_sequential_chars(password, 6):
        return "密码不能包含 6 个及以上连续顺序字符（如 123456）"
    return None
