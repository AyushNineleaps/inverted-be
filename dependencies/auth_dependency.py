from fastapi import Cookie, HTTPException, status

from services.auth_service import jwt_verify


def get_current_user(access_token: str|None= Cookie(None)):
    if not access_token:
        raise HTTPException(status_code= status.HTTP_401_UNAUTHORIZED,detail='Not authenticated')
    payload = jwt_verify(access_token)
    if (not payload) or( not payload.is_active):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail='Invalid Token')
    return payload

