from datetime import datetime, timedelta

from passlib.context import CryptContext

from jose import JWTError, jwt

from config import ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM, SECRET_KEY
from schemas.user import CurrentUser

pwd_context= CryptContext(schemes=['bcrypt'],deprecated= 'auto')

def hash_password(password:str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_pass: str, hashed_pass: str)-> bool:
    return pwd_context.verify(plain_pass,hashed_pass)
    
def jwt_creation(data: dict):
    shallow_cp = data.copy()
    
    expire= datetime.now() + timedelta(minutes = ACCESS_TOKEN_EXPIRE_MINUTES)
    shallow_cp.update({
        'exp': expire
    })
    new_jwt = jwt.encode(shallow_cp,SECRET_KEY, algorithm=ALGORITHM)
    
    return new_jwt

def jwt_verify(token: str):
    try:
        payload = jwt.decode(token,SECRET_KEY,algorithms = [ALGORITHM])
        print(payload)
        return CurrentUser(**payload)
    except JWTError:
        return None