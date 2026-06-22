from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from sqlalchemy.orm import Session

from database import get_db
from dependencies.auth_dependency import get_current_user
from dependencies.role_dependency import role_required
from models.user import User
from schemas.user import ActivationPayload, CurrentUser, ThemePayload, UserListResponse


router= APIRouter()

@router.put('/theme-update/{id}')
def update_theme(id:str,themePayload:ThemePayload, db:Session= Depends(get_db),current_user: CurrentUser= Depends(get_current_user)):
    if current_user.role == 'admin' or current_user.sub == id:
        user: User = db.query(User).filter(User.id == id, User.is_active== True).first()
        if not user:
            raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, detail="user does not exist")
        user.theme = themePayload.theme
        db.commit()
        db.refresh(user)
        return {
            'message':'theme Updated Successfully.',
            'user': {
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'role': user.role,
                'theme': user.theme,
                'is_active': user.is_active
            }
        }
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail='not allowed.')
        
@router.put('/activation-status/{id}')
def user_activation_controller(id:str,activation_payload: ActivationPayload,response: Response, current_user: CurrentUser = Depends(get_current_user), db:Session = Depends(get_db)):
    user:User = db.query(User).filter(User.id== id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User does not exist."
        )
    if(current_user.role=='visitor'):
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail= 'Action not allowed.')
        else:
            if not current_user.id == id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail= 'Action not allowed.')
            else:
                if(activation_payload.activation_status == True):
                    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail= 'Action not allowed.')
                else:
                    user.is_active = activation_payload.activation_status
                    db.commit()
                    db.refresh(user)
                    response.delete_cookie(key='access_token',path='/')
                    return {
                        'message':"updated status",
                        'user': {
                            'id': user.id,
                            'name': user.name,
                            'email': user.email,
                            'role': user.role,
                            'theme': user.theme,
                            'is_active': user.is_active
                        }
                    }
    elif current_user.role == 'admin':
        if not current_user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail= 'Action not allowed.')
        else:
           user.is_active = activation_payload.activation_status
           db.commit()
           db.refresh(user)
           if current_user.sub == id:
               response.delete_cookie(key='access_token',path='/')
           return {
                'message':"updated status",
                'user': {
                    'id': user.id,
                    'name': user.name,
                    'email': user.email,
                    'role': user.role,
                    'theme': user.theme,
                    'is_active': user.is_active
                }
            }
      
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Action not allowed.")
        
@router.get('/all-users',response_model=UserListResponse)
def get_all_users(current_user: CurrentUser= Depends(role_required('admin')), db: Session = Depends(get_db)):
    users: list[User]= db.query(User).order_by(User.name.asc()).all()
    return {
        "users":users
    }
    
    
@router.get('/user-detail/{id}')
def user_detail(id:str, current_user: CurrentUser= Depends(role_required('admin')),db: Session= Depends(get_db)):
    user: User= db.query(User).filter(User.id == id).first()
    
    return {
        "user":{
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'role': user.role,
            'theme': user.theme,
            'is_active': user.is_active
            
        }
    }
