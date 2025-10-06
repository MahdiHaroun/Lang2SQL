from jose import jwt, JWTError
from datetime import datetime, timedelta
import schemas, database, models
from config import settings
from fastapi import Depends, HTTPException, status 
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='login')#The tokenUrl='login' means the frontend will get tokens by calling your /login endpoint (that’s where users log in).


def create_access_token(data: dict):
    to_encode = data.copy()
    # Set the expiration time for the token
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_access_token(token: str, credentials_exception):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        id: str = payload.get("user_id")

        if id is None:
            raise credentials_exception 
        
        token_data = schemas.TokenData(id=str(id))
    except JWTError:
        raise credentials_exception
    
    return token_data


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token_data = verify_access_token(token, credentials_exception)
    user = db.query(models.User).filter(models.User.id == token_data.id).first()
    
    return user


def get_current_session(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
    """Get or create a session for the current user. Session ID is a UUID that serves as both session and thread ID"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate session",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # First get the user from token
    token_data = verify_access_token(token, credentials_exception)
    user = db.query(models.User).filter(models.User.id == token_data.id).first()
    
    if user is None:
        raise credentials_exception
    
    # Look for existing session or create new one
    session = db.query(models.Session).filter(models.Session.user_id == user.id).first()
    
    if session is None:
        # Create new session with UUID token (this UUID serves as both session_id and thread_id)
        import uuid
        session_token = str(uuid.uuid4())  # This UUID is both session_id and thread_id
        session = models.Session(
            session_token=session_token,
            user_id=user.id
        )
        db.add(session)
        db.commit()
        db.refresh(session)
    
    return session.session_token


def get_current_user_and_session(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
    """Get both current user and session in one call. Returns user and session_id (UUID) which serves as thread_id"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token_data = verify_access_token(token, credentials_exception)
    user = db.query(models.User).filter(models.User.id == token_data.id).first()
    
    if user is None:
        raise credentials_exception
    
    # Get or create session
    session = db.query(models.Session).filter(models.Session.user_id == user.id).first()
    
    if session is None:
        import uuid
        session_token = str(uuid.uuid4())  # This UUID is both session_id and thread_id
        session = models.Session(
            session_token=session_token,
            user_id=user.id
        )
        db.add(session)
        db.commit()
        db.refresh(session)
    
    return user, session.session_token