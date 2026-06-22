from fastapi import Depends, HTTPException,status

from dependencies.auth_dependency import get_current_user
from schemas.user import CurrentUser


def role_required(*allowed_roles):
    def role_checker(current_user: CurrentUser= Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Not Allowed.')
        
        return current_user
    return role_checker
    