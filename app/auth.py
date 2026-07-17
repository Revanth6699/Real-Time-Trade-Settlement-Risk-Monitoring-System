
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta

from fastapi import (
    Depends,
    HTTPException,
    status
)

from fastapi.security import (
    OAuth2PasswordBearer
)

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.user import User
import os

import re


# =========================================================
# PASSWORD HASHING
# =========================================================

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

# =========================================================
# JWT CONFIG
# =========================================================

SECRET_KEY = os.getenv("SECRET_KEY")

ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = 60

# =========================================================
# OAUTH2
# =========================================================

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="login"
)

# =========================================================
# DATABASE SESSION
# =========================================================

def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()

# =========================================================
# HASH PASSWORD
# =========================================================

def hash_password(password: str):

    return pwd_context.hash(password)

# =========================================================
# VERIFY PASSWORD
# =========================================================

def verify_password(
    plain_password: str,
    hashed_password: str
):

    return pwd_context.verify(
        plain_password,
        hashed_password
    )

# =========================================================
# VALIDATE PASSWORD
# =========================================================

def validate_password(password: str):

    if len(password) < 8:

        raise HTTPException(
            status_code=400,
            detail="Password must be at least 8 characters"
        )

    if not re.search(r"[A-Z]", password):

        raise HTTPException(
            status_code=400,
            detail="Password must contain uppercase letter"
        )

    if not re.search(r"[a-z]", password):

        raise HTTPException(
            status_code=400,
            detail="Password must contain lowercase letter"
        )

    if not re.search(r"\d", password):

        raise HTTPException(
            status_code=400,
            detail="Password must contain number"
        )

    if not re.search(r"[!@#$%^&*()_+=\-{}[\]:;<>,.?/]", password):

        raise HTTPException(
            status_code=400,
            detail="Password must contain special character"
        )

    return True

# =========================================================
# AUTHENTICATE USER
# =========================================================

def authenticate_user(
    db: Session,
    username: str,
    password: str
):

    user = db.query(User).filter(
        User.username == username
    ).first()

    if not user:

        return None

    valid_password = verify_password(
        password,
        user.hashed_password
    )

    if not valid_password:

        return None

    return user

# =========================================================
# CREATE ACCESS TOKEN
# =========================================================

def create_access_token(data: dict):

    to_encode = data.copy()

    expire = datetime.utcnow() + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    to_encode.update({
        "exp": expire
    })

    encoded_jwt = jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return encoded_jwt

# =========================================================
# VERIFY TOKEN
# =========================================================

def verify_token(token: str):

    try:

        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        username = payload.get("sub")
        role = payload.get("role")

        if username is None:

            raise HTTPException(
                status_code=401,
                detail="Invalid token"
            )

        return {
            "username": username,
            "role": role
        }

    except JWTError:

        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )

# =====================================================
# DECODE ACCESS TOKEN
# =====================================================

def decode_access_token(token: str):
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        username = payload.get("sub")
        role = payload.get("role")

        if username is None:
            return None

        return {
            "username": username,
            "role": role
        }

    except JWTError as e:
        print("JWT Decode Error:", e)
        return None


# =====================================================
# GET CURRENT USER
# =====================================================

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)


    if payload is None:
        raise credentials_exception

    username = payload.get("username")
    role = payload.get("role")

    user = (
        db.query(User)
        .filter(User.username == username)
        .first()
    )

    if user is None:
        raise credentials_exception

    return user

# =========================================================
# ROLE BASED ACCESS CONTROL (RBAC)
# =========================================================

def require_roles(*allowed_roles):
    """
    Generic RBAC dependency.
    Example:
        Depends(require_roles("admin"))
        Depends(require_roles("admin", "trader"))
    """

    def role_checker(current_user: User = Depends(get_current_user)):

        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this resource."
            )

        return current_user

    return role_checker


# =========================================================
# ADMIN
# =========================================================

def admin_required(current_user: User = Depends(get_current_user)):

    if current_user.role != "admin":

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required."
        )

    return current_user


# =========================================================
# TRADER
# =========================================================

def trader_required(current_user: User = Depends(get_current_user)):

    if current_user.role not in ["admin", "trader"]:

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Trader privileges required."
        )

    return current_user


# =========================================================
# AUDITOR
# =========================================================

def auditor_required(current_user: User = Depends(get_current_user)):

    if current_user.role not in ["admin", "auditor"]:

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Auditor privileges required."
        )

    return current_user


# =========================================================
# ADMIN OR TRADER
# =========================================================

def admin_or_trader(current_user: User = Depends(get_current_user)):

    if current_user.role not in ["admin", "trader"]:

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied."
        )

    return current_user


# =========================================================
# ADMIN OR AUDITOR
# =========================================================

def admin_or_auditor(current_user: User = Depends(get_current_user)):

    if current_user.role not in ["admin", "auditor"]:

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied."
        )

    return current_user


# =========================================================
# ANY AUTHENTICATED USER
# =========================================================

def authenticated_user(current_user: User = Depends(get_current_user)):
    return current_user