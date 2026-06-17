from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from models.user import Base
from database import engine
from sqlalchemy.orm import Session
from services.auth_service import hash_password,verify_password
from routers.auth import router as auth_router
from routers.user import router as user_router

from routers.resume import router as resume_router

from starlette.middleware.sessions import SessionMiddleware


app = FastAPI()

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(resume_router)


app.add_middleware(
    SessionMiddleware,
    secret_key="my-google-oauth-secret"
)
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    # allow_origins=['http://localhost:3000'],
    allow_methods=['*']
    
)

Base.metadata.create_all(bind = engine)
