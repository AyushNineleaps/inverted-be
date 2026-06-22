from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from dependencies.auth_dependency import get_current_user
from dependencies.role_dependency import role_required
from models.user import User
from database import get_db
from google_oauth import oauth
from schemas.user import CurrentUser, LoginRequest, RegisterRequest

from services.auth_service import hash_password, jwt_creation, verify_password
from config import ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM, SECRET_KEY

router = APIRouter()

@router.post('/new-user',status_code=status.HTTP_201_CREATED)
def add_new_user(newUser: RegisterRequest, db: Session= Depends(get_db)):
    # return {"message": newUser}
    user_found = db.query(User).filter(User.email==newUser.email.lower()).first()
    if user_found:
        raise HTTPException(
            status_code= status.HTTP_409_CONFLICT,
            detail= "Email already present"  
            
        )
    if len(newUser.password)<6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail= 'Password too short, minimum 6 characters'
        )
    
    user = User(
        name = newUser.name,
        email = newUser.email,
        password_hash = hash_password(newUser.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return ({
        'message':"User created Successfully",
        'user':{
            'id':user.id,
            'name':user.name,
            'email':user.email,
        }
    })
@router.post('/login',status_code= status.HTTP_200_OK)
def login_user(loginPayload:LoginRequest, response: Response, db: Session= Depends(get_db)):
    user: User = db.query(User).filter(User.email == loginPayload.email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail= 'Invalid Credentials')
    if user:
        valid_pass:bool= verify_password(loginPayload.password, user.password_hash)
        if not valid_pass:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail= 'email or password is incorrect')
    access_token= jwt_creation({
        "sub":str(user.id),
        "email": user.email,
        "role": user.role,
        "name": user.name,
        'is_active': user.is_active
    })
    response.set_cookie(
        key= "access_token",
        value= access_token,
        httponly= True,
        secure= False, # True for production
        samesite='lax',
        max_age = ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    return {
        'message':'login Successful',
        'user':{
            'email':user.email,
            'name':user.name,
        }
    }

@router.post('/logout')
def logout_user(response : Response):
    response.delete_cookie(
        key='access_token',
        path='/'
    )
    return {
        'message': "logged out successfully."
    }



@router.get('/profile')
def user_detail(response: Response, current_user: CurrentUser= Depends(role_required('admin','visitor')),db: Session= Depends(get_db)):
    user: User= db.query(User).filter(User.email == current_user.email).first()
    
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

@router.get('/google/callback')
async def google_callback(request: Request,response: Response,db:Session= Depends(get_db)):
    token = await oauth.google.authorize_access_token(request)
    user_info= token['userinfo']
    user:User = db.query(User).filter(User.email==user_info['email']).first()        
    if not user:
        user = User(name=user_info['name'],email=user_info['email'],password_hash=None,google_sub=user_info['sub'])
        db.add(user)
        db.commit()
        db.refresh(user)
        
    access_token= jwt_creation({
        "sub":str(user.id),
        "email": user.email,
        "role": user.role,
        "name": user.name,
        'is_active': user.is_active
    })
    redirect_response = RedirectResponse(
        url="http://localhost:3000/landing",
        status_code=302
    )
    redirect_response.set_cookie(
        key= "access_token",
        value= access_token,
        httponly= True,
        secure= False, # True for production
        samesite='lax',
        max_age = ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    return redirect_response
                                        

@router.get("/google/login")
async def google_login(request: Request):
    redirect_uri = request.url_for("google_callback")
    return await oauth.google.authorize_redirect(
        request,
        redirect_uri
    )
