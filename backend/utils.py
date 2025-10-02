from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash(password:str):
    return pwd_context.hash(password)  # Hash the password using bcrypt


def verify(plain_password , hashed_password):
    return pwd_context.verify(plain_password, hashed_password)  # Verify the password against the hashed password